GLOBAL UTILITY FINANCING–CAPACITY ANALYTICAL PANEL

This source-linked purposive corpus contains question-specific analytical evidence; it is not a population sample or a causal design. Closed intake covers 2019–2024 endpoints. Raw source exports and original observation IDs are preserved. Missing values remain missing.

Current evidence tiers: 33 principal fuel-identified utility-group scopes; four matched unsplit-thermal proxy extensions; 37 broad matched groups. Named fuel subsets are explicitly distinguished from complete fossil fleets. Capacity ownership bases and renewable definitions vary and are not pooled in MW. SPIC remains unmatched physical context. Question-specific exclusions are retained in candidate_adjudication_queue.csv.

Run build_panel.py with --replay-manifest PATH --output-dir PATH to reproduce from frozen source-derived inputs. No network or original reports are required. Original source paths are provenance metadata; replay resolves frozen files relative to the supplied manifest. The portable release includes a run_reproduce.py entrypoint.

Core outputs:
- canonical_observations.csv preserves numeric/raw records, source IDs, URLs, locators, scopes and date resolution.
- reviewed_regional_window_panel.csv preserves all reviewed comparable windows.
- longest_reviewed_window_display.csv selects the longest supported window, then latest ending date and stronger financing-date tier, independently of outcomes.
- candidate_adjudication_queue.csv and question_specific_cohort.csv expose eligibility and analytical tiers.
- canonical_finance.csv distinguishes actual issuance, allocated stock, identified outstanding bond liabilities and annual allocation flows. Monetary-unit validation excludes physical/project measures from finance gates.
- finance_record_ids supplies contextual coverage including opening stocks; finance_admission_record_ids identifies later in-window records. Neither establishes uninterrupted financing, allocation persistence, or attribution of the entire capacity change.
- rq1_repeated_finance_candidates.csv is screening evidence, not automatic same-project continuity. new_nested_continuity_evidence.csv identifies explicitly reconciled new cases.
- canonical_project_stage_auxiliary.csv links the WEC stage evidence without duplicating financial observations.
- results/ contains descriptive signs, boundary and technology sensitivities, source-linked endpoints, finance timing and bounded event-type presence. No inferential p-values or population prevalence is reported.

ESB is a known coal-plus-gas subset; unknown historical oil is not zero. Iberdrola principal coal-plus-CCGT excludes fuel-unspecified cogeneration, with the broader reported vector retained separately. Storage-inclusive renewable proxies are labelled separately. Outstanding identified bond liability values may be principal, carrying values or lower bounds; no common monetary estimand is assumed.

Methods amendments and 0%, 0.5%, 1% sign bands were declared retrospectively, not preregistered. Event evidence is a bounded source scan, not an exhaustive plant census. Sales and dispatch exits remain distinct from physical closure.

Original reports are audit sources and are not included or represented as redistributable. Source-derived inputs, reproducible code and verification records are packaged for manual review/upload. No public repository publication is implied.
