Exact stage-versus-weight decomposition: SSE GB5 and WEPCO 4.75% due 2032

Purpose and scope
Implement a two-date accounting decomposition without changing the published r3 cohort, financing definitions, dates, allocations, stage codes or Figure 3. Five reporting entries at two cutoffs yield ten project-cutoff records. This is a descriptive accounting identity within two instruments, not a regression, causal effect, additionality estimate or company-wide transition ranking.

Run
Python 3 standard library only; no package installation or network call is required.
From any working directory:
  python /path/to/build_stage_weight_decomposition.py
From the repository root, run:
  python revision_checks/stage_weight_decomposition/build_stage_weight_decomposition.py
All writes are confined to this package's outputs/ directory.

Method
M_t = sum_i w_it O_it, where w_it = a_it / sum_i a_it.
Stage = sum_i (w_i0 + w_i1)/2 * (O_i1 - O_i0).
Weight = sum_i (O_i0 + O_i1)/2 * (w_i1 - w_i0).
M_1 - M_0 = Stage + Weight exactly.
Fraction arithmetic represents every reported decimal amount as an exact rational number. Components are multiplied by 100 for percentage-point reporting. This identity averages the two possible orderings of stage and weight changes and assigns their interaction symmetrically. It is not a model of a physical or causal mechanism.

Findings
SSE: 6.839493% to 69.479684%, a 62.640191 pp stage component and exactly zero weight component. Seagreen accounts for the entire change; Gordonbush already operates and Viking has not achieved full operation at either March cutoff.
WEC: 0% to 33.461975%, a 33.894637 pp stage component and a -0.432662 pp weight component. Badger Hollow II's monetary allocation rises but its normalized weight falls (34.327299% to 33.461975%); this offsets a small part of the stage-associated increase. Paris remains one mixed entry, coded not yet fully operating at both June cutoffs, without invented solar/storage subweights.

Inputs and source gates
inputs/ contains byte-for-byte copies of the r3 source-derived project CSVs, a Figure 3 regression target and their hash manifest. Separate source_verification.csv documents fresh primary-source semantic reinspection, URLs and page locations; executing the script does not itself reverify source meaning. The retained actual-milestone CSV provides a separate consistency check of the report-derived SSE operation codes. Its exact announcement-day dates are not needed for the decomposition: the directly verified operation months already resolve both cutoffs.
The project key normalizes only Seagreen1 versus Seagreen 1. The two SSE cutoffs are extracted separately before checking equality by project, avoiding an unsupported assumption of constant weights. The 2024 report's separate GB6 rows are excluded. Missing allocations, unknown stages and changed/unmatched membership stop execution. WEC's denominator is cumulative allocated/disbursed expenditure, not the USD 495.7m issue net proceeds. Month-level dates are retained as month intervals; an interval overlapping a cutoff cannot silently resolve a stage.

Primary review coverage
SSE 2023/2024 Table 6, PSC 5-UR-111 p70 and WEPCO 2024 Form 10-K p7 were freshly text-checked. Supplied WEC 2023 p1 and 2024 pp1-2 were text- and image-checked; source page images were inspected locally and are not redistributed. Use the original issuer URLs and page locators. SSE and PSC web screenshots were unavailable (Cache miss). Source review was performed by an assistant; no human second coder, independent human adjudication or agreement coefficient is asserted.

Outputs
outputs/stage_weight_decomposition.csv: exact-computation summary with decimal display, denominators, dates, currencies, source IDs and zero residual.
outputs/stage_weight_si_table.csv: compact six-decimal manuscript/SI table and source locators.
outputs/project_cutoff_inputs.csv: derived ten-row analysis input panel with allocation and stage sources, raw CSV row locations, amount, code and exact normalized weight.
outputs/project_contributions.csv: five project contributions, decimal pp and exact fractions.
outputs/recomputed_cutoff_shares.csv: four endpoints matching the unchanged published Figure 3 values.
outputs/exact_fraction_results.json: unrounded rational summary.
outputs/validation_checks.csv: all arithmetic, admissibility, scope, regression and negative-test checks.
outputs/validation_and_provenance.json: hashes, pass status and exact reconciliation.

Seven-history matrix
The separate seven-history linkage matrix records the verified SSE/WEC monetary and stage evidence; this package does not duplicate the existing seven-history narrative or expand the two-case arithmetic to unresolved cases. Iberdrola's monetary project weights and Eletrobras's matched stages remain unavailable. Dominion remains outside the principal 33. Enel's explicitly documented deconsolidation/substitution link must be distinguished from cross-source chronology or contemporaneous observation.

Reproduction limits
Byte-identical reruns establish computational reproducibility, not independently verified source truth. Reported decimal precision bounds the informational content; extra output decimals permit reconciliation and should not be interpreted as economic measurement precision. Full-operation 0 is a resolved not-yet-full status and does not imply no generation. No statistical uncertainty interval is attached to this deterministic identity. The identity does not remove uncertainty in the inputs or provide a counterfactual financing path.
