#!/usr/bin/env python3
"""Independent post-build checks of exported figure data and artifacts."""
from pathlib import Path
import csv, hashlib, json, math
from collections import Counter, defaultdict
from PIL import Image

P=Path(__file__).resolve().parent
def rows(name):
 with (P/name).open(newline='') as f:return list(csv.DictReader(f))
manifest=json.loads((P/'figure_manifest.json').read_text())
for name,metadata in manifest['inputs'].items():
 assert not Path(name).is_absolute(),f'Nonportable input path: {name}'
 assert hashlib.sha256((P/name).read_bytes()).hexdigest()==metadata['sha256'],f'Input changed: {name}'
g=rows('figure_1_plot_data.csv'); assert len(g)==len({r['group_id'] for r in g})
principal={r['group_id'] for r in g if r['principal_scope']=='True'}
details=rows('figure_2_group_band_data.csv')
assert len(details)==len({(r['group_id'],r['boundary'],r['band']) for r in details})
for r in details:
 if r['boundary'] in ('fuel_identified_comparator_subset','strict_storage_excluded_subset','clean_wind_solar_components'):
  assert r['group_id'] in principal,'Proxy returned through a narrow boundary.'
counts=rows('figure_2_counts.csv')
for c in counts:
 subset=[r for r in details if r['boundary']==c['boundary'] and float(r['band'])==float(c['band_pct_of_opening_capacity']) and r['paired_available']=='True']
 matching=[r for r in subset if r['pair_class']==c['pair_class']]
 assert len(subset)==int(c['paired_denominator'])
 assert len(matching)==int(c['groups'])
 assert set(c['group_ids'].split(';'))- {''}=={r['group_id'] for r in matching}
 assert int(c['eligible_cohort_group_denominator'])== (len(g) if c['boundary']=='reported_source_boundary' else len(principal))
stage=rows('figure_3_plot_data.csv')
assert len(stage)==4 and len({(r['issuer'],r['cutoff']) for r in stage})==4
for r in stage:
 calc=100*float(r['fully_operating_allocated_million'])/float(r['allocated_million'])
 assert math.isclose(calc,float(r['full_operation_share_pct']),rel_tol=1e-12,abs_tol=1e-12)
pngs={}; artifacts={}
for f in manifest['figures']:
 stem=f['stem']; spec=manifest['figure_dimensions'][stem]
 with Image.open(P/(stem+'.png')) as im:
  assert abs(im.width-spec['width_inches']*300)<2
  assert abs(im.height-spec['height_inches']*300)<2
  assert im.mode in ('RGB','RGBA')
  assert len(im.getcolors(maxcolors=10000000))>20
  pngs[stem]={'pixels':list(im.size),'dpi':list(im.info.get('dpi',[]))}
 for suffix in ('png','pdf'):
  path=P/(stem+'.'+suffix)
  assert path.stat().st_size>1000
  if suffix=='pdf': assert path.read_bytes().startswith(b'%PDF')
  artifacts[path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
out={'status':'pass','input_hashes_unchanged':True,'one_group_per_window':True,
     'band_counts_independently_reconciled':True,'no_proxy_in_principal_or_clean_subsets':True,
     'stage_percentages_independently_reconciled':True,'broader_groups':len(g),
     'principal_groups':len(principal),'PNG_dimensions':pngs,'artifacts':artifacts}
(P/'independent_artifact_validation.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
