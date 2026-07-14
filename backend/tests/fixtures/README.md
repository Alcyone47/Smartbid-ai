# RFP test fixtures

Drop real sample RFP PDFs into `rfps/` to exercise the parser and the semantic
structure-selection pass against multiple real-world formats.

For each PDF you add, register it in `manifest.py` with the section titles you
expect to be classified **technical** vs **non-technical**. Tests then:

1. Parse each PDF (deterministic) and assert candidate headings/TOC are detected.
2. Feed the parsed structure digest through the analyzer with a fake LLM to
   confirm technical sections are selected and admin/commercial/legal/SLA/
   payment/eligibility sections are ignored.

If `rfps/` is empty, the fixture-backed tests are skipped so the suite stays green.
Real LLM calls are never made in CI — classification is stubbed via the fake
provider; the PDFs only feed the deterministic parser.
"""
