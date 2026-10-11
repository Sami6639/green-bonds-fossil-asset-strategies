#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,hashlib,json
p=Path(__file__).resolve().parent
for e in json.loads((p/'nested_histories/source_manifest.json').read_text()):
 f=p/'nested_histories'/e['file']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256'],f
for e in json.loads((p/'inputs/snapshot_manifest.json').read_text()):
 f=p/'inputs'/Path(e['frozen_path']).name
 assert hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256'],f
subprocess.run([sys.executable,str(p/'analysis_panel/build_panel.py'),'--replay-manifest',str(p/'inputs/snapshot_manifest.json'),'--output-dir',str(p/'analysis_panel')],check=True)
subprocess.run([sys.executable,str(p/'analysis_panel/results/build_capacity_results.py'),'--panel-root',str(p/'analysis_panel')],check=True)
subprocess.run([sys.executable,str(p/'analysis_panel/results/validate_capacity_results.py')],check=True)
subprocess.run([sys.executable,str(p/'figures/build_manuscript_figures.py')],check=True)
subprocess.run([sys.executable,str(p/'figures/validate_figure_artifacts.py')],check=True)
