Ørsted utility-transition pilot, 10 October 2026

Start with quality_note.txt and issuer_year_panel_view.csv.

Files and keys:
- issuer_year_panel_view.csv: three issuer-calendar-year records, a convenience view. Fossil-electricity and unique fossil-capacity targets are deliberately blank.
- issuer_year_observations.csv: 89 metric/source observations; observation_id is unique. Alternative 2024 capacity observations are retained with is_preferred_observation=false. Always filter this field before pivoting.
- projects_2024.csv: 22 unique project_id records. Allocation amounts are DKK million and ownership-adjusted; physical MW/GWh are full-project. Attributed physical values are unavailable, not zero.
- bond_summary_2024.csv: 23 unique ISINs; 22 outstanding and one redeemed in 2024. Reported maturity dates of hybrids in the 3000s are preserved from the table. Dates are normalized to ISO format.
- allocation_2024.csv: 26 unique instrument-project-2024 flows. Repeated project IDs across instruments are intentional. Do not sum physical output after joining without project deduplication.
- allocation_history_to_2023.csv: 374 instrument-project cells, cumulative over 2017–2023. annual_allocation_year is blank. Bond issue year is not allocation year.
- event_ledger.csv: seven event records; date precision follows source wording. Closure, temporary return, cessation of operation, fuel switching, and loss of coal capability are separate event classes.
- cell_provenance.csv: field-level source IDs, page numbers, source row and column labels, source URLs, and raw-value/dash status. Numerals omit display thousands separators. Bond dates use ISO normalization rather than printed day-month-year typography. Printed and PDF page numbers are identical for all three reports.
- source_manifest.csv: three official PDFs with URLs and SHA-256 hashes.
- validation_checks.csv / quality_profile.json: reproducible checks and the retained source conflicts. FAIL means disagreement with a printed source comparator, not an automatically corrected observation.
- build_orsted_pilot.py: transparent manual transcription plus standard-library generation/check code. Requires the three verified PDFs in sources/ only to hash their provenance; all transcribed factual inputs are in the script.
- validate_orsted_pilot.ipynb: portable checks of the CSV deliverables; notebook code was executed successfully.
- source_name_aliases.csv: explicit spelling mappings across tables.

Null conventions:
A blank numeric value is missing/unavailable. Raw '-' in generation is never a zero. Allocation dashes remain blank and are treated as zero solely inside arithmetic reconciliation tests. The 2024 coal-capability dash is explicitly normalized to zero using the table's 991 MW prior value and -991 MW change; raw '-' is preserved. This is not 991 MW of physical retirement.

Do not treat the 2024 finance report as a 2022–2024 project panel. Project histories, annual allocations for 2022 and 2023, ownership fractions, project CAPEX, fuel-specific electricity output, and exact asset retirement/commissioning dates require further source collection. These files provide a bounded, source-auditable descriptive pilot, not an econometric design or causal estimate.

The sources/ directory is local research evidence. Source PDFs and screenshots should be excluded from a public data archive unless redistribution rights are established. Deliver the derived CSVs, checks, notes, manifest, and script instead.

Targeted supplement: capacity_bridge_2024.csv and capacity_bridge_note.txt retain the unresolved -70 MW remainder after the explicitly identified Esbjerg and Kyndby reductions. This supplement does not change the original 113 checks or add fossil-capacity estimates.
