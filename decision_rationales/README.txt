Documentary decision-rationale supplement

Purpose and limits
This supplement adds primary-source public decision accounts to the existing asset-event and financing histories. It does not identify private managerial motives or a causal effect of green-bond financing. No interviews, causal mediation estimates, scores or intercoder-reliability claims were produced.

Inclusion and selection
1. The frozen field-screening universe is every one of the 97 selected-window event records used in the principal 33-group comparison. These records cover 28 groups; the five groups without a selected-window event record remain explicitly unknown. All 97 JSON records were screened for existing decision, finance-link and rationale fields, including narrative context. This is an archive-field audit, NOT a full-text review of every underlying source or a search of all corporate decisions.
2. All seven pre-existing financial histories are retained in the separate companion comparison, including unresolved choice/authority information. This fixed set was not selected based on finding an attractive rationale.
3. New documentary extracts were purposively assembled for source-explicit decision accounts and contrasting observable actions: closure applications and regulatory conditions, an accepted compensation bid, an acquisition, ownership disposal, allocation substitution and retrospective reporting. Cases with a named asset/event, identified corporate or regulatory actor, dateable decision/implementation relationship, and an explicit explanation received priority. Both contemporaneous and retrospective documents are retained but separately labelled. This outcome-diverse purposive enrichment is NOT an outcome-blind probability sample, an exhaustive rationale search or a basis for cross-group motive frequencies.
4. Thirteen source extracts cover eleven groups, link to fourteen of the existing event records, and include three instrument/reporting-purpose observations, two of which lack an event-ledger identifier. Multiple event records may correspond to one facility sequence or disclosure (Moorburg and Castle Peak), so extract/record counts are not independent decisions.
5. Eighty-three event rows have no newly assembled extract in this supplement. That status is unknown, not no rationale. All examples concern groups already represented by the principal event archive or the fixed seven financial histories; Dominion is a finance-history companion, not added to the principal33 event denominator.

What is genuinely added
Endesa's original 19 December 2018 closure application supplies pre-outcome market/compliance reasoning, beyond a retrospectively reported decision date. It is antecedent evidence outside the event observation period, not a new 2018 outcome.
Vattenfall's original 1 December 2020 award statement identifies public compensation, possible alternatives and the system-relevance gate before closure.
AES's 7 December 2023 Norgener statement names board approval, the security condition, requested acceleration and resource prioritisation. Its Warrior Run filing identifies PJM approval and lack of economically viable alternatives.
RATCH's 2 May 2024 statement supplies a coal-acquisition growth/partnership rationale and long-term contractual context, avoiding a retirement-only narrative.
CLP's 9 May 2025 AGM minutes explicitly attribute its 2024 retirements to replacement gas and LNG infrastructure. This is retrospective corporate attribution, not contemporaneous evidence of intent.
SSE's contemporaneous Triton statement specifies reliability/flexibility and prospective abatement considerations.
WEC's May 2021 plan predates the September 2022 bond in the financial history. This supports temporal ordering only: it cannot establish that the bond had no implementation role.
The Enel allocation substitution and Dominion expenditure correction retain already-known explanations to locate the new decision evidence against reporting mechanisms; they are not sold as novel empirical discoveries.

Reproduction
Run python build_audit.py followed by python build_evidence.py. Requires Python and pandas. The first script reproduces all33 and all97 coverage and hashes from frozen inputs; the second recreates the hand-extracted matrix, the seven-case companion and event-to-extract crosswalk. Hand extraction is auditable against exact URLs, locators and short quotations, not machine-verified semantic coding. Retrieval/inspection date is 11 October 2026. The selected official documents were read through public web retrieval. Full source PDFs were not bundled here; short quotations and source locators are retained. No missing source text was imputed.

Field-screening facts
97 event records, 28 represented groups, 33 principal groups. Eleven records have nonempty decision-date fields, eight have decision-source URLs, no record has a dedicated rationale-named field, and three have finance_connection fields that expressly say a connection is not established. These are schema/field counts only and MUST NOT be rendered as zero rationales, only eleven actual decisions, or three cases proving no financing relationship.

Files
all33_group_coverage.csv: complete principal-group field-screening denominator.
all97_archive_field_audit.csv: complete archive-field screen and explicit new-extract crosswalk/unknowns.
decision_rationale_evidence.csv: thirteen source extracts with timing, attribution, authority, financing-link type and rival/unknown fields.
seven_history_rationale_coverage.csv: unchanged seven-history inclusion plus new rationale coverage boundaries.
audit_summary.json / evidence_summary.json: reproducible counts.
Source details and interpretation are described in Supplementary Information, Section S9.
