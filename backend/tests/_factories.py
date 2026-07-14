"""In-memory model factories for matching/report tests (no DB session needed)."""

from app.models.extraction import ExtractedSpecification, Requirement, RequirementParameter


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
) -> RequirementParameter:
    """Build a single Parameter (with its Minimum Required Specification).

    In the hierarchy a Parameter is what the matching engine compares, so this is
    what the engine/report tests feed in. equipment_key/label are denormalized
    onto it exactly as the worker persists them.
    """
    return RequirementParameter(
        equipment_key=equipment_key,
        equipment_label=equipment_label,
        category=category,
        parameter_key=key,
        parameter_label=label,
        parameter_text=text,
        expected_value=expected_value,
        unit=unit,
        operator=operator,
        is_mandatory=is_mandatory,
    )


def make_requirement_group(
    *,
    equipment_key: str = "general",
    equipment_label: str = "General",
    parameters: list[RequirementParameter],
    category: str | None = None,
) -> Requirement:
    """Build a parent Requirement (one equipment/item) holding parameters."""
    for parameter in parameters:
        parameter.equipment_key = equipment_key
        parameter.equipment_label = equipment_label
    return Requirement(
        equipment_key=equipment_key,
        equipment_label=equipment_label,
        category=category,
        parameters=parameters,
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
