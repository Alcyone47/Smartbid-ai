"""Expected structure classification per sample RFP fixture.

Register each PDF you drop into ``tests/fixtures/rfps/`` here so the fixture-backed
tests know which sections should be technical vs non-technical. Example:

    RFP_FIXTURES = [
        RfpFixture(
            filename="metro_network_rfp.pdf",
            technical_sections=["Technical Specifications", "Scope of Supply"],
            non_technical_sections=["Eligibility Criteria", "Payment Terms", "SLA"],
        ),
        RfpFixture(
            filename="datacenter_ups_tender.pdf",
            technical_sections=["Technical Particulars", "Bill of Materials"],
            non_technical_sections=["Instructions to Bidders", "Commercial Bid"],
        ),
    ]

Provide at least three fixtures spanning different formats to satisfy the
"multiple RFP formats" requirement.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RfpFixture:
    filename: str
    technical_sections: list[str] = field(default_factory=list)
    non_technical_sections: list[str] = field(default_factory=list)


# Populate this list as real sample PDFs are added to tests/fixtures/rfps/.
RFP_FIXTURES: list[RfpFixture] = []
