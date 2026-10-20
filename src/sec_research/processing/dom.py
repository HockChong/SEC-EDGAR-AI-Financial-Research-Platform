"""Nonexecuting HTML recovery, byte decoding and stable positional DOM locators."""

import codecs
import re
from dataclasses import dataclass

from lxml import etree

PARSER_VERSION = (
    "sec-html-1/lxml-" + etree.LXML_VERSION.__str__() + "/libxml-" + etree.LIBXML_VERSION.__str__()
)
PIPELINE_VERSION = "html-1"
MAX_BYTES = 32 * 1024 * 1024
MAX_NODES = 750_000
MAX_DEPTH = 240


class ParseError(Exception):
    """Safe recoverable error; never includes document text or arbitrary exception data."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class DOM:
    root: etree._Element
    encoding: str
    warnings: tuple[str, ...]


class _DenyResources(etree.Resolver):
    # lxml-stubs 0.5.1 omits the runtime resolver context argument.
    def resolve(self, system_url: str, public_id: str, context: object = None) -> object:
        raise ParseError("external_resource_forbidden")


def decode(body: bytes) -> tuple[str, str, tuple[str, ...]]:
    """BOM, explicit HTML/XML charset, strict UTF-8, then Windows-1252 with warning."""
    if body.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    elif body.startswith(codecs.BOM_UTF8):
        encoding = "utf-8-sig"
    else:
        match = re.search(
            rb"(?:charset\s*=\s*[\"']?\s*|encoding\s*=\s*[\"'])([a-zA-Z0-9_-]+)",
            body[:4096],
            re.I,
        )
        encoding = match[1].decode("ascii") if match else "utf-8"
    warnings: list[str] = []
    try:
        # Restrict to text encodings; codecs such as base64/zip are not decoders here.
        canonical = codecs.lookup(encoding).name
        if canonical not in {
            "utf-8",
            "utf-8-sig",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "ascii",
            "cp1252",
            "iso8859-1",
        }:
            raise LookupError
        text = body.decode(canonical)
    except (UnicodeError, LookupError):
        canonical = "cp1252"
        text = body.decode(canonical, errors="replace")
        warnings.append("encoding_fallback")
    if "\ufffd" in text:
        warnings.append("encoding_replacement")
    return text, canonical, tuple(warnings)


def load_dom(body: bytes) -> DOM:
    if not body or len(body) > MAX_BYTES:
        raise ParseError("source_size_limit")
    text, encoding, warnings = decode(body)
    parser = etree.HTMLParser(
        encoding="utf-8",
        recover=True,
        no_network=True,
        huge_tree=False,
        remove_comments=False,
        collect_ids=False,
    )
    parser.resolvers.add(_DenyResources())
    try:
        root = etree.fromstring(text.encode("utf-8"), parser)
    except (etree.LxmlError, ValueError):
        raise ParseError("html_unparseable") from None
    if root is None:
        raise ParseError("html_unparseable")
    errors = list(parser.error_log)
    if any(e.level_name == "FATAL" or "RESOURCE_LIMIT" in e.type_name for e in errors):
        raise ParseError("dom_resource_limit")
    count = 0
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise ParseError("dom_resource_limit")
        stack.extend((child, depth + 1) for child in node)
    if errors:
        warnings += ("html_recovered",)
    return DOM(root, encoding, warnings)


def tag(node: etree._Element) -> str:
    return node.tag.lower() if isinstance(node.tag, str) else ""


def locator(node: etree._Element) -> str:
    # Numeric child positions work with ix: tags without binding arbitrary source namespaces.
    indices: list[int] = []
    current = node
    while (parent := current.getparent()) is not None:
        indices.append(
            1 + sum(isinstance(s.tag, str) for s in current.itersiblings(preceding=True))
        )
        current = parent
    return "/*[1]" + "".join(f"/*[{i}]" for i in reversed(indices))


def resolve(root: etree._Element, path: str) -> etree._Element:
    matches = root.xpath(path)
    if (
        not isinstance(matches, list)
        or len(matches) != 1
        or not isinstance(matches[0], etree._Element)
    ):
        raise ValueError("DOM locator must resolve to exactly one element")
    return matches[0]
