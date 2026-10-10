"""Offline rebuild of derived analysis, figures, workbook and data-only archive.
Requires Python 3, pandas, matplotlib and openpyxl. Uses extracted CSV snapshots.
Does not download sources, fit regressions, or alter external services.
"""
from pathlib import Path
import subprocess,sys
P=Path(__file__).parent
for name in ['integrate_pilot.py','integrate_history.py','build_main_exhibits.py','build_pool_continuity.py','build_review_analytics.py','build_joint_strategy.py','validate_issue_date_provenance.py','package_derived_data.py']:
 subprocess.run([sys.executable,str(P/name)],cwd=P,check=True)
