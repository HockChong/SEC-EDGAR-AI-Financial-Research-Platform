"""Adversarial extraction, form semantics and deterministic provenance invariants."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from sec_research.contracts.parsing import ParsedDocument
from sec_research.processing import blocks, dom
from sec_research.processing.dom import ParseError, load_dom, resolve
from sec_research.processing.html import parse_html
from tests.parsing_helpers import input_html


@pytest.mark.parametrize("fixture", ["annual.htm", "quarter.htm", "malformed.htm"])
def test_wp31_fixture_replay_and_source_graph(fixture: str) -> None:
    fetch, body = input_html(fixture=fixture)
    first = parse_html(fetch, body)
    assert first == parse_html(fetch, body)
    assert first.logical_bytes() == parse_html(fetch, body).logical_bytes()
    assert ParsedDocument.model_validate_json(first.model_dump_json()) == first
    assert first.document.source.sha256 == fetch.sha256
    assert first.document.source.source.filing == fetch.source.filing
    root = load_dom(body).root
    normalized = "\n".join(b.text for b in first.blocks)
    for block in first.blocks:
        assert resolve(root, block.locator.path) is not None
        assert normalized[block.locator.start : block.locator.end] == block.text
        assert block.locator.text_sha256 == first.document.text_sha256
    for section in first.sections:
        assert section.locator == first.blocks[section.first_block_ordinal].locator


def test_nested_mixed_content_has_no_duplicate_text() -> None:
    parsed = parse_html(
        *input_html(
            "<div>Before<span> inline <b>bold</b></span><p>Child <i>text</i></p>After"
            "<ul><li>Outer<ul><li>Inner</li></ul>tail</li><li>Next</li></ul>End</div>"
        )
    )
    assert [b.text for b in parsed.blocks] == [
        "Before inline bold",
        "Child text",
        "After",
        "Outer",
        "Inner",
        "tail",
        "Next",
        "End",
    ]
    assert [b.kind for b in parsed.blocks[3:7]] == ["list"] * 4


def test_inline_xbrl_visible_values_and_hidden_resources() -> None:
    parsed = parse_html(
        *input_html(
            "<ix:header><ix:hidden><ix:nonnumeric>SECRET</ix:nonnumeric></ix:hidden></ix:header>"
            '<p>Revenue <ix:nonfraction name="us-gaap:Revenue">123</ix:nonfraction> million.</p>'
            "<ix:resources><xbrli:context>HIDDEN</xbrli:context></ix:resources>"
            '<p style="display: none">INVISIBLE</p><div hidden>HIDDEN</div>'
            '<script>fetch("file:///secret")</script><style>CSS</style>'
        )
    )
    assert [b.text for b in parsed.blocks] == ["Revenue 123 million."]


def test_financial_and_nested_tables_are_opaque() -> None:
    parsed = parse_html(
        *input_html(
            "<h1>Item 8. Financial Statements</h1><p>Before</p><table><tr><th>Revenue</th>"
            "<td>123<table><tr><td>456</td></tr></table></td></tr></table><p>After</p>"
        )
    )
    assert [b.text for b in parsed.blocks] == [
        "Item 8. Financial Statements",
        "Before",
        "[TABLE]",
        "After",
    ]
    assert sum(b.kind == "table" for b in parsed.blocks) == 1
    assert "123" not in " ".join(b.text for b in parsed.blocks)


def test_layout_heading_table_is_not_a_financial_table() -> None:
    parsed = parse_html(
        *input_html(
            "<table><tr><td></td><td></td><td></td><td></td><td></td></tr>"
            "<tr><td>Item 1.</td><td>Business</td></tr></table><p>Our business.</p>"
            "<table><tr><td>Item 8. Financial Statements</td><td>123</td></tr></table>"
        )
    )
    assert parsed.blocks[0].kind == "heading"
    assert parsed.sections[0].item == "1"
    assert parsed.blocks[-1].kind == "table"


@pytest.mark.parametrize(
    "body,encoding,warning",
    [
        (b'<meta charset="windows-1252"><p>It\x92s text</p>', "cp1252", False),
        (b"<p>It\x92s text</p>", "cp1252", True),
        (b'<meta charset="invented"><p>text</p>', "cp1252", True),
        ("<p>Unicode \u2019</p>".encode("utf-16"), "utf-16", False),
        (b"\xef\xbb\xbf<p>text</p>", "utf-8-sig", False),
        (b'<meta charset="base64"><p>text</p>', "cp1252", True),
    ],
)
def test_encoding_policy(body: bytes, encoding: str, warning: bool) -> None:
    result = parse_html(*input_html(body))
    assert result.encoding == encoding
    assert ("encoding_fallback" in [e.reason_code for e in result.quality_events]) == warning


@pytest.mark.parametrize(
    "body",
    [
        "<nav><a href='#b'>Item 1. Business</a><a href='#r'>Item 1A. Risk Factors</a></nav>",
        "<table><tr><td><a href='#b'>Item 1. Business</a></td></tr>"
        "<tr><td><a href='#r'>Item 1A. Risk Factors</a></td></tr></table>",
    ],
)
def test_toc_does_not_own_body_section(body: str) -> None:
    result = parse_html(
        *input_html(
            body + "<h1>Item 1. Business</h1><p>Business body</p>"
            "<h1>Item 1A. Risk Factors</h1><p>Risk body</p>"
        )
    )
    assert [(s.item, s.classification) for s in result.sections if s.item] == [
        ("1", "classified"),
        ("1A", "classified"),
    ]
    assert result.sections[0].classification == "unclassified"
    assert result.sections[1].first_block_ordinal > 0


def test_quarter_part_i_and_part_ii_are_distinct() -> None:
    result = parse_html(*input_html(fixture="quarter.htm"))
    assert [(s.part, s.item) for s in result.sections if s.item] == [
        ("I", "1"),
        ("I", "2"),
        ("II", "1"),
        ("II", "1A"),
    ]


@pytest.mark.parametrize(
    "html,reason",
    [
        ("<h1>Item 1. Financial Statements</h1><p>Body</p>", "missing_part"),
        ("<h1>Part I</h1><h2>Item 1A. Risk Factors</h2><p>Body</p>", "invalid_form_item"),
        (
            "<h1>Part I</h1><h2>Item 3. Market risk</h2><h2>Item 2. Discussion</h2>",
            "item_order_conflict",
        ),
    ],
)
def test_uncertain_quarter_sections_preserved(html: str, reason: str) -> None:
    result = parse_html(*input_html(html, fixture="quarter.htm"))
    assert reason in [e.reason_code for e in result.quality_events]
    assert any(s.classification == "ambiguous" for s in result.sections)


def test_missing_headings_preserves_every_block() -> None:
    result = parse_html(*input_html("<div>Unlabeled<p>Meaningful</p></div>"))
    assert len(result.sections) == 1
    assert result.sections[0].classification == "unclassified"
    assert [b.text for b in result.blocks] == ["Unlabeled", "Meaningful"]


def test_running_headers_and_prose_references_do_not_split_sections() -> None:
    result = parse_html(
        *input_html(
            "<h1>Item 1. Business</h1><p>Body</p><p>Item 1</p>"
            "<p>Item 7 discusses results elsewhere.</p><p>More</p>"
            "<h1>Item 1A. Risk Factors</h1><p>Risk</p>"
        )
    )
    assert [s.item for s in result.sections] == ["1", "1A"]


def test_fetch_occurrences_do_not_change_logical_content() -> None:
    fetch, body = input_html()
    first = parse_html(fetch, body)
    second = parse_html(fetch.model_copy(update={"id": UUID(int=100)}), body)
    assert first.logical_bytes() == second.logical_bytes()
    assert first.provenance.id != second.provenance.id


@pytest.mark.parametrize(
    "update", [{"sha256": "0" * 64}, {"byte_count": 1}, {"processing_status": "quarantined"}]
)
def test_source_integrity_failure(update: dict[str, object]) -> None:
    fetch, body = input_html()
    with pytest.raises(ParseError, match="source_integrity"):
        parse_html(fetch.model_copy(update=update), body)


@pytest.mark.parametrize(
    "html,code",
    [(b"", "source_size_limit"), (b"<script>only script</script>", "no_visible_content")],
)
def test_empty_or_invisible_input_fails(html: bytes, code: str) -> None:
    with pytest.raises(ParseError, match=code):
        parse_html(*input_html(html))


@pytest.mark.parametrize(
    "limit,value,body,code",
    [
        ("MAX_BYTES", 1, "<p>body</p>", "source_size_limit"),
        ("MAX_NODES", 2, "<p>body</p>", "dom_resource_limit"),
        ("MAX_DEPTH", 2, "<div><div><p>body</p></div></div>", "dom_resource_limit"),
    ],
)
def test_dom_budgets(
    monkeypatch: pytest.MonkeyPatch, limit: str, value: int, body: str, code: str
) -> None:
    monkeypatch.setattr(dom, limit, value)
    with pytest.raises(ParseError, match=code):
        parse_html(*input_html(body))


def test_block_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(blocks, "MAX_BLOCKS", 1)
    with pytest.raises(ParseError, match="block_resource_limit"):
        parse_html(*input_html("<p>One</p><p>Two</p>"))


@pytest.mark.parametrize("field", ["document_id", "section_id", "ordinal", "text_sha256"])
def test_contract_rejects_corrupt_block_graph(field: str) -> None:
    result = parse_html(*input_html())
    data = result.model_dump(mode="json")
    data["blocks"][0].pop("id")
    replacements: dict[str, object] = {
        "ordinal": 99,
        "document_id": "document:" + "0" * 64,
        "section_id": "section:" + "0" * 64,
        "text_sha256": "0" * 64,
    }
    data["blocks"][0][field] = replacements[field]
    with pytest.raises(ValidationError):
        ParsedDocument.model_validate(data)


def test_external_entity_is_never_loaded(tmp_path: object) -> None:
    result = parse_html(
        *input_html(
            '<!DOCTYPE html [<!ENTITY xxe SYSTEM "file:///secret.txt">]><html><body><p>&xxe;</p></body></html>'
        )
    )
    assert "&xxe;" in " ".join(b.text for b in result.blocks)


def test_unlinked_dense_toc_duplicates_are_retained_but_not_classified() -> None:
    labels = ["Item 1. Business", "Item 1A. Risk Factors", "Item 7. Management's Discussion"]
    toc = "".join(f"<p>{text}</p>" for text in labels)
    body = "".join(f"<h1>{text}</h1><p>Actual body content.</p>" for text in labels)
    result = parse_html(*input_html(toc + body))
    assert result.sections[0].classification == "unclassified"
    assert [s.first_block_ordinal for s in result.sections if s.item] == [3, 5, 7]
    assert "toc_content_retained" in [e.reason_code for e in result.quality_events]


def test_ambiguous_annual_heading_retains_warning() -> None:
    result = parse_html(
        *input_html(
            "<h1>Item 7. Management's Discussion</h1><p>Body</p>"
            "<h2>Item 7? uncertain heading</h2><p>Retained</p>"
        )
    )
    assert result.sections[-1].classification == "ambiguous"
    assert "uncertain_heading" in [e.reason_code for e in result.quality_events]


@pytest.mark.parametrize("kind", ["gap", "overlap", "source", "provenance", "quality"])
def test_envelope_rejects_broken_cross_record_invariants(kind: str) -> None:
    result = parse_html(*input_html())
    data = result.model_dump(mode="json")
    if kind in {"gap", "overlap"}:
        section = data["sections"][1]
        section["id"] = None
        section["first_block_ordinal"] += 1 if kind == "gap" else -1
    elif kind == "source":
        data["filing"]["id"] = None
        data["filing"]["source"]["sha256"] = "0" * 64
    elif kind == "provenance":
        data["provenance"]["id"] = None
        data["provenance"]["entity_id"] = "document:" + "0" * 64
    else:
        data["quality_events"][0]["id"] = None
        data["quality_events"][0]["entity_id"] = "document:" + "0" * 64
    with pytest.raises(ValidationError):
        ParsedDocument.model_validate(data)


def test_parser_version_changes_all_document_and_block_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sec_research.processing import html

    before = parse_html(*input_html())
    monkeypatch.setattr(html, "PARSER_VERSION", "test-new-version")
    after = parse_html(*input_html())
    assert before.document.id != after.document.id
    assert {b.id for b in before.blocks}.isdisjoint(b.id for b in after.blocks)


def test_bronze_metadata_sources_are_not_html_documents() -> None:
    fetch, body = input_html(fixture="company_facts.json")
    with pytest.raises(ParseError, match="not_a_filing"):
        parse_html(fetch, body)


def test_recovery_and_encoding_loss_are_recorded() -> None:
    result = parse_html(*input_html(b"<p>A\x81B</p></not-valid>"))
    reasons = {e.reason_code for e in result.quality_events}
    assert {"encoding_fallback", "encoding_replacement", "html_recovered"} <= reasons


def test_excessive_source_depth_is_not_silently_truncated() -> None:
    with pytest.raises(ParseError, match="dom_resource_limit"):
        parse_html(*input_html("<div>" * 300 + "Body" + "</div>" * 300))
