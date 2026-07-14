"""CSV export of the full compliance matrix (stdlib only)."""

from __future__ import annotations

import csv
import io

from app.services.reports.data import ReportRow, status_label

_HEADER = [
    "Equipment",
    "Requirement",
    "Detail",
    "Category",
    "Mandatory",
    "Expected",
    "Unit",
    "Operator",
    "Vendor",
    "Vendor Value",
    "Status",
    "Compliance %",
    "Explanation",
    "Source Page",
]


def generate_matrix_csv(rows: list[ReportRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_HEADER)
    for row in rows:
        writer.writerow(
            [
                row.equipment_label,
                row.requirement_label,
                row.requirement_text,
                row.category or "",
                "Yes" if row.is_mandatory else "No",
                row.expected_value or "",
                row.unit or "",
                row.operator or "",
                row.vendor_name,
                row.vendor_value or "",
                status_label(row.status),
                row.compliance_pct,
                row.rationale,
                row.source_page if row.source_page is not None else "",
            ]
        )
    # UTF-8 BOM so Excel opens accented text correctly on a double-click.
    return buffer.getvalue().encode("utf-8-sig")
