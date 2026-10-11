#!/usr/bin/env python3
"""Descriptive, source-linked group/window capacity results. Never adjudicates admission.
Reads canonical integration only; writes exclusively beside this script. Python stdlib.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date, datetime, timezone
import csv, json, hashlib, io, re, argparse

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--panel-dir','--panel-root',dest='panel_dir',type=Path,default=HERE.parent,help='Canonical analysis_panel folder; outputs remain beside this script.')
args=parser.parse_args()
P=args.panel_dir.resolve()
INPUTS=['longest_reviewed_window_display.csv','reviewed_regional_window_panel.csv','canonical_observations.csv','canonical_events.csv','regional_descriptive_envelopes.csv','candidate_adjudication_queue.csv','executed_protocol.json','canonical_candidate_windows.csv','canonical_finance.csv','group_mapping_review.csv','window_finance_links.csv']
FINANCE_CLASSES=['actual_issuance_flow','cumulative_allocated_stock','outstanding_identified_bond_liability','annual_allocation_flow']

def j(v, default=None):
    if not v:return {} if default is None else default
    try:return json.loads(v)
    except (ValueError,TypeError):return {} if default is None else default

def num(x):
    if x is None or x=='':return None
    try:return float(str(x).replace(',',''))
    except (TypeError,ValueError):return None

def clean(x):
    if isinstance(x,float):return round(x,9)
    if isinstance(x,(list,dict)):return json.dumps(x,ensure_ascii=False,sort_keys=True)
    return x

def write(name,rows,fields=None):
    rows=list(rows)
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with (HERE/name).open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:clean(r.get(k,'')) for k in fields})

def join(xs):return ';'.join(sorted(set(str(x) for x in xs if x)))
def urls(xs):return ' | '.join(sorted(set(str(x) for x in xs if x)))
def delta(a,b):return None if a is None or b is None else round(b-a,9)
def direction(a,b):
    d=delta(a,b)
    return 'unresolved' if d is None else ('increase' if d>1e-8 else 'decrease' if d < -1e-8 else 'unchanged_at_reported_precision')
def pct(a,b):return None if a in [None,0] or b is None else 100*(b-a)/a

def dates(raw):
    a=next((raw[k] for k in ['physical_start_date','physical_start_cutoff','physical_window_start','physical_endpoint_earliest'] if raw.get(k)), '')
    b=next((raw[k] for k in ['physical_end_date','physical_end_cutoff','physical_window_end','physical_endpoint_latest'] if raw.get(k)), '')
    def norm(s):
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s):return s
        m=re.search(r'March\s*(\d{4})',s)
        return m[1]+'-03-31' if m else ''
    return norm(a),norm(b)

def rank(w):
    duration=(date.fromisoformat(w['end_date'])-date.fromisoformat(w['start_date'])).days
    precision={'exact_cutoff':4,'exact_physical_cutoffs':4,'fully_bounded_flow_period':3,'bounded_report_vintage_alignment':1}.get(w.get('finance_timing_tier'),0)
    return (-duration,-date.fromisoformat(w['end_date']).toordinal(),-precision,w.get('source_file',''),w.get('reviewed_window_id',''))

# Stable read, detecting integration refresh. The retained input hashes establish exact build basis.
for attempt in range(4):
    blobs={f:(P/f).read_bytes() for f in INPUTS if (P/f).exists()}
    if all((P/f).read_bytes()==b for f,b in blobs.items()):break
else:raise RuntimeError('Integration inputs changed repeatedly during read; rerun after integration refresh.')
D={f:list(csv.DictReader(io.StringIO(b.decode('utf-8-sig')))) for f,b in blobs.items() if f.endswith('.csv')}
for rows_ in D.values():
    for row_ in rows_:
        for key_ in ['measure_class','finance_evidence_classes','finance_classes']:
            if key_ in row_:row_[key_]=row_[key_].replace('outstanding_principal_stock','outstanding_identified_bond_liability')
O=D['canonical_observations.csv']; OBS={o['record_id']:o for o in O}; SID=defaultdict(list)
for o in O:
    if o['source_observation_id']:SID[o['source_observation_id']].append(o)
BY=defaultdict(list)
for o in O:BY[o['group_id']].append(o)
E=[]
for e in D['regional_descriptive_envelopes.csv']:
    e=dict(e);e['raw']=j(e['source_raw_json']);e['dates']=dates(e['raw']);E.append(e)
AD={r['group_id']:r for r in D.get('candidate_adjudication_queue.csv',[])}
BPATH=HERE/'fossil_boundary_review.csv'
BLOB=BPATH.read_bytes() if BPATH.exists() else b''
BOUNDARY={r['group_id']:r for r in csv.DictReader(io.StringIO(BLOB.decode('utf-8-sig')))} if BLOB else {}

# Canonical observation evidence is attached even when a source-reviewed scalar controls a result.
def obs_ids(s):
    out=[]
    for x in re.split(r'[;|]',s or ''):
        if x in OBS:out.append(OBS[x])
        elif x in SID:out.extend(SID[x])
    return list({x['record_id']:x for x in out}.values())

def vector(v):
    vs=j(v,[]);out=[]
    for x in vs:
        if not isinstance(x,dict):continue
        oid=x.get('record_id')
        o=OBS.get(oid) or (SID.get(x.get('id') or x.get('source_observation_id')) or [None])[0]
        out.append(o or {'record_id':'','source_observation_id':x.get('id',''),'metric':x.get('metric',''),'technology':x.get('technology',''),'value_numeric':x.get('value_numeric',x.get('value','')),'unit':x.get('unit',''),'ownership_basis':'','operating_scope':x.get('scope',''),'source_url':'','source_locator':''})
    return out

def sum_vector(v):
    if not v:return None,'no_endpoint_vector'
    if any(num(x.get('value_numeric')) is None for x in v):return None,'missing_component'
    units={x.get('unit') for x in v}
    if not units.issubset({'MW','GW'}):return None,'non_capacity_unit'
    if len(units)!=1:return None,'mixed_units'
    if len(v)>1:
        if len({x.get('ownership_basis') for x in v})>1 or len({x.get('operating_scope') for x in v})>1:return None,'mixed_ownership_or_scope_components'
        labels=[(x.get('metric',''),x.get('technology','')) for x in v]
        if len(set(labels))!=len(labels):return None,'duplicate_or_nested_components'
        if any(re.search(r'(?:^|_)total|subtotal|renewable_total', ' '.join(l),re.I) for l in labels):return None,'nested_total_risk'
    return sum(num(x.get('value_numeric'))*(1000 if x['unit']=='GW' else 1) for x in v),'source_reviewed_disjoint_components' if len(v)>1 else 'source_value'

def evidence_matching(g,date_,metric=None,datafile=None,expected=None,source_urls=None):
    arr=[o for o in BY[g] if o['record_kind']=='physical_capacity' and o['date_upper']==date_ and o['unit'] in ['MW','GW']]
    if metric:arr=[o for o in arr if o['metric']==metric]
    if datafile:arr=[o for o in arr if o['source_file']==datafile or Path(o['source_file']).name==Path(datafile).name]
    if expected is not None:arr=[o for o in arr if num(o['value_numeric']) is not None and abs(num(o['value_numeric'])*(1000 if o['unit']=='GW' else 1)-expected)<1e-6]
    if source_urls:
        same=[o for o in arr if o['source_url'] and o['source_url'] in source_urls]
        if same:arr=same
    return arr

def metric_pair(g,a,b,metric,datafile=None,technology=None,cross_vintage_reviewed=False):
    va=evidence_matching(g,a,metric,datafile);vb=evidence_matching(g,b,metric,datafile)
    if technology:
        va=[o for o in va if o['technology']==technology];vb=[o for o in vb if o['technology']==technology]
    candidates=[]
    for x in va:
        for y in vb:
            if (x['ownership_basis'],x['operating_scope'],x['unit'])==(y['ownership_basis'],y['operating_scope'],y['unit']) and (x['source_url']==y['source_url'] or bool(set(x['source_url'].split(' | ')) & set(y['source_url'].split(' | '))) or cross_vintage_reviewed):
                candidates.append((x,y))
    values={(num(x['value_numeric']),num(y['value_numeric']),x['unit']) for x,y in candidates}
    if len(values)!=1:return None
    x,y=sorted(candidates,key=lambda t:(t[0]['record_id'],t[1]['record_id']))[0]
    f=1000 if x['unit']=='GW' else 1
    return dict(start=num(x['value_numeric'])*f,end=num(y['value_numeric'])*f,va=[x],vb=[y],label=metric+('_'+technology if technology else ''),method='source_reviewed_cross_vintage_same_scope_metric_pair' if cross_vintage_reviewed else 'same_primary_source_scope_metric_pair',raw={})

def fossil(w):
    raw=j(w['source_raw_json']); va=vector(w.get('endpoint_start_vector'));vb=vector(w.get('endpoint_end_vector'))
    a,methoda=sum_vector(va);b,methodb=sum_vector(vb)
    if num(w['physical_start_value_raw']) is not None and num(w['physical_end_value_raw']) is not None:
        # The reviewed scalar controls; its geography bridge is source review, not a new sum.
        a=num(w['physical_start_value_raw']);b=num(w['physical_end_value_raw']);unit=w['physical_unit']
        if unit not in ['MW','GW']:a=b=None
        elif unit=='GW':a=a*1000 if a is not None else None;b=b*1000 if b is not None else None
        va=va or obs_ids(raw.get('physical_start_observation_ids',''));vb=vb or obs_ids(raw.get('physical_end_observation_ids',''))
        if not va:va=evidence_matching(w['group_id'],w['start_date'],raw.get('fossil_capacity_metric'),raw.get('data_file'),a)
        if not vb:vb=evidence_matching(w['group_id'],w['end_date'],raw.get('fossil_capacity_metric'),raw.get('data_file'),b)
        if not va:va=evidence_matching(w['group_id'],w['start_date'],datafile=raw.get('data_file'),expected=a)
        if not vb:vb=evidence_matching(w['group_id'],w['end_date'],datafile=raw.get('data_file'),expected=b)
        methoda=methodb='source_reviewed_scalar'
    if w['group_id']=='rwe' and (not va or not vb):
        src=raw.get('physical_source_url','')
        def rf(dt):return [o for o in BY[w['group_id']] if o['date_upper']==dt and o['record_kind']=='physical_capacity' and o['source_url']==src and o['technology'] in ['gas','lignite','hard_coal'] and o['ownership_basis']=='IFRS accounting/consolidated']
        va=va or rf(w['start_date']);vb=vb or rf(w['end_date'])
    return dict(start=a,end=b,va=va,vb=vb,label=w['metric_family'],method=methoda+';'+methodb,raw=raw)

def renewable(w):
    raw=j(w['source_raw_json']);g=w['group_id'];a=w['start_date'];b=w['end_date'];out=[]
    # Direct same-window source-reviewed capacity values, retaining source-defined alternatives.
    for k1,k2,label in [('renewable_capacity_earliest_MW','renewable_capacity_latest_MW','source_reviewed_renewable_capacity'),('renewable_start_mw','renewable_end_mw','source_reviewed_renewable_capacity'),('reported_RE_category_capacity_earliest_MW','reported_RE_category_capacity_latest_MW','reported_RE_category_capacity')]:
        x,y=num(raw.get(k1)),num(raw.get(k2))
        if x is None or y is None:continue
        va=obs_ids(raw.get('renewable_start_id',''));vb=obs_ids(raw.get('renewable_end_id',''))
        if not va:va=evidence_matching(g,a,expected=x,source_urls=' '.join(str(v) for k,v in raw.items() if 'source' in k))
        if not vb:vb=evidence_matching(g,b,expected=y,source_urls=' '.join(str(v) for k,v in raw.items() if 'source' in k))
        if g=='kansai_electric_power' and label=='reported_RE_category_capacity':
            def kr(dt):return [o for o in BY[g] if o['date_upper']==dt and o['record_kind']=='physical_capacity' and o['ownership_basis']=='nonconsolidated' and o['metric'] in ['hydro_installed_capacity','other_renewable_installed_capacity']]
            va=va or kr(a);vb=vb or kr(b)
        out.append(dict(start=x,end=y,va=va,vb=vb,label=label,method='source_reviewed_same_window_scalar',raw=raw))
    for key in ['renewable_capacity_proxy_metric','renewable_capacity_partial_metric']:
        if raw.get(key):
            p=metric_pair(g,a,b,raw[key],raw.get('data_file'))
            if p:
                p['raw']=raw;p['partial']=key.endswith('partial_metric');out.append(p)
    if raw.get('renewable_capacity_metric'):
        p=metric_pair(g,a,b,raw['renewable_capacity_metric'],raw.get('data_file'))
        if p:p['raw']=raw;out.append(p)
        elif raw['renewable_capacity_metric'] in ['installed_capacity','effective_capacity']:
            p=metric_pair(g,a,b,raw['renewable_capacity_metric'],raw.get('data_file'),technology='renewables',cross_vintage_reviewed=True)
            if p:p['raw']=raw;out.append(p)
        # A separately reported inclusive boundary is a sensitivity, not an addition.
        alt=raw['renewable_capacity_metric'].replace('_excluding_pumped_storage','_reported_including_pumped_storage')
        if alt!=raw['renewable_capacity_metric']:
            p=metric_pair(g,a,b,alt,raw.get('data_file'))
            if p:p['raw']=raw;out.append(p)
    if g=='constellation_energy':
        p=metric_pair(g,a,b,'renewable_capacity_including_storage',raw.get('data_file'))
        if p:p['raw']=raw;out.append(p)
    for e in E:
        r=e['raw']
        if e['group_id']!=g or e['dates']!=(a,b) or 'renewable_capacity' not in r.get('metric_family',''):continue
        va=obs_ids(r.get('physical_start_observation_ids','')) or vector(r.get('earliest_values_json',''))
        vb=obs_ids(r.get('physical_end_observation_ids','')) or vector(r.get('latest_values_json',''))
        x,y=num(r.get('physical_start_value')),num(r.get('physical_end_value'))
        method='source_reviewed_same_window_scalar'
        if x is None:x,_=sum_vector(va);y,_=sum_vector(vb);method='source_reviewed_same_window_vector'
        if x is not None and y is not None:out.append(dict(start=x,end=y,va=va,vb=vb,label=r['metric_family'],method=method,raw=r))
    if g in ['china_huaneng','chn_energy'] and not out:
        # Source-defined proxy expression is explicit in the retained regional window.
        techs={'hydro_unsplit','wind','solar_pv'} if g=='china_huaneng' else {'hydro_unsplit','wind','solar_and_other_renewables_proxy'}
        def cp(dt):return [o for o in BY[g] if o['record_kind']=='physical_capacity' and o['date_upper']==dt and o['technology'] in techs and (not raw.get('data_file') or o['source_file']==raw['data_file'])]
        va,vb=cp(a),cp(b)
        x,mx=sum_vector(va);y,my=sum_vector(vb)
        if {o['technology'] for o in va}==techs and {o['technology'] for o in vb}==techs and x is not None and y is not None:
            out.append(dict(start=x,end=y,va=va,vb=vb,label='reported_hydro_wind_solar_proxy',method='source_declared_proxy_disjoint_component_sum',raw=raw))
    # Adjudicated nested SSE proxy: same metric and exact ownership/scope across report vintages.
    if g=='sse' and not out:
        va=evidence_matching(g,a,'renewable_capacity_including_storage')
        vb=evidence_matching(g,b,'renewable_capacity_including_storage')
        pairs=[(x,y) for x in va for y in vb if (x['metric'],x['ownership_basis'],x['operating_scope'],x['unit'])==(y['metric'],y['ownership_basis'],y['operating_scope'],y['unit'])]
        if len(pairs)==1:
            x,y=pairs[0];out.append(dict(start=num(x['value_numeric']),end=num(y['value_numeric']),va=[x],vb=[y],label='renewable_capacity_including_storage',method='source_definition_reviewed_cross_vintage_same_definition_nested_proxy',raw={'notes':'SSE renewable wholly-owned/JV scope differs from thermal segment plus 100% Marchwood PPA. Hydro/storage-inclusive proxy; not strict RE. Source-definition reviewed 2022–2024 comparison.'}))
    # Deduplicate repeated envelopes only when values, named boundary and source identities agree.
    uniq={}
    for r in out:
        key=(r['label'],r['start'],r['end'],join(x['record_id'] for x in r['va']+r['vb']))
        uniq[key]=r
    return list(uniq.values())

# Explicitly conservative boundary review. 'Strict' below means storage-exclusion documented
# in this extract; it is not a new certification of all plants or of an unchanged asset perimeter.
STRICT_GROUP_NOTES={
 'constellation_energy':'Source-derived same-ownership bridge removes 1058 MW Muddy Run pumped storage and 5 MW Clinton battery at both endpoints; nuclear excluded.',
 'nextera_energy':'Harmonized source vector excludes storage, nuclear and 75 MW non-incremental thermal solar at the opening endpoint.',
 'aes_corporation':'Source-reviewed equity renewable capacity explicitly excludes storage; biomass may remain source-defined renewable.',
 'dte_energy':'Separate source-derived RE metric removes pumped hydro; published rounding difference retained.',
 'jsw_energy':'Source notes identify operational Baspa II/Karcham hydro and exclude pumped-storage pipeline.',
 'ratch_group':'Source-reviewed operating fuel-category sum excludes BESS and pipeline; biomass remains source-defined renewable.',
 'colbun_s_a':'Source-reviewed operating RE explicitly excludes storage and uncommissioned Horizonte.',
}

def boundary(g,r):
    text=' '.join([r['label'],json.dumps(r['raw'])]+[o.get('metric','')+' '+o.get('technology','')+' '+o.get('operating_scope','')+' '+o.get('notes','') for o in r['va']+r['vb']]).lower()
    if r['label']=='reported_hydro_wind_solar_proxy':return 'broader_storage_inclusive_or_unresolved','Source-declared proxy: hydro storage unresolved; CHN solar-and-other is compound and can contain biomass. Not strict RE.'
    if r.get('partial'):return 'strict_component_only','Solar-only partial capacity, not a complete renewable total.'
    if r['raw'].get('renewable_measure')=='reported_owned_renewables_excluding_pumped_storage':return 'strict_storage_excluded','Source-defined owned renewables explicitly exclude pumped storage.'
    if g=='iberdrola':return 'broader_storage_inclusive_or_unresolved','Hydro includes pumping; Solar & Other is compound. EBITDA-consolidated RE only; no strict storage-free headline.'
    if 'reported_re_category' in r['label'] or ('including_pumped' in r['label'] or 'including_storage' in r['label']):return 'broader_storage_inclusive_or_unresolved','Source-reported hydro/storage-inclusive category; not strict storage-excluded RE.'
    if 'excluding_pumped_storage' in r['label'] or 'excluding_storage' in r['label'] or 'hydro_excluding_pumped' in r['label']:return 'strict_storage_excluded','Explicit source metric excludes pumped/storage.'
    if g in STRICT_GROUP_NOTES:return 'strict_storage_excluded',STRICT_GROUP_NOTES[g]
    if 'pumped' in text or 'tâmega' in text:return 'broader_storage_inclusive_or_unresolved','Pumped/storage boundary is included or unresolved in this same-window extract.'
    if 'wind' in r['label'] and 'hydro' not in r['label']:return 'strict_component_only','Wind component excludes storage but is not a complete RE total.'
    return 'reported_boundary_not_fully_verified','No affirmative whole-boundary storage-exclusion verification in the retained same-window evidence.'

# Event labels deliberately separate actual ownership exits, physical closure and operational cessation.
OWN={'ownership_disposal','ownership_sell_down','asset_sale','ownership_exit','ownership_share_dispatch_retirement','sale_and_deconsolidation','sale_partial_interest','ownership_sale','sale_with_retained_PPA','divestment_ownership_transfer','partial_equity_sale','ownership_disposal_and_deconsolidation','partnership_and_deconsolidation','BOT_contract_handback','concession_expiry'}
CLOSE={'physical_retirement','retirement_reported_in_fleet_transition_table','retirement','physical_closure','formal_decommissioning','physical_decommissioning','production_cessation_and_decommissioning','closure_after_reserve','retirement_after_long_suspension'}
CEASE={'retirement_and_mothballing','cessation_of_commercial_generation','coal_generation_cessation','taken_out_of_operation','taken_out_of_operation_partial_asset','shutdown_with_mothballing_qualification','withdrawal_from_service','reserve_transfer','reserve_status','reserve_or_out_of_operation','cold_reserve_status'}
ACQ={'ownership_acquisition','existing_asset_acquisition','acquisition_or_consolidation','acquisition_existing_asset','acquisition_or_operating_rights_existing_asset'}
ADD={'new_commissioning','addition','physical_commissioning','new_gas_commissioning','gas_capacity_addition','physical_installation_completion','commercial_operation_reached','commissioning_generation','uprating','modernisation_uprating'}
def event_family(t):
    if t in OWN:return 'ownership_exit_or_dispatch_right_exit'
    if t in CLOSE:return 'reported_physical_closure_or_retirement'
    if t in CEASE:return 'operational_cessation_or_reserve'
    if t in ACQ:return 'existing_asset_acquisition'
    if t in ADD:return 'commissioning_or_uprating'
    if 'plan' in t or 'pending' in t or 'construction_start'==t:return 'planned_pending_or_construction'
    if 'switch' in t or 'conversion' in t or 'repower' in t:return 'fuel_switch_or_conversion'
    if 'reactivat' in t or 'return' in t or 'demoth' in t:return 'reactivation_or_return'
    if t.startswith('no_') or t in {'gate','unknown_event_attribution','capacity_reduction_mechanism_unresolved'}:return 'coverage_or_unresolved_statement'
    return 'other_reported_event'

def event_rows(g,a,b,window_id):
    out=[]
    for ev in D['canonical_events.csv']:
        if ev['group_id']!=g:continue
        lo,hi=ev['date_lower'],ev['date_upper']
        if lo and hi and a<lo<=hi<=b:timing='wholly_within_opening_exclusive_interval'
        elif lo and hi and lo<=b and hi>a:timing='overlaps_window_date_uncertain'
        else:continue
        rr={k:ev[k] for k in ['event_record_id','group_id','issuer_label','asset','event_type_raw','event_type_canonical','event_date_raw','date_lower','date_upper','date_precision','capacity_raw','capacity_basis','source_url','source_locator','search_coverage','source_file','source_csv_row']}
        rr.update(selected_window_id=window_id,start_date=a,end_date=b,timing=timing,event_family=event_family(ev['event_type_canonical']),event_raw_json=ev['source_raw_json'])
        out.append(rr)
    return out

components=[]; provenance=[]; output=[]; events_out=[]; selection=[]
windows=defaultdict(list)
for w in D['longest_reviewed_window_display.csv']:windows[w['group_id']].append(w)
for g,ws in sorted(windows.items()):
    first=sorted(ws,key=rank)[0];a,b=first['start_date'],first['end_date']
    selected=[w for w in ws if (w['start_date'],w['end_date'])==(a,b)]
    wid=hashlib.sha256((g+'|'+a+'|'+b).encode()).hexdigest()[:20]
    for w in ws:selection.append(dict(group_id=g,reviewed_window_id=w['reviewed_window_id'],start_date=w['start_date'],end_date=w['end_date'],selected=str(w in selected),selector='duration_days_desc,end_date_desc,finance_precision_desc,source_path_and_id_lexical'))
    fs=[fossil(w) for w in selected]
    # Cross-category/scope vectors remain separate. ESB is intentionally not pooled.
    f=fs[0] if len(fs)==1 else None
    rs=renewable(first)
    # Deterministic boundary preference only, no endpoint magnitude/direction enters selection.
    rs=sorted(rs,key=lambda r:(0 if r['label']=='source_reviewed_renewable_capacity' else 1 if r['label']=='renewable_capacity' else 2,r['label'],r['method']))
    # Multiple distinct component windows (e.g., ESB wind and hydro) are not automatically summed.
    unique_boundaries={(r['label'],r['start'],r['end']) for r in rs}
    aggregate_rs=[r for r in rs if r['label'] not in ['renewable_capacity_wind','renewable_capacity_hydro_excluding_pumped'] and not r.get('partial')]
    broad=aggregate_rs[0] if aggregate_rs else (rs[0] if len(unique_boundaries)==1 else None)
    stricts=[r for r in aggregate_rs if boundary(g,r)[0]=='strict_storage_excluded']
    strict=stricts[0] if stricts else None
    # Source-reported inclusive alternate is kept separately without replacing corrected primary RE.
    proxy=next((r for r in rs if r['label']=='reported_RE_category_capacity' or 'reported_including_pumped' in r['label']),None)
    all_measures=[('fossil',r,i) for i,r in enumerate(fs)]+[('renewable',r,i) for i,r in enumerate(rs)]
    for family,r,i in all_measures:
        mid=wid+'_'+family+'_'+str(i)
        bc,bnote=boundary(g,r) if family=='renewable' else ('source_defined_fossil','Fuel-capable/source categories; no fuel-input apportionment or exhaustive asset census inferred.')
        components.append(dict(group_id=g,issuer_label=first['issuer_label'],selected_window_id=wid,measure_id=mid,measure_family=family,component_label=r['label'],start_date=a,end_date=b,start_mw=r['start'],end_mw=r['end'],delta_mw=delta(r['start'],r['end']),direction=direction(r['start'],r['end']),boundary_class=bc,boundary_note=bnote,calculation_method=r['method'],start_record_ids=join(x['record_id'] for x in r['va']),end_record_ids=join(x['record_id'] for x in r['vb']),source_urls=urls(x['source_url'] for x in r['va']+r['vb']),source_window_file=first['source_file'],measure_notes=join(r['raw'].get(k,'') for k in ['caveats','notes','capacity_basis','strict_RE_storage_exclusion_gate','missing_or_exclusion_reasons'])))
        for endpoint,v in [('start',r['va']),('end',r['vb'])]:
            for o in v:provenance.append(dict(group_id=g,selected_window_id=wid,measure_id=mid,endpoint=endpoint,selected_window_basis_adjudication=join(w['physical_basis'] for w in selected),**{k:o.get(k,'') for k in ['record_id','source_observation_id','metric','technology','value_raw','value_numeric','unit','date_label_raw','date_lower','date_upper','ownership_basis','operating_scope','source_url','source_locator','source_file','source_csv_row','notes']}))
    evs=event_rows(g,a,b,wid);events_out.extend(evs)
    actual=[e for e in evs if e['timing']=='wholly_within_opening_exclusive_interval' and e['event_family']!='coverage_or_unresolved_statement']
    classes=set(c for w in selected for c in w['finance_evidence_classes'].split(';') if c)
    ad=AD.get(g,{})
    f0,f1=(f['start'],f['end']) if f else (None,None)
    r0,r1=(broad['start'],broad['end']) if broad else (None,None)
    s0,s1=(strict['start'],strict['end']) if strict else (None,None)
    raw=j(first['source_raw_json'])
    caveats=join(raw.get(k,'') for k in ['caveats','notes','quality_flags','capacity_basis','capacity_comparability','missing_or_exclusion_reasons','strict_RE_storage_exclusion_gate','output_caution','limitations','scope'])
    row=dict(group_id=g,issuer_label=first['issuer_label'],selected_window_id=wid,reviewed_window_ids=join(w['reviewed_window_id'] for w in selected),start_date=a,end_date=b,duration_days=(date.fromisoformat(b)-date.fromisoformat(a)).days,group_unit='utility_group',admitted=ad.get('admitted',''),admission_status=ad.get('admission_status','not_provided_by_canonical_adjudication'),admission_basis=ad.get('admission_basis',''),integration_rq3_status=join(w['rq3_status'] for w in selected),gate_flags=join(w['gate_flags'] for w in selected),physical_basis=join(w['physical_basis'] for w in selected),fossil_start_mw=f0,fossil_end_mw=f1,fossil_delta_mw=delta(f0,f1),fossil_change_pct=pct(f0,f1),fossil_direction=direction(f0,f1),fossil_component_directions=join(direction(x['start'],x['end']) for x in fs),fossil_aggregation_note='Single reviewed source boundary' if f else 'Multiple scope/category rows retained separately; group total deliberately blank',renewable_start_mw=r0,renewable_end_mw=r1,renewable_delta_mw=delta(r0,r1),renewable_change_pct=pct(r0,r1),renewable_direction=direction(r0,r1),renewable_boundary=boundary(g,broad)[0] if broad else 'separate_components_or_missing_same_window_total',strict_RE_start_mw=s0,strict_RE_end_mw=s1,strict_RE_delta_mw=delta(s0,s1),strict_RE_direction=direction(s0,s1),reported_proxy_start_mw=proxy['start'] if proxy else None,reported_proxy_end_mw=proxy['end'] if proxy else None,reported_proxy_delta_mw=delta(proxy['start'],proxy['end']) if proxy else None,strict_boundary_note=boundary(g,strict)[1] if strict else 'Storage-exclusion confirmation absent or component-only; strict RE cells remain missing.',finance_evidence_classes=join(classes),finance_timing_tiers=join(w['finance_timing_tier'] for w in selected),finance_record_ids=join(x for w in selected for x in w['finance_record_ids'].split(';')),finance_admission_record_ids=join(x for w in selected for x in w.get('finance_admission_record_ids',w['finance_record_ids']).split(';')),reported_event_types_present=join(e['event_type_canonical'] for e in actual),reported_event_families_present=join(e['event_family'] for e in actual),ownership_exit_present='documented' if any(e['event_family']=='ownership_exit_or_dispatch_right_exit' for e in actual) else 'not_documented_in_bounded_extract',physical_closure_present='documented' if any(e['event_family']=='reported_physical_closure_or_retirement' for e in actual) else 'not_documented_in_bounded_extract',operational_cessation_or_reserve_present='documented' if any(e['event_family']=='operational_cessation_or_reserve' for e in actual) else 'not_documented_in_bounded_extract',event_search_caveat='Presence only, not an exhaustive event count or a zero-event finding. Asset-specific fuel/ownership status remains in event evidence.',source_window_files=join(w['source_file'] for w in selected),physical_source_urls=urls(o.get('source_url','') for _,r,_ in all_measures for o in r['va']+r['vb']),caveats=caveats)
    for c in FINANCE_CLASSES:row['has_'+c]=str(c in classes)
    boundary_review=BOUNDARY.get(g,{})
    row['fossil_boundary_class']=first.get('fossil_boundary_class') or boundary_review.get('fossil_boundary_class','source_identified_categories_pending_boundary_audit')
    row['fossil_boundary_caveat']=boundary_review.get('fossil_boundary_caveat',boundary_review.get('boundary_reason','Boundary-specific adjudication pending; do not describe as a verified whole-fleet strict fossil total.'))
    row['fossil_boundary_audit_status']=boundary_review.get('audit_status',boundary_review.get('evidence_tier','pending_boundary_specific_review'))
    row['analysis_evidence_tier']=first.get('analysis_evidence_tier') or first.get('evidence_tier') or boundary_review.get('evidence_tier','pending_boundary_specific_review')
    row['principal_analysis_include']=first.get('principal_analysis_include') or str(ad.get('admitted','').lower()=='true' and row['analysis_evidence_tier']=='principal_fuel_identified_scope')
    row['matched_proxy_extension_include']=first.get('matched_proxy_extension_include') or str(ad.get('admitted','').lower()=='true' and row['analysis_evidence_tier']=='matched_thermal_proxy_extension')
    row['broad_matched_include']=str(row['principal_analysis_include']=='True' or row['matched_proxy_extension_include']=='True')
    row['fuel_identified_sensitivity_eligible']=boundary_review.get('fuel_identified_sensitivity_eligible','unresolved')
    row['fossil_boundary_source_urls']=boundary_review.get('source_urls','')
    row['finance_label_sensitivity']='ICMA Green Bond Principles-aligned New Energy bonds; separate from literal Green Bond label sensitivity' if g=='clp' else 'Source-classified qualifying finance; retained record-level instrument labels control'
    row['company_dependence_note']='One selected window per group. All alternate/category/event rows are dependent evidence from that group; no independent-observation inflation.'
    output.append(row)

write('group_capacity_results.csv',output)
write('capacity_component_results.csv',components)
write('capacity_endpoint_provenance.csv',provenance)
write('selected_window_event_evidence.csv',events_out)
write('deterministic_window_selection.csv',selection)
finlong=[]
F={r['record_id']:r for r in D.get('canonical_finance.csv',[])}
for r in output:
    for fid in r['finance_admission_record_ids'].split(';'):
        if fid in F:
            finlong.append(dict(selected_window_id=r['selected_window_id'],selected_start_date=r['start_date'],selected_end_date=r['end_date'],**F[fid]))
write('selected_window_finance_evidence.csv',finlong)
# Contextual stock coverage is closed at the opening endpoint [start,end]. Admission and
# event/issuance timing remain separate and opening-exclusive. Never infer continuous balances.
contextual=[]
for r in output:
    admitted_records=[f for f in finlong if f['selected_window_id']==r['selected_window_id']]
    instruments={f['instrument_or_pool_id'] for f in admitted_records if f['instrument_or_pool_id']}
    source_opening_ids=set()
    for w in windows[r['group_id']]:
        raw=j(w['source_raw_json'])
        for key in ['finance_start_observation_ids','finance_earliest_observation_ids']:
            source_opening_ids.update(o['record_id'] for o in obs_ids(raw.get(key,'')))
    admitted_ids={f['record_id'] for f in admitted_records}
    canonical_context=[F[fid] for fid in r['finance_record_ids'].split(';') if fid in F]
    ids={f['record_id'] for f in admitted_records+canonical_context}
    for f in admitted_records:contextual.append(dict(f,evidence_role='admission_linked_finance_evidence'))
    for f in canonical_context:
        if f['record_id'] not in admitted_ids:contextual.append(dict(selected_window_id=r['selected_window_id'],selected_start_date=r['start_date'],selected_end_date=r['end_date'],**f,evidence_role='canonical_context_inclusive_finance_evidence_not_new_admission'))
    for f in F.values():
        if f['group_id']!=r['group_id'] or f['record_id'] in ids:continue
        if f['measure_class'] not in ['cumulative_allocated_stock','outstanding_identified_bond_liability']:continue
        if f['date_lower']!=r['start_date'] or f['date_upper']!=r['start_date']:continue
        if not ((f['instrument_or_pool_id'] and f['instrument_or_pool_id'] in instruments) or f['record_id'] in source_opening_ids):continue
        contextual.append(dict(selected_window_id=r['selected_window_id'],selected_start_date=r['start_date'],selected_end_date=r['end_date'],**f,evidence_role='matching_opening_stock_context_not_new_admission'))
    r['contextual_finance_record_ids']=join(f['record_id'] for f in contextual if f['selected_window_id']==r['selected_window_id'])
write('contextual_window_finance_evidence.csv',contextual)
# Financing-time coverage describes the first retained qualifying observation, not financing inception.
coverage=[]
for r in output:
    ff=[f for f in contextual if f['selected_window_id']==r['selected_window_id'] and f.get('date_lower') and f.get('date_upper') and f['date_lower']<=r['end_date'] and f['date_upper']>=r['start_date']]
    lower=min((f['date_lower'] for f in ff),default='');upper=min((f['date_upper'] for f in ff),default='')
    start=date.fromisoformat(r['start_date']);duration=r['duration_days']
    lo=max(0,min(duration,(date.fromisoformat(lower)-start).days)) if lower else None
    hi=max(0,min(duration,(date.fromisoformat(upper)-start).days)) if upper else None
    earliest=[f for f in ff if f['date_lower']==lower or f['date_upper']==upper]
    r.update(first_retained_finance_observation_lower=lower,first_retained_finance_observation_upper=upper,antecedent_days_lower=lo,antecedent_days_upper=hi,antecedent_fraction_lower=lo/duration if lo is not None else None,antecedent_fraction_upper=hi/duration if hi is not None else None)
    coverage.append({k:r[k] for k in ['group_id','issuer_label','selected_window_id','start_date','end_date','duration_days','first_retained_finance_observation_lower','first_retained_finance_observation_upper','antecedent_days_lower','antecedent_days_upper','antecedent_fraction_lower','antecedent_fraction_upper']}|dict(first_observation_record_ids=join(f['record_id'] for f in earliest),first_observation_evidence_roles=join(f['evidence_role'] for f in earliest),first_observation_classes=join(f['measure_class'] for f in earliest),first_observation_precision=join(f['date_precision'] for f in earliest),source_urls=urls(f['source_url'] for f in earliest),interpretation='First retained finance evidence including matching opening stocks on [start,end], not earliest-ever financing or issue inception. Antecedent interval is descriptive coverage only; the entire capacity delta is not a post-financing outcome. Bounds are capped at physical interval.'))
write('finance_timing_coverage.csv',coverage)
write('group_capacity_results.csv',output)
# Strict source/scope adjacent capacity matches with qualifying finance evidence, plus timing tier.
links=defaultdict(list)
for l in D.get('window_finance_links.csv',[]):links[l['candidate_window_id']].append(l)
aligned=[]
for w in D.get('canonical_candidate_windows.csv',[]):
    ls=links.get(w['candidate_window_id'],[])
    if not ls:continue
    aligned.append(dict(w,finance_linked_record_ids=join(l['finance_record_id'] for l in ls),finance_linked_classes=join(l['measure_class'] for l in ls),finance_alignment_tiers=join(l['date_alignment'] for l in ls),company_dependence='Category and overlapping adjacent windows within same utility group; not independent observations',temporal_interpretation='Finance observed within/at stated interval bounds; does not establish finance active throughout or causal timing.'))
write('finance_aligned_adjacent_robustness.csv',aligned)

# Boundary alternatives are reported separately and do not imply an automatic strict total.
sensitivity=[]
for r in output:
    g,a,b=r['group_id'],r['start_date'],r['end_date']
    if g=='iberdrola':
        original=[e for e in E if e['group_id']==g and e['dates']==(a,b) and e['raw'].get('metric_family')=='fossil_capacity']
        for e in original[:1]:
            va=vector(e['raw'].get('earliest_values_json',''));vb=vector(e['raw'].get('latest_values_json',''));x,_=sum_vector(va);y,_=sum_vector(vb)
            if x is not None and y is not None:sensitivity.append(dict(group_id=g,boundary='original_cogeneration_inclusive_fossil_sensitivity',start_date=a,end_date=b,start_mw=x,end_mw=y,delta_mw=delta(x,y),direction=direction(x,y),strict_total_RE='not_applicable',caveat='Original EBITDA-consolidated coal+CCGT+unsplit cogeneration vector retained separately. Principal fuel-defined subset excludes fuel-unspecified cogeneration; neither is a whole-fleet census.',record_ids=join(o['record_id'] for o in va+vb)))
    if g=='ontario_power_generation':
        p=metric_pair(g,a,b,'renewable_capacity_excluding_biomass')
        if p:sensitivity.append(dict(group_id=g,boundary='hydro_solar_excluding_biomass',start_date=a,end_date=b,start_mw=p['start'],end_mw=p['end'],delta_mw=delta(p['start'],p['end']),direction=direction(p['start'],p['end']),strict_total_RE='False',caveat='Biomass excluded sensitivity; storage exclusion has not been fully verified. Compare with source-defined renewable portfolio including biomass.',record_ids=join(o['record_id'] for o in p['va']+p['vb'])))
    if g=='enbw' and r['renewable_start_mw'] is not None:
        # Same source, ownership and scope are required before this nested-category subtraction.
        source_rows=[c for c in components if c['group_id']==g and c['measure_family']=='renewable']
        for sr in source_rows[:1]:
            av=obs_ids(sr['start_record_ids']);bv=obs_ids(sr['end_record_ids'])
            pairs=[]
            for v,dt in [(av,a),(bv,b)]:
                roots=v
                matches=[o for o in BY[g] if o['metric']=='capacity_pumped_storage_no_natural_inflow' and o['date_upper']==dt and any((o['source_url'],o['ownership_basis'],o['operating_scope'])==(x['source_url'],x['ownership_basis'],x['operating_scope']) for x in roots)]
                pairs.append(matches[0] if len(matches)==1 else None)
            if all(pairs):
                x=r['renewable_start_mw']-num(pairs[0]['value_numeric']);y=r['renewable_end_mw']-num(pairs[1]['value_numeric'])
                sensitivity.append(dict(group_id=g,boundary='reported_RE_minus_pumped_without_natural_inflow',start_date=a,end_date=b,start_mw=x,end_mw=y,delta_mw=delta(x,y),direction=direction(x,y),strict_total_RE='not_certified',caveat='Subtracts explicitly nested pumped-storage-without-natural-inflow cells. Does not certify that every remaining mixed hydro category is storage-free.',record_ids=join(o['record_id'] for o in av+bv+pairs)))
write('additional_boundary_sensitivities.csv',sensitivity)

# One row per group and boundary for plotting; missing measures remain blank.
plots=[]
for r in output:
    for boundary_,x,y in [('reported_source_boundary',r['renewable_delta_mw'],r['fossil_delta_mw']),('strict_storage_excluded_subset',r['strict_RE_delta_mw'],r['fossil_delta_mw'])]:
        plots.append({k:r[k] for k in ['group_id','issuer_label','selected_window_id','start_date','end_date','duration_days','admitted','admission_status','analysis_evidence_tier','principal_analysis_include','matched_proxy_extension_include','broad_matched_include','finance_evidence_classes','renewable_boundary','fossil_boundary_class','fuel_identified_sensitivity_eligible','fossil_boundary_caveat','physical_basis','physical_source_urls']}|dict(boundary=boundary_,renewable_delta_mw=x,fossil_delta_mw=y,paired_values_available=str(x is not None and y is not None),plot_interpretation='Unweighted group-level endpoint change; heterogeneous reporting bases and durations, no pooled MW total or annualization'))
# Clean wind + solar sensitivity requires actual components at both exact endpoints.
# Never substitute Solar & Other, an absent component, or another ownership/scope.
def clean_component(o):
    label=(o['technology'] or o['metric']).lower().replace(' ','_')
    if label in {'wind','wind_capacity','capacity_wind','capacity_wind_mw'}:return 'wind_total'
    if label in {'onshore_wind','capacity_onshore_wind_mw'}:return 'wind_onshore'
    if label in {'offshore_wind','capacity_offshore_wind_mw'}:return 'wind_offshore'
    if label in {'solar','solar_pv','solar_capacity','capacity_solar','capacity_solar_pv_mw'}:return 'solar'
    return ''
windsolar=[]
for r in output:
    g=r['group_id'];variants=[]
    for ep,dt in [('start',r['start_date']),('end',r['end_date'])]:
        allowed={p['source_url'] for p in provenance if p['group_id']==g and p['endpoint']==ep}
        buckets=defaultdict(list)
        for o in BY[g]:
            if o['record_kind']=='physical_capacity' and o['date_upper']==dt and o['unit'] in ['MW','GW'] and clean_component(o) and num(o['value_numeric']) is not None and (not allowed or o['source_url'] in allowed):
                buckets[(o['ownership_basis'],o['operating_scope'],o['source_url'])].append(o)
        good=[]
        for key,oo in buckets.items():
            cats=defaultdict(list)
            for o in oo:cats[clean_component(o)].append(o)
            if len(cats['solar'])!=1:continue
            if len(cats['wind_total'])==1:wind=cats['wind_total']
            elif len(cats['wind_onshore'])==len(cats['wind_offshore'])==1:wind=cats['wind_onshore']+cats['wind_offshore']
            else:continue
            vv=wind+cats['solar'];good.append((key,vv))
        variants.append(good)
    pairs=[(x,y) for x in variants[0] for y in variants[1] if x[0][:2]==y[0][:2]]
    reason='No same-window exact-scope/basis actual wind and solar components at both endpoints.'
    if g=='nextera_energy' and any('nonincremental' in str(x).lower() or 'non-incremental' in str(x).lower() for x in [r['caveats']]):
        pairs=[];reason='Non-incremental thermal solar in reported component requires a separate clean component bridge; no unverified correction applied here.'
    # Conflicting in-scope source alternatives remain unresolved rather than chosen on outcome.
    vals={(sum(num(o['value_numeric'])*(1000 if o['unit']=='GW' else 1) for o in x[1]),sum(num(o['value_numeric'])*(1000 if o['unit']=='GW' else 1) for o in y[1])) for x,y in pairs}
    if len(vals)==1:
        x,y=sorted(pairs,key=lambda z:(z[0][0],z[1][0]))[0];v0,v1=next(iter(vals));ev=x[1]+y[1]
        wr=dict(group_id=g,issuer_label=r['issuer_label'],selected_window_id=r['selected_window_id'],admitted=r['admitted'],start_date=r['start_date'],end_date=r['end_date'],available='True',wind_solar_start_mw=v0,wind_solar_end_mw=v1,wind_solar_delta_mw=delta(v0,v1),wind_solar_direction=direction(v0,v1),ownership_basis=x[0][0],operating_scope=x[0][1],start_record_ids=join(o['record_id'] for o in x[1]),end_record_ids=join(o['record_id'] for o in y[1]),source_urls=urls(o['source_url'] for o in ev),caveat='Clean partial wind + solar sensitivity only; no total-RE interpretation. Both components are actual and separately reported; matching source-definition reviewed window, same literal ownership and scope.')
        plots.append({k:r[k] for k in ['group_id','issuer_label','selected_window_id','start_date','end_date','duration_days','admitted','admission_status','analysis_evidence_tier','principal_analysis_include','matched_proxy_extension_include','broad_matched_include','finance_evidence_classes','renewable_boundary','fossil_boundary_class','fuel_identified_sensitivity_eligible','fossil_boundary_caveat','physical_basis','physical_source_urls']}|dict(boundary='clean_wind_solar_partial',renewable_delta_mw=wr['wind_solar_delta_mw'],fossil_delta_mw=r['fossil_delta_mw'],paired_values_available=str(r['fossil_delta_mw'] is not None),plot_interpretation=wr['caveat']))
    else:wr=dict(group_id=g,issuer_label=r['issuer_label'],selected_window_id=r['selected_window_id'],admitted=r['admitted'],start_date=r['start_date'],end_date=r['end_date'],available='False',wind_solar_start_mw=None,wind_solar_end_mw=None,wind_solar_delta_mw=None,wind_solar_direction='unresolved',caveat=reason if not vals else 'Multiple conflicting exact-scope source alternatives; no outcome-based choice.')
    wr.update({k:r[k] for k in ['analysis_evidence_tier','principal_analysis_include','matched_proxy_extension_include','broad_matched_include']})
    windsolar.append(wr)
write('clean_wind_solar_sensitivity.csv',windsolar)
write('clean_wind_solar_coverage_summary.csv',[dict(selected_group_rows=len(output),actual_component_coverage_groups=sum(x['available']=='True' for x in windsolar),component_and_fossil_pair_groups=sum(x['available']=='True' and next(r for r in output if r['group_id']==x['group_id'])['fossil_delta_mw'] is not None for x in windsolar),covered_group_ids=join(x['group_id'] for x in windsolar if x['available']=='True'),caveat='Observed two-component coverage, not a cohort-admission or total-RE denominator. No absent=zero, compound Solar & Other, or cross-scope mixing.')])
write('capacity_scatter_plot_data.csv',plots)

# Adjacent candidates are a robustness ledger, not additional independent groups or generic totals.
rob=[]
for w in D['reviewed_regional_window_panel.csv']:
    if w.get('adjacent_annual','').lower()!='true':continue
    r=fossil(w)
    rob.append(dict(group_id=w['group_id'],issuer_label=w['issuer_label'],reviewed_window_id=w['reviewed_window_id'],start_date=w['start_date'],end_date=w['end_date'],metric_family=w['metric_family'],physical_basis=w['physical_basis'],start_mw=r['start'],end_mw=r['end'],delta_mw=delta(r['start'],r['end']),direction=direction(r['start'],r['end']),finance_evidence_classes=w['finance_evidence_classes'],integration_status=w['rq3_status'],gate_flags=w['gate_flags'],source_file=w['source_file'],company_dependence='Repeated or overlapping observations within utility group; not independent cases'))
write('reviewed_adjacent_window_robustness.csv',rob)
# Automatic adjacent matches remain category-level, never unreviewed whole-fleet values.
auto=[]
for r in D.get('canonical_candidate_windows.csv',[]):
    auto.append(r)
write('automatic_adjacent_category_robustness.csv',auto)
# Descriptive summaries condition on canonical eligibility when supplied. Not population prevalence.
summaries=[];finance=[];event_summary=[]
cohorts={'all_selected_source_defined_groups':output}
if any(str(r['admitted']).lower()=='true' for r in output):
    cohorts['eligible_broad_matched']=[r for r in output if str(r['admitted']).lower()=='true']
    cohorts['principal_fuel_identified_groups']=[r for r in output if r['principal_analysis_include']=='True']
    cohorts['matched_thermal_proxy_extension']=[r for r in output if r['matched_proxy_extension_include']=='True']
    cohorts['broad_matched_groups']=[r for r in output if r['broad_matched_include']=='True']
    if any(r['group_id']=='clp' for r in cohorts['eligible_broad_matched']):
        cohorts['eligible_broad_matched_excluding_CLP_New_Energy_label_case']=[r for r in cohorts['eligible_broad_matched'] if r['group_id']!='clp']
        cohorts['principal_excluding_CLP_New_Energy_label_case']=[r for r in cohorts['principal_fuel_identified_groups'] if r['group_id']!='clp']
write('clean_wind_solar_tier_coverage_summary.csv',[dict(cohort=cohort,group_rows=len(rr),actual_component_coverage_groups=sum(x['available']=='True' and x['group_id'] in {r['group_id'] for r in rr} for x in windsolar),actual_component_and_fossil_scalar_pair_groups=sum(x['available']=='True' and x['group_id'] in {r['group_id'] for r in rr if r['fossil_delta_mw'] is not None} for x in windsolar),covered_group_ids=join(x['group_id'] for x in windsolar if x['available']=='True' and x['group_id'] in {r['group_id'] for r in rr}),interpretation='Partial wind plus separately reported solar only; no compound Solar & Other or zero imputation.') for cohort,rr in cohorts.items()])
for cohort,rr in cohorts.items():
    for measure,field in [('source_defined_fossil','fossil_delta_mw'),('source_defined_RE','renewable_delta_mw'),('strict_storage_excluded_RE','strict_RE_delta_mw')]:
        valid=[r for r in rr if r[field] is not None];vals=[r[field] for r in valid]
        summaries.append(dict(cohort=cohort,measure=measure,group_rows=len(rr),observed_group_rows=len(valid),missing_group_rows=len(rr)-len(valid),increase_groups=sum(v>1e-8 for v in vals),decrease_groups=sum(v < -1e-8 for v in vals),unchanged_groups=sum(abs(v)<=1e-8 for v in vals),group_ids=join(r['group_id'] for r in valid),interpretation='Describes retained group labels only. Mixed scope/duration; no inference, population prevalence, causal effect, or pooled capacity total.'))
    for c in FINANCE_CLASSES:
        groups=[r for r in rr if r['has_'+c]=='True']
        finance.append(dict(cohort=cohort,finance_class=c,group_rows_with_class=len(groups),group_ids=join(r['group_id'] for r in groups),groups_with_fossil_increase=join(r['group_id'] for r in groups if r['fossil_direction']=='increase'),groups_with_fossil_decrease=join(r['group_id'] for r in groups if r['fossil_direction']=='decrease'),groups_with_fossil_unchanged=join(r['group_id'] for r in groups if r['fossil_direction']=='unchanged_at_reported_precision'),caveat='Classes overlap. One group may appear in multiple classes. No amount summation; stock, flow, liability and currencies remain separate.'))
    for family in sorted({e['event_family'] for e in events_out if e['event_family']!='coverage_or_unresolved_statement'}):
        groups=[r for r in rr if family in r['reported_event_families_present'].split(';')]
        event_summary.append(dict(cohort=cohort,event_family=family,groups_with_documented_presence=len(groups),group_ids=join(r['group_id'] for r in groups),caveat='Group-level documented presence only; other groups have unknown/nonexhaustively searched presence, not observed zeros. Event records are not independent asset counts.'))
write('descriptive_capacity_summary.csv',summaries)
write('finance_class_breakdown.csv',finance)
write('event_type_presence_summary.csv',event_summary)
presence=[]
for r in output:
    for t in filter(None,r['reported_event_types_present'].split(';')):
        evidence=[e for e in events_out if e['group_id']==r['group_id'] and e['event_type_canonical']==t and e['timing']=='wholly_within_opening_exclusive_interval']
        presence.append(dict(group_id=r['group_id'],issuer_label=r['issuer_label'],selected_window_id=r['selected_window_id'],admitted=r['admitted'],event_type=t,presence='documented',event_family=event_family(t),supporting_event_record_ids=join(e['event_record_id'] for e in evidence),source_urls=urls(e['source_url'] for e in evidence),interpretation='Presence in bounded extract only; rows are not exhaustive event counts.'))
write('event_type_presence_by_group.csv',presence)

quadrants=[]
for cohort,rr in cohorts.items():
    for label,field in [('reported_source_boundary','renewable_delta_mw'),('strict_storage_excluded_subset','strict_RE_delta_mw')]:
        groups=defaultdict(list)
        for r in rr:
            if r[field] is None or r['fossil_delta_mw'] is None: key=('unresolved_pair','unresolved_pair')
            else:key=(direction(0,r[field]),r['fossil_direction'])
            groups[key].append(r['group_id'])
        for (rd,fd),gs in sorted(groups.items()):quadrants.append(dict(cohort=cohort,boundary=label,RE_direction=rd,fossil_direction=fd,group_rows=len(gs),group_ids=join(gs),caveat='Descriptive selected-group directions at source precision; no population prevalence or causal interpretation.'))
for cohort,rr in cohorts.items():
    gids={r['group_id'] for r in rr};cells=defaultdict(list)
    for ws in windsolar:
        if ws['group_id'] not in gids:continue
        r=next(r for r in rr if r['group_id']==ws['group_id'])
        key=(ws['wind_solar_direction'],r['fossil_direction']) if ws['available']=='True' and r['fossil_delta_mw'] is not None else ('unresolved_pair','unresolved_pair')
        cells[key].append(ws['group_id'])
    for (rd,fd),gs in sorted(cells.items()):quadrants.append(dict(cohort=cohort,boundary='clean_wind_solar_partial',RE_direction=rd,fossil_direction=fd,group_rows=len(gs),group_ids=join(gs),caveat='Partial wind + solar, actual two-component coverage only; not total RE, population prevalence or causal inference.'))
write('capacity_direction_pair_summary.csv',quadrants)
# Retrospectively declared numerical sign bands, not preregistered or inferential thresholds.
def band_sign(opening,change,band):
    if opening is None or change is None:return 'unresolved'
    if opening==0 and band>0:return 'undefined_relative_band_zero_baseline'
    threshold=abs(opening)*band/100
    return 'within_declared_band' if abs(change)<=threshold+1e-8 else ('increase' if change>0 else 'decrease')
bands=[];band_summaries=[]
for r in output:
    for band in [0,0.5,1]:
        for label,startfield,deltafield in [('reported_source_boundary','renewable_start_mw','renewable_delta_mw'),('strict_storage_excluded_subset','strict_RE_start_mw','strict_RE_delta_mw')]:
            bands.append(dict(group_id=r['group_id'],issuer_label=r['issuer_label'],admitted=r['admitted'],boundary=label,band_pct_of_opening_capacity=band,RE_opening_mw=r[startfield],RE_delta_mw=r[deltafield],RE_direction_at_band=band_sign(r[startfield],r[deltafield],band),fossil_opening_mw=r['fossil_start_mw'],fossil_delta_mw=r['fossil_delta_mw'],fossil_direction_at_band=band_sign(r['fossil_start_mw'],r['fossil_delta_mw'],band),declaration='Retrospective descriptive sensitivity: abs(change) <= band% of opening capacity is within band. Zero band means unchanged at source precision; not a preregistered threshold or statistical test.'))
write('group_sign_band_sensitivity.csv',bands)
for cohort,rr in cohorts.items():
    gids={r['group_id'] for r in rr}
    for band in [0,0.5,1]:
        for label in ['reported_source_boundary','strict_storage_excluded_subset']:
            cells=defaultdict(list)
            for x in bands:
                if x['group_id'] in gids and x['band_pct_of_opening_capacity']==band and x['boundary']==label:cells[(x['RE_direction_at_band'],x['fossil_direction_at_band'])].append(x['group_id'])
            for (rd,fd),gs in sorted(cells.items()):band_summaries.append(dict(cohort=cohort,boundary=label,band_pct_of_opening_capacity=band,RE_direction=rd,fossil_direction=fd,group_rows=len(gs),group_ids=join(gs),declaration='Retrospectively declared sign-band description; no p-values, population prevalence, or causal inference.'))
write('sign_band_direction_summary.csv',band_summaries)
loo=[]
for cohort,rr in cohorts.items():
    for omitted in rr:
        kept=[r for r in rr if r['group_id']!=omitted['group_id']]
        for label,field in [('reported_source_boundary','renewable_delta_mw'),('strict_storage_excluded_subset','strict_RE_delta_mw')]:
            valid=[r for r in kept if r[field] is not None and r['fossil_delta_mw'] is not None]
            counts=Counter((direction(0,r[field]),r['fossil_direction']) for r in valid)
            row=dict(cohort=cohort,omitted_group_id=omitted['group_id'],boundary=label,remaining_group_rows=len(kept),remaining_complete_pairs=len(valid),remaining_incomplete_pairs=len(kept)-len(valid))
            for rd in ['increase','decrease','unchanged_at_reported_precision']:
                for fd in ['increase','decrease','unchanged_at_reported_precision']:row['RE_'+rd+'__fossil_'+fd]=counts[(rd,fd)]
            row['interpretation']='Leave-one-utility-group-out descriptive count sensitivity at zero band. Dependent windows/categories/events removed together. No jackknife variance, uncertainty interval, or significance inference.'
            loo.append(row)
write('leave_one_group_out_descriptive_counts.csv',loo)
# Compact presentation tables carry exact provenance through the selected window identifier.
write('table_capacity_window_summary.csv',[{k:r[k] for k in ['group_id','issuer_label','selected_window_id','admitted','admission_status','analysis_evidence_tier','principal_analysis_include','matched_proxy_extension_include','broad_matched_include','start_date','end_date','duration_days','fossil_start_mw','fossil_end_mw','fossil_delta_mw','fossil_direction','renewable_start_mw','renewable_end_mw','renewable_delta_mw','renewable_direction','renewable_boundary','strict_RE_delta_mw','fossil_boundary_class','fuel_identified_sensitivity_eligible','fossil_boundary_caveat','physical_basis','finance_evidence_classes','finance_label_sensitivity','physical_source_urls']} for r in output])
write('table_finance_event_presence.csv',[{k:r[k] for k in ['group_id','issuer_label','selected_window_id','admitted','finance_evidence_classes','finance_timing_tiers','first_retained_finance_observation_lower','first_retained_finance_observation_upper','antecedent_fraction_lower','antecedent_fraction_upper','ownership_exit_present','physical_closure_present','operational_cessation_or_reserve_present','reported_event_types_present']} for r in output])


qa={'unique_group_row_check':len(output)==len({r['group_id'] for r in output}),'selected_group_rows':len(output),'group_rows_eligible_broad_matched':sum(str(r['admitted']).lower()=='true' for r in output),'principal_group_rows':sum(r['principal_analysis_include']=='True' for r in output),'matched_proxy_extension_group_rows':sum(r['matched_proxy_extension_include']=='True' for r in output),'broad_matched_group_rows':sum(r['broad_matched_include']=='True' for r in output),'canonical_admission_status_is_not_recomputed':True,'missing_fossil_aggregate_groups':[r['group_id'] for r in output if r['fossil_delta_mw'] is None],'missing_same_window_RE_aggregate_groups':[r['group_id'] for r in output if r['renewable_delta_mw'] is None],'strict_storage_exclusion_confirmed_groups':[r['group_id'] for r in output if r['strict_RE_delta_mw'] is not None],'source_reported_RE_only_groups':[r['group_id'] for r in output if r['renewable_delta_mw'] is not None and r['strict_RE_delta_mw'] is None],'fuel_identified_sensitivity_group_rows':sum(r['fuel_identified_sensitivity_eligible'].lower()=='true' for r in output),'boundary_audit_missing_groups':[r['group_id'] for r in output if r['fossil_boundary_audit_status']=='pending_boundary_specific_review'],'no_inferential_statistics':True,'no_zero_filling':True,'no_capacity_generation_substitution':True,'no_cross_group_MW_sum':True,'no_independent_count_of_components_events_or_robustness_windows':True,'input_changes_during_build':[f for f,b in blobs.items() if (P/f).read_bytes()!=b]}
(HERE/'results_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':{f:hashlib.sha256(b).hexdigest() for f,b in blobs.items()},'output_files':sorted(x.name for x in HERE.glob('*.csv')),'output_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(HERE.glob('*.csv'))},'boundary_review_sha256':hashlib.sha256(BLOB).hexdigest() if BLOB else None,'admission_authority':'audited candidate_adjudication_queue.csv; absent/false/pending admissions are never converted to accepted by this script'}
(HERE/'results_build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(qa,indent=2))
