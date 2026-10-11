MANUSCRIPT FIGURES

Three author-generated figures, delivered as 300-dpi PNG and vector PDF.
Captions are deliberately separate from the image. Concise main-copy
captions are in figure_main_captions.txt and each figure's main_caption field
in figure_manifest.json. Full captions remain in figure_captions.txt and the
caption field for supplementary methodological detail.

Build from the figures directory:
    python build_manuscript_figures.py

Or specify a frozen result directory and the WEC project-stage panel:
    python build_manuscript_figures.py --results /path/to/results \
        --wec-panel /path/to/wec_project_stage_panel.csv --out /path/to/figures

Dependencies: Python 3, numpy, pandas and matplotlib; the independent
validator also uses Pillow. Exact tested versions are in requirements.txt.

Portable layout:
    integration/figures/build_manuscript_figures.py
    integration/figures/validate_figure_artifacts.py
    integration/figures/source_data/sse_gb5_maturity_project_weights.csv
    integration/figures/source_data/sse_actual_milestones.csv
    integration/figures/source_data/wec_project_stage_panel.csv
    integration/analysis_panel/results/group_capacity_results.csv
    integration/analysis_panel/results/group_sign_band_sensitivity.csv
    integration/analysis_panel/results/clean_wind_solar_sensitivity.csv
    integration/analysis_panel/results/results_build_manifest.json

Defaults resolve from the builder's own location, not the current working
directory. Input paths in the manifests are relative to the output directory.
The validator resolves those paths relative to its own figure directory.
Corporate source reports are not needed for offline figure reproduction.

Figure 1 uses one reviewed selected window per utility group, ordered
alphabetically. Period and scope labels remain visible. Directions are
source-defined within-group descriptions, not performance rankings.

Figure 2 recomputes the 0%, 0.5% and 1% retrospective bands from opening
capacity and endpoint changes, verifies reported/strict-RE classifications
against the result builder, and emits the complete group-by-band data and
count tables. Paired denominators, rather than overall group counts, govern
each bar. Missing observations are never imputed as zeros.

Figure 3 recomputes stock-weighted full-operation shares from source-derived
project rows. The SSE input extract, actual milestone ledger and WEC panel
are archived in source_data/, with original archive provenance. SSE fixed
weights differ from WEC cutoff-specific
weights. The stage measure is not measured production or a causal estimate.

Reproducibility and quality checks:
- figure_provenance_manifest.json records SHA-256 hashes of all read inputs.
- figure_1_plot_data.csv preserves full scopes and source URLs.
- figure_2_group_band_data.csv and figure_2_counts.csv preserve exact counts.
- figure_3_plot_data.csv preserves stage values, amounts, cutoffs and sources.
- figure_validation.json records automatic assertions.
- independent_artifact_validation.json records independently recomputed checks.
- portable_replay_validation.json records an offline copied-layout replay.
- visual_qa.json records the final rendered-image inspection after freeze.
- New group IDs require explicit review of short display-scope labels.

The default build refreshes from current integration results. Use a frozen
input directory to reproduce an earlier snapshot. Do not describe a result
snapshot as final before the panel and figure provenance hashes are frozen.

No raw corporate reports or source PDFs are redistributed here.
