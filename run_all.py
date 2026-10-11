#!/usr/bin/env python3
"""Rebuild expanded panel, supplementary workflows and revision checks."""
from pathlib import Path
import datetime, hashlib, importlib.metadata, json, platform, subprocess, sys, time
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'revision_checks';OUT.mkdir(exist_ok=True)
commands=['run_reproduce.py','strategy_comparison/build_theory_evidence.py','decision_rationales/build_audit.py','decision_rationales/build_evidence.py','revision_checks/apply_interpretation_corrections.py','revision_checks/build_revision_checks.py']
report={'version':'BSE-2026-10-11-r3','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'dependencies':{n:importlib.metadata.version(n) for n in ['numpy','pandas','matplotlib','Pillow']},'commands':[],'scope':'Clean-copy computational reproduction; no original-report semantic re-verification implied.'}
def hashes():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['analysis_panel','figures','strategy_comparison','decision_rationales'] for p in (ROOT/base).rglob('*.csv')}
before=hashes()
for command in commands:
 start=time.monotonic();p=subprocess.run([sys.executable,str(ROOT/command)],cwd=ROOT,text=True,capture_output=True)
 name=command.replace('/','_')+'.log';(OUT/name).write_text(p.stdout+'\nSTDERR\n'+p.stderr)
 report['commands'].append({'command':'python '+command,'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'log':'revision_checks/'+name})
 if p.returncode:break
after=hashes();report['csv_comparison']={'compared_files':len(before),'byte_identical_files':sum(after.get(k)==v for k,v in before.items()),'changed_files':[k for k,v in before.items() if after.get(k)!=v]};report['passed']=len(report['commands'])==len(commands) and all(x['exit_code']==0 for x in report['commands']);report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'reproduction_log.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'commands':report['commands'],'csv_comparison':report['csv_comparison']},indent=2))
sys.exit(0 if report['passed'] else 1)
