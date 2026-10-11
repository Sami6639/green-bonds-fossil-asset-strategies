#!/usr/bin/env python3
"""Rebuild the current analysis and report computational validation boundaries."""
from pathlib import Path
import datetime
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'revision_checks'
OUT.mkdir(exist_ok=True)
VERSION = '2026-10-11-r4'
COMMANDS = [
    'run_reproduce.py',
    'strategy_comparison/build_theory_evidence.py',
    'decision_rationales/build_audit.py',
    'decision_rationales/build_evidence.py',
    'revision_checks/apply_interpretation_corrections.py',
    'revision_checks/build_revision_checks.py',
    'revision_checks/stage_weight_decomposition/build_stage_weight_decomposition.py',
]


def csv_hashes():
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ROOT.rglob('*.csv'))
    }


report = {
    'version': VERSION,
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python': sys.version,
    'platform': platform.platform(),
    'dependencies': {
        name: importlib.metadata.version(name)
        for name in ['numpy', 'pandas', 'matplotlib', 'Pillow']
    },
    'commands': [],
    'scope': (
        'Computational reproduction using included source-derived records. '
        'This command does not independently verify original issuer reports '
        'or establish financing effects.'
    ),
}
before = csv_hashes()
for command in COMMANDS:
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, command], cwd=ROOT, text=True, capture_output=True
    )
    log_name = command.replace('/', '_') + '.log'
    # Portable logs retain diagnostics without disclosing the executing machine's path.
    log = (result.stdout + '\nSTDERR\n' + result.stderr).replace(str(ROOT), '.')
    (OUT / log_name).write_text(log)
    report['commands'].append({
        'command': 'python ' + command,
        'exit_code': result.returncode,
        'elapsed_seconds': round(time.monotonic() - started, 3),
        'log': 'revision_checks/' + log_name,
    })
    if result.returncode:
        break

after = csv_hashes()
report['csv_comparison'] = {
    'compared_files': len(before),
    'byte_identical_files': sum(after.get(path) == digest for path, digest in before.items()),
    'changed_files': [path for path, digest in before.items() if after.get(path) != digest],
    'new_files': sorted(set(after) - set(before)),
    'scope': 'All pre-existing repository CSV files, including frozen records and derived outputs.',
}
report['passed'] = (
    len(report['commands']) == len(COMMANDS)
    and all(command['exit_code'] == 0 for command in report['commands'])
)
report['completed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT / 'reproduction_log.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({
    'passed': report['passed'],
    'commands': report['commands'],
    'csv_comparison': report['csv_comparison'],
}, indent=2))
sys.exit(0 if report['passed'] else 1)
