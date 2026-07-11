"""Deterministic compliance report generators (Excel / CSV / PDF).

Pure functions: compliance data in, file ``bytes`` out. No LLM, no DB.
"""

from app.services.reports.csv_report import generate_matrix_csv
from app.services.reports.data import ReportRow, build_report_rows
from app.services.reports.excel_report import generate_matrix_xlsx
from app.services.reports.pdf_report import generate_summary_pdf

__all__ = [
    "ReportRow",
    "build_report_rows",
    "generate_matrix_csv",
    "generate_matrix_xlsx",
    "generate_summary_pdf",
]
