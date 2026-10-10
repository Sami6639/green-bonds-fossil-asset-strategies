"""Optional reproducibility helper: fetch official URLs from source_manifest.csv.
Needs network permission and pdftotext. No login, form or third-party data sharing.
Saves stable source_id filenames in this folder, without altering source facts.
"""
from pathlib import Path
import csv,urllib.request,subprocess,hashlib
H=Path(__file__).parent
for r in csv.DictReader((H/'source_manifest.csv').open(encoding='utf-8-sig')):
 p=H/(r['source_id']+'.pdf')
 if not p.exists():
  with urllib.request.urlopen(r['source_url']) as response:p.write_bytes(response.read())
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if sha!=r['sha256']:print('WARNING changed source fingerprint:',r['source_id'])
 subprocess.run(['pdftotext','-layout',str(p),str(p.with_suffix('.txt'))],check=True)
