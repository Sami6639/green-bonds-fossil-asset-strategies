#!/usr/bin/env python3
"""Apply a dated semantic correction to derived displays, preserving frozen sources."""
from pathlib import Path
import csv, hashlib, json
ROOT=Path(__file__).resolve().parents[1]; HERE=Path(__file__).resolve().parent
note=('Constellation displayed categories sum to USD542m versus the USD541m printed total; signed residual (total minus category sum) -USD1m. Rounding is plausible but not explicitly explained in the reviewed source and remains unreconciled.')
replacements=[('preserve1m source rounding','preserve the unreconciled USD1m residual; rounding is plausible but not source-explained'),('due source rounding','with an unreconciled USD1m difference from the reported total; rounding is plausible but not source-explained'),('due reported rounding','with an unreconciled USD1m difference from the reported total; rounding is plausible but not source-explained'),('with rounding discrepancy','with an unreconciled reported-total/category-sum discrepancy'),('Allocation categories round1m above total.','Allocation categories sum USD1m above the reported total; rounding is plausible but not source-explained and remains unreconciled.')]
active_displays={'analysis_panel/results/group_capacity_results.csv','analysis_panel/results/capacity_component_results.csv','analysis_panel/results/selected_window_finance_evidence.csv','analysis_panel/results/contextual_window_finance_evidence.csv','figures/figure_1_plot_data.csv','strategy_comparison/seven_history_comparison.csv','decision_rationales/seven_history_rationale_coverage.csv'}
changed=[]
for directory in ['analysis_panel','figures','strategy_comparison','decision_rationales']:
 for path in (ROOT/directory).rglob('*.csv'):
  rel=path.relative_to(ROOT)
  if str(rel) not in active_displays:continue
  if 'frozen_inputs' in rel.parts or path.name in ['seven_history_handcoding.csv']:continue
  with path.open(newline='') as stream:
   reader=csv.DictReader(stream); fields=reader.fieldnames; rows=list(reader)
  if not fields:continue
  n=0; raw_notes=0
  for row in rows:
   if 'constellation' not in str(row).lower():continue
   for field in list(row):
    value=row[field]
    if not value:continue
    if field in ['source_raw_json','source_row_json','screening_raw_json']:
     pass # Quoted raw provenance is unchanged; dated overlay documents its supersession.
     continue
    for old,new in replacements:
     if old in value:value=value.replace(old,new);n+=1
    row[field]=value
  if n or raw_notes:
   if raw_notes and 'revision_semantic_note' not in fields:fields.append('revision_semantic_note')
   with path.open('w',newline='') as stream:
    w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)
   changed.append({'path':str(rel),'replacement_count':n,'raw_provenance_notes':raw_notes,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# A separate manifest describes corrected active outputs; historical manifests remain unmodified.
result={'version':'2026-10-11-r4','correction':note,'frozen_source_values_unchanged':True,'corrected_outputs':changed,'interpretation':'Historical source manifests validate the pre-correction scientific baseline; this manifest validates the derived semantic revision. Quoted raw provenance is preserved; the separate dated correction register records the revised interpretation.'}
(HERE/'corrected_output_manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
