import pytest

from sec_research.ingestion.cli import main, parser


def test_help_without_configuration_or_network(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
    assert "reconcile" in capsys.readouterr().out


def test_cli_missing_database_is_safe(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ingest", "--company", "1"]) == 2
    assert capsys.readouterr().out.strip() == '{"error": "invalid_configuration"}'


@pytest.mark.parametrize("value", ["0", "-1", "1001", "not-a-number"])
def test_cli_limit_validation(value: str) -> None:
    with pytest.raises(SystemExit) as caught:
        parser().parse_args(["ingest", "--company", "1", "--max-filings", value])
    assert caught.value.code == 2
