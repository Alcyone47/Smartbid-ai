"""In-memory model factories for matching tests (no DB session needed)."""

from app.models.extraction import ExtractedRequirement, ExtractedSpecification


def make_requirement(
    *,
    key: str = "param",
    label: str = "Parameter",
    text: str = "",
    expected_value: str | None = None,
    unit: str | None = None,
    operator: str | None = None,
    is_mandatory: bool = True,
    category: str | None = None,
    equipment_key: str = "general",
    equipment_label: str = "General",
) -> ExtractedRequirement:
    return ExtractedRequirement(
        equipment_key=equipment_key,
        equipment_label=equipment_label,
        requirement_key=key,
        requirement_label=label,
        requirement_text=text,
        expected_value=expected_value,
        unit=unit,
        operator=operator,
        is_mandatory=is_mandatory,
        category=category,
    )


def make_specification(
    *,
    key: str = "param",
    label: str = "Parameter",
    text: str = "",
    value: str | None = None,
    unit: str | None = None,
    vendor_name: str = "Acme",
    equipment_key: str = "general",
    equipment_label: str = "General",
) -> ExtractedSpecification:
    return ExtractedSpecification(
        equipment_key=equipment_key,
        equipment_label=equipment_label,
        spec_key=key,
        spec_label=label,
        spec_text=text,
        value=value,
        unit=unit,
        vendor_name=vendor_name,
    )
