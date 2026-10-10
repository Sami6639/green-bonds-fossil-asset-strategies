**Green Bond Financing and Fossil Asset Strategies in Electric Utilities**

Reproducibility data and code for a purposive archival study of green-bond financing and fossil-asset strategies. The three core utilities are Enel, Iberdrola and SSE, with issuer-specific evidence spanning 2019–2024.

Matched strategy comparisons use adjacent Enel and Iberdrola report vintages and the SSE fiscal interval from 31 March 2023 to 31 March 2024. Reporting boundaries, disclosure gaps and unresolved observations remain explicit. The evidence does not establish causal financing effects, financing additionality or population-wide prevalence; the companies are not ranked.

- [Full package guide](PACKAGE_README.txt): analytical scope, source provenance, measurement limits and reproducibility details.
- [Main exhibits](main_exhibits/): four canonical tables, three figures, supporting evidence and the Excel workbook.
- [Matched strategy evidence](joint_strategy/): within-case interval comparisons and supporting records.

The supported offline rebuild uses the included source-derived CSVs. Original reports are linked and fingerprinted where available, rather than redistributed. Historical source-extraction scripts may require those original reports and are not the supported offline entry point.

Use the Python and dependency versions recorded in [BUILD_ENVIRONMENT.json](BUILD_ENVIRONMENT.json) and [requirements.txt](requirements.txt). From the extracted repository root, run:

```text
python run_analysis.py
python validate_package.py
```

The included clean-workspace reproduction records document the validated computational release. This repository-ready package preserves its scientific outputs; the publication-only documentation and provenance updates were checked separately for file integrity.
