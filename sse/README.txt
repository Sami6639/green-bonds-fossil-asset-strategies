SSE bounded pilot extraction — 10 October 2026

Coverage
Three fiscal years ending 31 March 2022, 2023 and 2024. Values for 2022 and 2023 come from the official 2023 annual report; 2024 values come from the 2024 annual report. Each row records the reporting period, unit, exact source row, column and page.

Project coverage is one 2024 reporting snapshot. All direct-generation project rows in Tables 2, 3 and 6 are included; the HVDC rows in Tables 2 and 3 are retained to distinguish networks. Transmission-only Tables 4 and 5 are not extracted. This is not a complete bond-project universe or a three-year project panel.

Files
- issuer_year_cells.csv: 60 long-form cells, including two explicitly unverified blanks (2024 GB thermal capacity and 2024 hydro capacity).
- bond_project_rows_2024.csv: 16 bond-project rows, including two HVDC entries and the source-dash Gordonbush/GB6 row. Eleven distinct generation projects and one HVDC asset.
- bond_project_cell_provenance.csv: 96 field-level provenance records.
- bond_register_2024.csv: seven reporting bond groups; group 4 combines two ISINs.
- asset_event_ledger.csv: Tarbert closure, Triton acquisition, Keadby 2 commissioning, and Seabank PPA reporting-scope change.
- derived_comparable_generation.csv: wind plus conventional hydro, with an explicit arithmetic formula.
- validation.json: successful component-sum checks. No regressions.
- extract_sse.py: reproducible CSV export from manually transcribed cells.

Verification limits
The 2023 report and 2024 bond report were readable through official PDF text returned by the web tool. The 2024 annual report cells came from indexed official PDF excerpts. Direct local 2024 PDF downloads returned HTTP 403; bond-report screenshots returned cache errors. These are text-checked cells, not a completed visual audit. No source PDF is bundled here.

Interpretation rules
1. FY2024 is 1 April 2023 to 31 March 2024, not calendar 2024.
2. Thermal output includes 100% of Marchwood PPA production despite 50% equity ownership. Seabank changed from 100% PPA to 50% equity output after September 2021. The 2023 scope adds Triton and excludes 1,184 GWh of Keadby 2 pre-commissioning output. These prevent an automatic constant-perimeter interpretation.
3. The 9,927 GWh FY2024 renewable aggregate includes 315 GWh of pumped storage. The 11,158 GWh headline also includes 1,231 GWh of compensated constrained-off wind. Derived wind plus conventional hydro is 9,612 GWh; this excludes biomass, which sits outside SSE Renewables. Preserve these definitions rather than label one total simply 'renewables'.
4. The bond report explicitly classifies all seven groups as refinancing and fully allocated at settlement. Refinancing does not imply an already operational asset: Viking was under construction. Financial purpose and project maturity are separate fields.
5. Allocations are reported allocation stocks, not incremental annual cash flows. Reallocation, repayment and foreign-exchange effects need reconciliation before differencing.
6. Table 6 publishes the physical project attributes and output once, alongside GB5 and GB6 allocation columns. The analytical long-form CSV repeats shared physical attributes when expanding those allocation columns into rows; this is not issuer double counting. Physical GWh must be counted once per project and reporting year. Gordonbush has a GB6 dash, so no GB6 allocation link is established. Splitting output by allocation weights would be an analyst assumption, not reported information.
7. Network MW/MVA measure connection or transmission capability. They are not power generation. SHET capex is reported at 100% despite 75% ownership after September 2022.
8. The Gordonbush/GB6 dash remains source_dash, not numerical zero. Viking output 0.0 is a reported zero. Its future operational date is explicitly expected_at_report. Individual project countries remain blank pending verification; the source portfolio includes UK and Irish projects.
9. Tarbert's old 620 MW oil station closed in December 2023. This does not establish that the entire site permanently ceased generating, or that a green bond caused closure.

Missing work
Project allocation and generation reports for 2022/2023 are not extracted. Plant identifiers, individual locations, complete historical ownership, coal output and absolute emissions require further checks. No missing coal value has been set to zero. Two 2024 capacity cells remain unverified rather than inferred. Transmission-only Tables 4/5 remain outside this bounded extraction. No counterfactual or globally representative sample is established.
