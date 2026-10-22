"""Financial lexical normalization boundary."""

from typing import Literal, Protocol, Self

from pydantic import Field, model_validator

from sec_research.contracts.canonical import ExactDecimal, Text, ValueModel


class NumericContext(ValueModel):
    """Only evidence-backed context; a dollar sign alone does not establish USD."""

    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    unit: Text | None = None
    scale: ExactDecimal | None = Field(default=None, gt=0)


class NormalizedNumber(ValueModel):
    """Value is the signed displayed number, before scale or percent conversion."""

    policy_version: Literal["table-numeric-1"] = "table-numeric-1"
    raw_text: str
    status: Literal["parsed", "missing", "not_numeric", "uncertain"]
    value: ExactDecimal | None = None
    sign: Literal["negative", "zero", "positive"] | None = None
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    unit: Text | None = None
    scale: ExactDecimal | None = Field(default=None, gt=0)
    percentage: bool | None = None
    missing: bool | None = None
    warnings: tuple[Text, ...] = ()

    @property
    def cell_status(self) -> Literal["parsed", "not_numeric", "empty", "uncertain"]:
        """Canonical-1 has no missing enum; retain nonblank dashes as uncertain."""
        if self.status == "missing":
            return "uncertain" if self.raw_text.strip() else "empty"
        return self.status

    @model_validator(mode="after")
    def consistent_number(self) -> Self:
        if (self.status == "parsed") != (self.value is not None):
            raise ValueError("only parsed results carry a value")
        if self.value is not None:
            expected = "negative" if self.value < 0 else "positive" if self.value > 0 else "zero"
            if self.sign != expected or self.missing is not False or self.percentage is None:
                raise ValueError("parsed result requires consistent sign, missing and percentage")
        elif self.sign is not None:
            raise ValueError("unparsed result cannot assert a numeric sign")
        if self.status == "missing" and self.missing is not True:
            raise ValueError("missing status requires explicit missing flag")
        if self.status != "missing" and self.missing is True:
            raise ValueError("missing flag requires missing status")
        if self.status != "parsed" and self.percentage is not None:
            raise ValueError("unparsed result cannot assert a percentage")
        if self.status in {"not_numeric", "uncertain"} and self.missing is not False:
            raise ValueError("nonmissing result requires explicit false missing flag")
        if self.status == "uncertain" and not self.warnings:
            raise ValueError("uncertain normalization requires a warning")
        return self


class NumericNormalizer(Protocol):
    def __call__(self, raw_text: str, *, context: NumericContext) -> NormalizedNumber: ...
