**Green Bond Financing and Fossil Asset Strategies in Electric Utilities**

Data and code for a source-linked, purposive archival study of utility financing and capacity trajectories, with historical endpoints spanning 2019–2024. The current expanded analysis contains 33 principal fuel-identified utility-group scopes and four matched unsplit-thermal proxy extensions. Named subsets, ownership bases, reporting boundaries and missing observations remain explicit. Question-specific and paired comparisons use their own eligible denominators.

The evidence supports descriptive comparisons within reported scopes. It does not establish causal financing effects, financing additionality or population-wide prevalence. Capacity changes are not equated with physical plant closures, and companies are not ranked.

**Current expanded analysis**

- [Analytical panel guide](analysis_panel/README.txt): scope, eligibility, measurement boundaries and limitations.
- [Executed protocol](analysis_panel/executed_protocol.json): documented analytical rules.
- [Descriptive results](analysis_panel/results/): capacity-window tables, finance and event evidence, sensitivities and validation records; start with the [results guide](analysis_panel/results/README.txt).
- [Figures](figures/): three figures, source-derived plot data and verification records.
- [Nested histories](nested_histories/): supporting case-level evidence.
- [Frozen inputs](inputs/): source-derived observations and provenance manifest.

The expanded release is installed directly at this repository's root. Its entry point is [run_reproduce.py](run_reproduce.py). After installing the dependencies in [requirements.txt](requirements.txt), run from the repository root:

```text
python run_reproduce.py
```

This command verifies frozen input hashes, rebuilds the panel and descriptive results, and regenerates and validates the figures. Reproduction uses the included source-derived files; no network connection or original corporate reports are required after dependencies are installed. Original reports are referenced as audit sources and are not redistributed.

The upload instructions in [README.txt](README.txt) describe adding the portable package as a separate versioned directory. This repository instead contains its files at the root; use the root command above. The root [package_sha256.json](package_sha256.json) records the expanded package's file checksums.

**Earlier release and repository history**

The earlier three-core Enel, Iberdrola and SSE analysis remains available in [PACKAGE_README.txt](PACKAGE_README.txt), [main_exhibits/](main_exhibits/) and [joint_strategy/](joint_strategy/). Its historical workflow uses run_analysis.py and validate_package.py. These are retained for provenance and are separate from the expanded reproduction entry point. Earlier files and documentation can also be inspected through the repository's Git history; legacy outputs should not be mixed with the current expanded results.
