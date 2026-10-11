#!/usr/bin/env python3
"""Independent stdlib validation of the derived CSV arithmetic and source links."""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
from datetime import date
import csv,json,hashlib
P=Path(__file__).resolve().parent

def rows(n):return list(csv.DictReader((P/n).open()))
def n(x):return Decimal(x) if x not in ['',None] else None
checks=[];issues=[]
def check(label,ok,detail=''):
    checks.append({'check':label,'passed':bool(ok),'detail':detail})
    if not ok:issues.append(label+': '+str(detail))
groups=rows('group_capacity_results.csv');G={r['group_id']:r for r in groups}
check('One row per selected utility group',len(G)==len(groups))
for r in groups:
    for prefix in ['fossil','renewable','strict_RE']:
        a,b,d=[n(r[prefix+k]) for k in ['_start_mw','_end_mw','_delta_mw']]
        check(r['group_id']+' '+prefix+' delta and missingness',(a is None and b is None and d is None) or (None not in [a,b,d] and abs((b-a)-d)<=Decimal('0.00000001')))
    for side in ['lower','upper']:
        x=n(r['antecedent_fraction_'+side]);check(r['group_id']+' antecedent '+side,x is None or 0<=x<=1)
components=rows('capacity_component_results.csv');prov=rows('capacity_endpoint_provenance.csv');by=defaultdict(list)
for p in prov:by[(p['measure_id'],p['endpoint'])].append(p)
source_recomputations=0
for c in components:
    check(c['measure_id']+' delta',n(c['start_mw']) is not None and n(c['end_mw']) is not None and abs(n(c['end_mw'])-n(c['start_mw'])-n(c['delta_mw']))<=Decimal('0.00000001'))
    g=G[c['group_id']];check(c['measure_id']+' same selected window',(c['start_date'],c['end_date'])==(g['start_date'],g['end_date']))
    for ep in ['start','end']:
        ps=by[(c['measure_id'],ep)];vv=[n(p['value_numeric'])*(1000 if p['unit']=='GW' else 1) for p in ps if n(p['value_numeric']) is not None and p['unit'] in ['MW','GW']]
        expected=n(c[ep+'_mw'])
        # A reviewed scalar can have duplicate corroborating observations. A vector is disjoint.
        matching=bool(vv) and (sum(vv)==expected or set(vv)=={expected})
        check(c['measure_id']+' '+ep+' source arithmetic',matching,{'expected':str(expected),'source_values':[str(v) for v in vv]})
        source_recomputations+=1
        check(c['measure_id']+' '+ep+' source links',bool(ps) and all(p['source_url'] for p in ps))
        check(c['measure_id']+' '+ep+' capacity only',all(p['unit'] in ['MW','GW'] for p in ps))
for r in rows('selected_window_finance_evidence.csv'):
    check(r['record_id']+' finance is not a physical unit',r['unit'] not in ['MW','GW','MWh','GWh','TWh'])
for r in rows('leave_one_group_out_descriptive_counts.csv'):
    count=sum(int(v) for k,v in r.items() if k.startswith('RE_'))
    check('LOO '+r['cohort']+' '+r['omitted_group_id']+' '+r['boundary'],count==int(r['remaining_complete_pairs']) and int(r['remaining_group_rows'])==int(r['remaining_complete_pairs'])+int(r['remaining_incomplete_pairs']))
canonical={r['record_id']:r for r in csv.DictReader((P.parent/'canonical_observations.csv').open())}
for r in rows('clean_wind_solar_sensitivity.csv'):
    if r['available']!='True':
        check(r['group_id']+' missing wind/solar not zero filled',r['wind_solar_start_mw']==r['wind_solar_end_mw']=='');continue
    for ep in ['start','end']:
        ids=r[ep+'_record_ids'].split(';');oo=[canonical[k] for k in ids if k in canonical]
        vv=[n(o['value_numeric'])*(1000 if o['unit']=='GW' else 1) for o in oo]
        check(r['group_id']+' clean wind/solar '+ep+' source sum',len(oo)==len(ids) and all(v is not None for v in vv) and sum(vv)==n(r['wind_solar_'+ep+'_mw']))
        check(r['group_id']+' clean wind/solar '+ep+' exact scope and date',all(o['ownership_basis']==r['ownership_basis'] and o['operating_scope']==r['operating_scope'] and o['date_upper']==r[ep+'_date'] for o in oo))
        check(r['group_id']+' clean wind/solar '+ep+' no compound solar',not any('other' in (o['metric']+' '+o['technology']).lower() for o in oo))
for r in rows('group_sign_band_sensitivity.csv'):
    for family,cap,dd,out in [('RE','RE_opening_mw','RE_delta_mw','RE_direction_at_band'),('fossil','fossil_opening_mw','fossil_delta_mw','fossil_direction_at_band')]:
        a,d,band=n(r[cap]),n(r[dd]),n(r['band_pct_of_opening_capacity'])
        if a is None or d is None:expected='unresolved'
        elif a==0 and band>0:expected='undefined_relative_band_zero_baseline'
        elif abs(d)<=abs(a)*band/100+Decimal('0.00000001'):expected='within_declared_band'
        else:expected='increase' if d>0 else 'decrease'
        check(r['group_id']+' '+family+' band '+str(band)+' '+r['boundary'],r[out]==expected)
summary=rows('descriptive_capacity_summary.csv')
check('No cross-group median/min/max MW magnitude summary',all(not any(k in r for k in ['median_delta_mw','minimum_delta_mw','maximum_delta_mw']) for r in summary))
for r in groups:
    if r['fossil_boundary_class']=='identified_coal_and_CCGT_subset':
        used=[p for p in prov if p['group_id']==r['group_id'] and '_fossil_' in p['measure_id']]
        check(r['group_id']+' principal known-fuel subset excludes unsplit cogeneration',bool(used) and all('cogeneration' not in p['technology'].lower() for p in used))
    check(r['group_id']+' principal and proxy tiers disjoint',not (r['principal_analysis_include']=='True' and r['matched_proxy_extension_include']=='True'))
# Exact canonical values are checked; no test pretends to certify original-document extraction.
result={'status':'PASS' if not issues else 'FAIL','checks':len(checks),'failed_checks':len(issues),'endpoint_source_arithmetic_recomputations':source_recomputations,'issues':issues,'scope':'Derived CSV arithmetic, units, within-group window identity, source-link presence, timing bounds and leave-one-out denominators. Original document extraction and parent admissions remain independently auditable.'}
(P/'independent_results_validation.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'independent_validation_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(result,indent=2))
if issues:raise SystemExit(1)
