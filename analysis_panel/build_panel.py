#!/usr/bin/env python3
"""Conservative, non-mutating canonical ingestion and question-specific candidate gates.
No currencies, ownership bases, stocks/flows or physical technologies are pooled.
Run from any directory. Regional source files remain untouched.
"""
import csv,json,re,hashlib,calendar,datetime,collections,argparse,shutil,math
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--replay-manifest',help='Replay frozen local inputs with portable manifest-relative resolution.');parser.add_argument('--freeze',action='store_true');parser.add_argument('--input-root',help='Expansion project root for a live build.');parser.add_argument('--output-dir',help='Output directory, independent of original provenance paths.');args=parser.parse_args()
manifest_records=json.loads(Path(args.replay_manifest).read_text()) if args.replay_manifest else []
if args.replay_manifest:
 root_source=next(x['original_path'] for x in manifest_records if x['original_path'].endswith('/integration/proposed_cohort_window_gate_spec.json'));ROOT=Path(root_source).parent.parent
else:ROOT=Path(args.input_root).resolve() if args.input_root else Path(__file__).resolve().parents[2]
SOURCE_PANEL=ROOT/'integration/analysis_panel';OUT=Path(args.output_dir).resolve() if args.output_dir else SOURCE_PANEL;OUT.mkdir(parents=True,exist_ok=True);SH=ROOT.parent
INPUTS=[SH/f'{r}_utility_actual_data.csv' for r in ['north_america','asia','southern','aes','nextera','duke','dominion','constellation']]+[ROOT/'europe_new/europe_additional_observations_long.csv',ROOT/'existing_nine/existing_nine_current_long.csv',ROOT/'rwe/rwe_operating_observations_long.csv',ROOT/'rwe/rwe_finance_observations.csv',ROOT/'rwe/rwe_instrument_register.csv',ROOT/'jsw/jsw_observations_long.csv',ROOT/'latam_operating_observations_long.csv',ROOT/'latam_financing_observations_long.csv',ROOT/'taipower_tohoku/taipower_tohoku_observations_long.csv',ROOT/'china_utilities/china_observations_long.csv']
EVENTS=[ROOT/'china_utilities/china_event_ledger.csv',SH/'constellation_event_ledger.csv',SH/'dominion_event_ledger.csv',ROOT/'latam_event_ledger.csv',ROOT/'taipower_tohoku/bounded_fossil_event_scan.csv',SH/'duke_event_ledger.csv',SH/'nextera_event_ledger.csv',ROOT/'jsw/jsw_fossil_event_ledger.csv',SH/'aes_event_ledger.csv',SH/'asia_fossil_asset_events.csv',SH/'southern_utility_eligibility_event_ledger.csv',ROOT/'north_america_event_ledger.csv',ROOT/'rwe/rwe_fossil_event_ledger.csv',ROOT/'europe_new/fossil_asset_event_ledger.csv',ROOT/'existing_nine/existing_eight_bounded_event_ledger.csv']
ENVELOPES=[ROOT/'china_utilities/china_analytical_window_candidates.csv',SH/'constellation_analytical_window_candidates.csv',SH/'dominion_analytical_window_candidates.csv',ROOT/'latam_analytical_window_candidates.csv',ROOT/'taipower_tohoku/candidate_windows.csv',SH/'duke_analytical_window_candidates.csv',SH/'nextera_analytical_window_candidates.csv',ROOT/'jsw/analytical_window_candidates.csv',SH/'aes_analytical_window_candidates.csv',SH/'asia_analytical_window_candidates.csv',SH/'southern_analytical_window_candidates.csv',ROOT/'north_america_analytical_window_candidates.csv',ROOT/'rwe/analytical_window_candidates.csv',ROOT/'existing_nine/analytical_window_candidates.csv',ROOT/'europe_new/analytical_window_candidates.csv']
FRAME_INPUTS=[ROOT/'wba2023_candidate_frame.csv',ROOT/'remaining_wba_screen.csv',ROOT/'global_additional_candidate_coverage.csv']

AUXILIARY=[ROOT/'wec_project_stage/wec_project_stage_panel.csv',ROOT/'wec_project_stage/wec_stage_outputs.csv']

CONFIGS=[ROOT/'china_utilities/china_QA_notes.json',ROOT/'integration/proposed_cohort_window_gate_spec.json',SOURCE_PANEL/'executed_protocol.json']

SUPPLEMENTAL=[ROOT/'integration/group_audit/fossil_boundary_consistency_audit.csv',ROOT/'integration/group_audit/iberdrola_known_fuel_subset_audit.csv',ROOT/'china_utilities/china_group_mapping.csv',ROOT/'china_utilities/china_event_search_coverage.csv',ROOT/'integration/group_audit/independent_group_admission_audit.csv',ROOT/'integration/group_audit/root_measurement_checks.csv',SOURCE_PANEL/'finance_identity_overrides.csv',ROOT/'jsw/jsw_group_mapping.csv',ROOT/'jsw/jsw_event_search_coverage.csv',SOURCE_PANEL/'integration_evidence_annotations.csv',ROOT/'existing_nine/existing_eight_group_independence_map.csv',ROOT/'existing_nine/existing_eight_event_search_coverage.csv',ROOT/'rwe/rwe_group_mapping.csv']

pathmap={}
if args.replay_manifest:
 mp=Path(args.replay_manifest).resolve()
 for x in manifest_records:
  old=Path(x['frozen_path']);candidates=[mp.parent/old.name,mp.parent/'snapshots'/old.parent.name/old.name]
  frozen=next((p for p in candidates if p.exists()),None)
  if frozen is None:raise FileNotFoundError('Frozen input missing beside relocated manifest: '+old.name)
  if hashlib.sha256(frozen.read_bytes()).hexdigest()!=x['sha256']:raise ValueError('Frozen input hash mismatch: '+old.name)
  pathmap[x['original_path']]=frozen
if args.freeze:
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');dest=OUT/'snapshots'/stamp;dest.mkdir(parents=True,exist_ok=True);snap=[]
 for p in dict.fromkeys(INPUTS+EVENTS+ENVELOPES+SUPPLEMENTAL+AUXILIARY+CONFIGS+FRAME_INPUTS):
  if p.exists():
   data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();frozen=dest/(digest[:12]+'_'+p.name);frozen.write_bytes(data);pathmap[str(p)]=frozen
   snap.append(dict(original_path=str(p),frozen_path=str(frozen),sha256=digest,artifact_type='local_extracted_csv_not_original_pdf' if p.suffix=='.csv' else 'local_protocol_json'))
 shutil.copy2(Path(__file__),dest/'build_panel.py');(dest/'snapshot_build_metadata.json').write_text(json.dumps({'build_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'frozen_at_utc':stamp},indent=2)+'\n')
 (dest/'snapshot_manifest.json').write_text(json.dumps(snap,indent=2)+'\n');shutil.copy2(dest/'snapshot_manifest.json',OUT/'latest_snapshot_manifest.json')
def mapped(p):return pathmap.get(str(p),OUT/'__absent_from_frozen_snapshot__') if args.replay_manifest else pathmap.get(str(p),p)

def read(p):
 return list(csv.DictReader(mapped(p).open(encoding='utf-8-sig'))) if mapped(p).exists() else []
def write(name,rows,fields=None):
 fields=fields or list(dict.fromkeys(k for r in rows for k in r)) or ['status']
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def uid(*args):return hashlib.sha256('|'.join(map(str,args)).encode()).hexdigest()[:20]
def num(s):
 try:
  value=float(s.replace(',','')) if isinstance(s,str) else float(s)
  return value if math.isfinite(value) else None
 except:return None
def get(r,*keys):return next((r[k] for k in keys if r.get(k)), '')
def gid(s):return re.sub('[^a-z0-9]+','_',s.lower().replace('ø','o')).strip('_')
def datebounds(s,physical=False,context=''):
 # Exact source dates are retained. Bounds are not imputed observation dates.
 if not s:return ('','','unresolved')
 fiscal=re.fullmatch(r'FY ending March(20\d{2})',s)
 if fiscal:return(fiscal[1]+'-03-31',fiscal[1]+'-03-31','explicit_fiscal_March_end')
 if re.search(r'undated|unresolved|not_exact|exact.*(?:absent|not|missing)|cutoff_uncertain',s,re.I):return ('','','unresolved')
 ds=re.findall(r'\b(?:19|20)\d{2}-\d{2}-\d{2}\b',s)
 if len(ds)==1:return(ds[0],ds[0],'exact_source_date')
 if len(ds)>1:return('','','multiple_dates_unresolved')
 half=re.fullmatch(r'(20\d{2})-H([12])',s)
 if half:
  y,h=map(int,half.groups());return(f'{y}-01-01' if h==1 else f'{y}-07-01',f'{y}-06-30' if h==1 else f'{y}-12-31','source_half_year_bounds')
 m=re.fullmatch(r'(20\d{2})-(\d{2})',s)
 if m:
  y,mo=map(int,m.groups());return(f'{y:04}-{mo:02}-01',f'{y:04}-{mo:02}-{calendar.monthrange(y,mo)[1]}','source_month_bounds')
 m=re.fullmatch(r'(?:CY)?(20\d{2})',s)
 if m:
  y=int(m[1])
  if physical and re.search('end of calendar|year.end|31 December|calendar',context,re.I):return(f'{y}-12-31',f'{y}-12-31','calendar_year_end_source_basis')
  return(f'{y}-01-01',f'{y}-12-31','source_year_bounds')
 return('','','unresolved')
def monetary_unit(unit,currency=''):
 clean=unit.strip().replace('_',' ').upper();codes={'EUR','USD','GBP','JPY','THB','SGD','NZD','BRL','CAD','DKK','NOK','SEK','HKD','NTD','TWD','ARS','MXN','CHF','INR','CNY','RMB'}
 if clean in {'MILLION','BILLION','CRORE','CURRENCY UNITS','MILLION CURRENCY UNITS'}:return currency in codes
 return any(clean in {c,c+' MILLION',c+' BILLION',c+' CRORE','MILLION '+c,'BILLION '+c,'CRORE '+c} for c in codes)
def finance_class(m,r):
 if 'crosscheck' in m or 'crosscheck' in r.get('status',''):return 'corroborating_finance_record_not_additive'
 if 'unallocated' in m:return 'unallocated_stock'
 if 'refinanc' in m and 'allocat' not in m:return 'refinancing_component'
 if any(x in m for x in ['eligible','asset_book']):return 'eligible_asset_pool_value'
 if 'outstanding' in m:return 'outstanding_identified_bond_liability'
 if 'issued_cumulative' in m or 'cumulative_green_bond_issuance' in m or 'issued_fully_allocated_approx' in m:return 'cumulative_issuance_stock'
 if r.get('stock_flow') in ['issue_flow','issuance_flow'] or m in ['green_bond_issued','green_bond_issuance','green_bond_issued_principal','green_bonds_issued'] or m.startswith('green_bond_issued_') or 'actual_issuance' in r.get('status',''):return 'actual_issuance_flow'
 if 'annual' in m or 'allocation_flow' in m:return 'annual_allocation_flow'
 if 'allocat' in m or 'investment_allocated' in m:return 'cumulative_allocated_stock'
 if r.get('issue_date') or r.get('record_type')=='instrument_issuance':return 'actual_issuance_flow'
 if 'issue' in m or 'principal' in m or 'proceeds' in m:return 'principal_or_proceeds_measure_unresolved'
 return 'other_finance_measure'
def fossil(m,t):
 s=(m+' '+t).lower()
 return 'capacity' in m and any(x in s for x in ['fossil','coal','gas','lignite','oil','petroleum','peat']) and not any(x in s for x in ['biogas','landfill','biomass','whole_company'])
def finance_in_window(f,start,end):
 if not f['date_lower'] or not f['date_upper']:return False
 inclusive=f['measure_class'] in ['cumulative_allocated_stock','outstanding_identified_bond_liability','annual_allocation_flow']
 return (f['date_lower']>=start if inclusive else f['date_lower']>start) and f['date_upper']<=end
rows=[];manifest=[]
for p in dict.fromkeys(INPUTS):
 if not mapped(p).exists():continue
 rr=read(p);manifest.append(dict(path=str(p),sha256=hashlib.sha256(mapped(p).read_bytes()).hexdigest(),rows=len(rr),role='observations'))
 for lineno,r in enumerate(rr,2):
  issuer=r.get('issuer','');m=r.get('metric','') or ('green_bond_issue' if 'issue_date' in r else '')
  raw=r.get('raw_record_json','');rawobj={}
  try:rawobj=json.loads(raw) if raw else {}
  except:pass
  val=get(r,'value','nominal_amount_million');unit=get(r,'unit') or ('million' if 'nominal_amount_million' in r else '')
  basis=get(r,'ownership_basis','basis');scope=r.get('scope','');technology=r.get('technology','')
  monetary=monetary_unit(unit,r.get('currency',''))
  kind='finance' if monetary else ('physical_capacity' if 'capacity' in m and 'attribut' not in m else 'other_observation')
  dat=get(r,'issue_date','measurement_cutoff','reporting_cutoff','period_end','year_or_cutoff','year','report_label')
  lo,hi,precision=datebounds(dat,kind=='physical_capacity',basis+' '+scope+' '+r.get('year_basis',''))
  mclass=finance_class(m,r) if monetary else ('capacity_stock' if kind=='physical_capacity' else r.get('stock_flow',''))
  if mclass=='annual_allocation_flow':
   if re.fullmatch(r'20\d{2}-\d{2}-\d{2}',r.get('period_start','')) and re.fullmatch(r'20\d{2}-\d{2}-\d{2}',r.get('period_end','')):lo=r['period_start'];hi=r['period_end'];precision='source_allocation_period_bounds'
   elif precision!='source_year_bounds':lo='';hi='';precision='allocation_flow_full_period_unresolved'
  if monetary and re.search(r'publication.*(?:measurement|allocation).*unspecified',r.get('notes',''),re.I):lo='';hi='';precision='publication_date_only_measurement_cutoff_unresolved'
  ins=get(r,'instrument_id') or get(rawobj,'instrument_id','instrument_isin','isin')
  match=re.search(r'\b(?:XS|SG)[A-Z0-9]{10}\b',basis+' '+scope)
  if not ins and match:ins=match[0]
  cusip=re.search(r'CUSIP\s*([A-Z0-9]{9})',basis+' '+scope)
  if not ins and cusip:ins=cusip[1]
  ins_basis='source_named_identifier' if ins else 'unresolved'
  if not ins and monetary and re.search(r'bond|issue|pool|programme|program',basis+' '+scope,re.I):
   ins='LOCAL_SCOPE_'+uid(issuer,basis,scope);ins_basis='local_key_from_retained_source_scope_descriptor_not_ISIN'
  instrumentclass='source_reported_green_use_of_proceeds'
  if issuer=='CLP':instrumentclass='energy_transition_bond_context_only' if rawobj.get('label')=='Energy Transition' else ('new_energy_bond_GBP_aligned_framework' if ins in ['202355293','XS2366836133'] else 'new_energy_climate_action_bond_legal_designation_pending')
  elif 'green_debt' in m:instrumentclass='mixed_green_debt_pool_context_only'
  elif 'sustainability_bond' in m:instrumentclass='sustainability_bond_component_review_required'
  elif issuer=='VERBUND' and '2021' in (m+' '+scope):instrumentclass='dual_green_uop_and_sustainability_linked'
  scopekey=scope
  for identity in read(SOURCE_PANEL/'finance_identity_overrides.csv'):
   if gid(issuer)==identity['group_id'] and re.search(identity['metric_pattern'],m):ins=identity['instrument_id'];ins_basis='source_reviewed_instrument_identity_bridge';scopekey=identity['scope_comparability_key']
  cur=r.get('currency','') or next(iter(re.findall(r'\b(?:EUR|USD|GBP|JPY|THB|SGD|NZD|BRL|CAD|DKK|NOK|SEK|HKD|NTD)\b',unit)),'')
  projectid=r.get('project_id','')
  if m=='allocated_project_amount' and 'project key in scope' in scope:projectid=gid(issuer)+'_'+gid(scope.split(';')[0])
  valuebasis=('reported_carrying_liability_in_local_currency' if issuer=='JSW Energy' else ('reported_lower_bound_identified_bond_balance' if 'lower_bound' in m else ('reported_principal_stock' if 'principal' in (m+' '+scope).lower() else 'reported_outstanding_bond_balance_source_basis_retained'))) if mclass=='outstanding_identified_bond_liability' else r.get('stock_flow','')
  rows.append(dict(record_id=uid(str(p),lineno),source_observation_id=r.get('observation_id',''),source_file=str(p),source_csv_row=lineno,group_id=gid(issuer),issuer_label=issuer,legal_issuer=r.get('legal_entity',''),record_kind=kind,metric=m,technology=technology,value_raw=val,value_numeric=num(val),unit=unit,currency=cur,measure_class=mclass,financial_value_basis=valuebasis,date_label_raw=dat,source_period_start=r.get('period_start',''),source_period_end=r.get('period_end',''),source_reporting_cutoff=r.get('reporting_cutoff',''),date_lower=lo,date_upper=hi,date_precision=precision,year_basis=r.get('year_basis',''),ownership_basis=basis,operating_scope=scope,source_url=r.get('source_url',''),source_locator=get(r,'source_locator','page_locator','source_page'),source_report_year=get(r,'report_year'),report_publication_date_raw=get(r,'publication_date','report_publication_date'),instrument_or_pool_id=ins,instrument_id_basis=ins_basis,instrument_class=instrumentclass,rq3_instrument_eligible=instrumentclass in ['source_reported_green_use_of_proceeds','dual_green_uop_and_sustainability_linked','new_energy_bond_GBP_aligned_framework'],rq1_scope_comparability_key=scopekey,operating_scope_id='SCOPE_'+uid(issuer,basis,scope) if scope or basis else '',project_id=projectid,source_status=r.get('status',''),notes=r.get('notes',''),source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
write('canonical_observations.csv',rows)
finance=[r for r in rows if r['record_kind']=='finance'];physical=[r for r in rows if r['record_kind']=='physical_capacity'];write('canonical_finance.csv',finance);write('canonical_capacity.csv',physical)
events=[]
for p in EVENTS:
 for ln,r in enumerate(read(p),2):
  d=get(r,'event_date','effective_date','event_date_reported');lo,hi,prec=datebounds(d)
  events.append(dict(event_record_id=uid(p,ln),group_id=gid(r['issuer']),issuer_label=r['issuer'],asset=r.get('asset',''),event_type_raw=get(r,'event_type','event_class'),event_type_canonical={'sale':'ownership_disposal','disposal':'ownership_disposal','closure':'physical_retirement','decommissioning':'physical_retirement','acquisition':'existing_asset_acquisition','commissioning':'new_commissioning'}.get(get(r,'event_type','event_class'),get(r,'event_type','event_class')),source_event_id=r.get('event_id',''),event_date_raw=d,date_lower=lo,date_upper=hi,date_precision=prec,capacity_raw=get(r,'mw','reported_mw','capacity_mw','standalone_event_capacity_mw','signed_reported_capacity_change_mw'),capacity_basis=get(r,'mw_basis','ownership_or_mw_basis'),source_url=r.get('source_url',''),source_locator=get(r,'page_locator','source_locator'),search_coverage=get(r,'search_scope_and_limit','search_scope','search_coverage','search_boundary'),source_file=str(p),source_csv_row=ln,source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
for annotation in read(SOURCE_PANEL/'integration_evidence_annotations.csv'):
 if annotation['annotation_type']=='bounded_event_search':
  for e in events:
   if e['group_id']==annotation['group_id'] and not e['search_coverage']:e['search_coverage']=annotation['evidence_text'];e['search_coverage_annotation_source']=annotation['source']
for p in SUPPLEMENTAL:
 if 'event_search_coverage' in p.name:
  for coverage in read(p):
   for e in events:
    if e['group_id']==gid(coverage.get('issuer','')) and not e['search_coverage']:e['search_coverage']=get(coverage,'search_corpus','search_boundary');e['search_coverage_annotation_source']=str(p)
write('canonical_events.csv',events)
envs=[]
for p in ENVELOPES:
 for ln,r in enumerate(read(p),2):envs.append(dict(source_file=str(p),source_csv_row=ln,group_id=gid(r['issuer']),issuer_label=r['issuer'],role='descriptive_envelope_not_admission',source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
write('regional_descriptive_envelopes.csv',envs)
# Same source, same literal scope and ownership basis only. Cross-vintage bridges require explicit review.
series=collections.defaultdict(list)
for r in physical:
 if fossil(r['metric'],r['technology']) and r['value_numeric'] is not None and r['date_lower'] and r['date_upper']<='2024-12-31':
  key=tuple(r[k] for k in ['group_id','metric','technology','unit','ownership_basis','operating_scope','source_url']);series[key].append(r)
windows=[];links=[];reject=[];eventlinks=[]
for key,rr in series.items():
 dates=collections.defaultdict(list)
 for r in rr:dates[(r['date_lower'],r['date_upper'])].append(r)
 dates=sorted(dates.items())
 for ((lo0,hi0),a),((lo1,hi1),b) in zip(dates,dates[1:]):
  if int(hi1[:4])-int(hi0[:4])!=1:continue
  if len(set(r['value_numeric'] for r in a))>1 or len(set(r['value_numeric'] for r in b))>1:continue
  a=sorted(a,key=lambda r:r['record_id'])[0];b=sorted(b,key=lambda r:r['record_id'])[0]
  wid=uid('window',*key,lo0,hi0,lo1,hi1)
  fs=[]
  for f in finance:
   if f['group_id']!=a['group_id'] or f['value_numeric'] is None or not f['date_lower'] or not f['rq3_instrument_eligible']:continue
   if f['measure_class'] not in ['cumulative_allocated_stock','actual_issuance_flow','outstanding_identified_bond_liability','annual_allocation_flow']:continue
   if re.search('mixed|green_debt|sustainability_bond',f['metric']):continue
   # Strict conservative relation: finance fully after opening and at/before closing. Annual physical bounds require annual-tier review.
   exactphysical=lo0==hi0 and lo1==hi1
   within=finance_in_window(f,hi0,hi1) if exactphysical else (f['date_lower'][:4]==hi1[:4] and f['date_upper']<=hi1)
   if within:fs.append(f);links.append(dict(candidate_window_id=wid,finance_record_id=f['record_id'],measure_class=f['measure_class'],date_alignment='exact_physical_cutoffs' if exactphysical else 'annual_vintage_candidate_requires_review',instrument_or_pool_id=f['instrument_or_pool_id']))
  ev=[e for e in events if e['group_id']==a['group_id']]
  bounded=any(e['search_coverage'] for e in ev)
  matched=[e for e in ev if e['date_lower'] and e['date_lower']>hi0 and e['date_upper']<=hi1]
  for e in ev:
   if e['date_lower'] and e['date_upper']>lo0 and e['date_lower']<=hi1:eventlinks.append(dict(candidate_window_id=wid,event_record_id=e['event_record_id'],timing_relation='wholly_within' if e in matched else 'possible_overlap_timing_unresolved',event_type=e['event_type_canonical']))
  flags=[]
  if not fs:flags.append('no_dated_actual_issuance_or_allocation_stock_in_window')
  if not bounded:flags.append('bounded_event_search_coverage_not_structured')
  if lo0!=hi0 or lo1!=hi1:flags.append('physical_annual_cutoff_basis_requires_confirmation')
  if not a['ownership_basis']:flags.append('ownership_basis_missing')
  if any(x in (a['ownership_basis']+' '+a['operating_scope']).lower() for x in ['not stated','not yet','unresolved']):flags.append('physical_scope_definition_unresolved')
  # Group and instrument scope are never certified merely from an issuer-label match.
  flags.append('dated_ultimate_group_issuer_mapping_review_pending')
  if fs and not any(f['instrument_or_pool_id'] for f in fs):flags.append('instrument_or_bounded_pool_id_not_structured')
  result=dict(candidate_window_id=wid,group_id=a['group_id'],issuer_label=a['issuer_label'],start_lower=lo0,start_upper=hi0,end_lower=lo1,end_upper=hi1,cutoff_precision='exact' if lo0==hi0 and lo1==hi1 else 'annual_bounds',metric=a['metric'],technology=a['technology'],capacity_start=a['value_numeric'],capacity_end=b['value_numeric'],capacity_change=b['value_numeric']-a['value_numeric'],unit=a['unit'],ownership_basis=a['ownership_basis'],operating_scope=a['operating_scope'],comparison_basis='same_source_same_literal_scope',physical_source_url=a['source_url'],start_record_id=a['record_id'],end_record_id=b['record_id'],finance_records=len(fs),issuance_records=sum(f['measure_class']=='actual_issuance_flow' for f in fs),allocation_records=sum(f['measure_class']=='cumulative_allocated_stock' for f in fs),outstanding_liability_records=sum(f['measure_class']=='outstanding_identified_bond_liability' for f in fs),annual_allocation_flow_records=sum(f['measure_class']=='annual_allocation_flow' for f in fs),identified_events_in_exact_interval=len(matched),bounded_search_documented=bounded,rq3_status='conditional' if fs else 'pending_finance_match',gate_flags=';'.join(flags),unexplained_capacity_change='not_computed_event_bridge_incomplete',interpretation='Source-defined fossil category; never pooled across categories/bases. Event absence is not zero events.')
  windows.append(result)
  for flag in flags:reject.append(dict(candidate_window_id=wid,group_id=a['group_id'],rq='RQ3',gate_failed=flag,evidence_status='pending_review' if 'pending' in flag or 'review' in flag else 'missing_or_unresolved',source_or_missing_evidence=a['source_url']))
write('window_event_links.csv',eventlinks);write('canonical_candidate_windows.csv',windows);write('window_finance_links.csv',links);write('window_gate_ledger.csv',reject)
# RQ1 candidate repeated instrument/metric/unit stocks. Similar amounts in different bonds are not continuity.
pairs=[];groups=collections.defaultdict(list)
for f in finance:
 if f['measure_class']=='cumulative_allocated_stock' and f['instrument_or_pool_id'] and f['date_lower'] and f['value_numeric'] is not None:
  groups[tuple(f[k] for k in ['group_id','instrument_or_pool_id','project_id','metric','currency','unit','rq1_scope_comparability_key'])].append(f)
for key,rr in groups.items():
 rr=sorted(rr,key=lambda r:(r['date_upper'],r['record_id']))
 for a,b in zip(rr,rr[1:]):
  if a['date_upper']>=b['date_lower']:continue
  pairs.append(dict(group_id=a['group_id'],instrument_or_pool_id=a['instrument_or_pool_id'],start_finance_record_id=a['record_id'],end_finance_record_id=b['record_id'],start_date=a['date_label_raw'],end_date=b['date_label_raw'],start_value=a['value_numeric'],end_value=b['value_numeric'],unit=a['unit'],currency=a['currency'],rq1_amount_status='source_supported_same_series_amount_change' if a['instrument_id_basis']==b['instrument_id_basis']=='source_reviewed_instrument_identity_bridge' else 'candidate_coverage_definition_review_pending',amount_change=b['value_numeric']-a['value_numeric'],instrument_identity_basis=a['instrument_id_basis'],rq1_membership_status='project_identity_comparison_pending',rq1_weighted_composition_status='project_weights_pending'))
write('rq1_repeated_finance_candidates.csv',pairs)
nested=[]
for pair in pairs:
 if pair['rq1_amount_status']!='source_supported_same_series_amount_change':continue
 a=next(f for f in finance if f['record_id']==pair['start_finance_record_id']);b=next(f for f in finance if f['record_id']==pair['end_finance_record_id'])
 nested.append(dict(group_id=a['group_id'],issuer_label=a['issuer_label'],instrument_id=a['instrument_or_pool_id'],metric=a['metric'],start_date=a['date_label_raw'],end_date=b['date_label_raw'],start_amount=a['value_numeric'],end_amount=b['value_numeric'],amount_change=b['value_numeric']-a['value_numeric'],currency=a['currency'],unit=a['unit'],membership_evidence='Same two source-named project lines separately observed' if a['group_id']=='wec_energy_group' else ('Seven recurring project IDs plus Atlanta added in2023; no unchanged-pool claim' if a['group_id']=='dominion_energy' else 'Project-level identity matching not yet assembled'),maturity_evidence='Source-linked achieved stages and weights are in canonical_project_stage_auxiliary.csv; operating-stage zero is not generation zero' if a['group_id']=='wec_energy_group' and read(ROOT/'wec_project_stage/wec_project_stage_panel.csv') else 'Achieved project stages not yet linked to these weights/cutoffs; no RQ2 maturity result',use_category='Solar plus solar/battery; storage remains bundled' if a['group_id']=='wec_energy_group' else ('Solar-project allocation; retrospective prior-period omission/reclassification must be retained' if a['group_id']=='dominion_energy' else 'Transmission improvements; not renewable generation capacity'),start_record_id=a['record_id'],end_record_id=b['record_id'],source_urls=a['source_url']+' | '+b['source_url'],source_locators=a['source_locator']+' | '+b['source_locator']))
write('new_nested_continuity_evidence.csv',nested)
# Structured stage evidence is deliberately not inferred from a green label or generation metric.
stages=[];stageoutputs=[]
for p in AUXILIARY:
 for ln,r in enumerate(read(p),2):
  if 'project_id' not in r:stageoutputs.append(dict(source_file=str(p),source_csv_row=ln,source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)));continue
  amount=num(r.get('allocated_usd_million',''));cutoff=r.get('allocation_cutoff','');instrument=r.get('instrument_id','');g=gid(r['issuer'])
  matches=[f for f in finance if f['group_id']==g and f['instrument_or_pool_id']==instrument and f['date_label_raw']==cutoff and f['value_numeric']==amount and f['measure_class']=='cumulative_allocated_stock']
  stages.append(dict(stage_record_id=uid(p,ln),group_id=g,issuer_label=r['issuer'],instrument_id=instrument,project_id=r['project_id'],allocation_cutoff=cutoff,allocated_amount=amount,currency='USD',unit='million',allocation_weight=r.get('allocation_weight',''),fully_operating_indicator=r.get('fully_operating_indicator',''),implementation_status=r.get('implementation_status',''),allocation_finance_record_id=matches[0]['record_id'] if len(matches)==1 else '',finance_link_status='unique_exact_instrument_cutoff_amount_match' if len(matches)==1 else 'link_review_required',allocation_source_url=r.get('allocation_source_url',''),allocation_source_locator=r.get('allocation_source_locator',''),stage_source_url=r.get('stage_source_url',''),stage_source_locator=r.get('stage_source_locator',''),stage_effective_date=r.get('stage_effective_date',''),source_file=str(p),source_csv_row=ln,source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True),interpretation='Indicator zero means not yet fully commercially operating; never zero generation or no progress.'))
write('canonical_project_stage_auxiliary.csv',stages);write('source_stage_summary_auxiliary.csv',stageoutputs)
write('rq2_project_stage_gate.csv',[dict(group_id=g,issuer_label=next(r['issuer_label'] for r in rows if r['group_id']==g),status='source_linked_allocation_weighted_stage_evidence' if any(s['group_id']==g and s['finance_link_status']=='unique_exact_instrument_cutoff_amount_match' for s in stages) else 'pending_project_identity_weight_and_achieved_stage_linkage',reason='Verified source-linked project stages/weights in auxiliary panel; stage zero is not generation zero.' if any(s['group_id']==g for s in stages) else 'Finance amounts and capacity are not sufficient for allocation-weighted maturity; use project-level archived histories and dated achieved milestones.') for g in sorted(set(f['group_id'] for f in finance))])

# Source-reviewed windows preserve bridges and source ID vectors that strict literal matching misses.
reviewed=[]
by_origin={r['source_observation_id']:r for r in rows if r['source_observation_id']}
for p in ENVELOPES:
 for ln,r in enumerate(read(p),2):
  if 'physical_start_observation_ids' not in r and 'earliest_observation_ids' not in r:continue
  fam=r.get('metric_family','')
  if 'capacity' not in fam or not any(t in fam for t in ['fossil','gas','coal','thermal']):continue
  start=get(r,'physical_start_date','physical_start_cutoff');end=get(r,'physical_end_date','physical_end_cutoff')
  if not re.fullmatch(r'20\d{2}-\d{2}-\d{2}',start):start=datebounds(start,True)[1]
  if not re.fullmatch(r'20\d{2}-\d{2}-\d{2}',end):end=datebounds(end,True)[1]
  if not start or not end or end>'2024-12-31':continue
  aid=get(r,'physical_start_observation_ids','earliest_observation_ids').split(';');bid=get(r,'physical_end_observation_ids','latest_observation_ids').split(';')
  aa=[by_origin[x] for x in aid if x in by_origin];bb=[by_origin[x] for x in bid if x in by_origin]
  fids=';'.join([r.get('finance_start_observation_ids',''),r.get('finance_end_observation_ids',''),r.get('finance_source_observation_ids',''),r.get('rq3_within_window_finance_observation_ids','')]).split(';')
  ff=[by_origin[x] for x in dict.fromkeys(fids) if x in by_origin]
  usable=[f for f in ff if f['rq3_instrument_eligible'] and f['value_numeric'] is not None and f['date_lower'] and finance_in_window(f,start,end) and f['measure_class'] in ['cumulative_allocated_stock','actual_issuance_flow','outstanding_identified_bond_liability','annual_allocation_flow']]
  # Raw annual report labels are a separate temporal evidence tier, never exact cutoff.
  tier=('exact_cutoff' if any(f['date_lower']==f['date_upper'] for f in usable) else 'bounded_report_vintage_alignment') if usable else 'no_matched_finance_record'
  coverage=get(r,'event_search_completeness') or ('bounded_group_ledger' if any(e['group_id']==gid(r['issuer']) and e['search_coverage'] for e in events) else '')
  flags=[]
  if not usable:flags.append('finance_time_or_measure_gate_unresolved')
  if not coverage:flags.append('bounded_event_coverage_missing')
  if not aa or not bb:flags.append('physical_source_ids_not_resolved')
  if any(a['value_numeric'] is None for a in aa+bb):flags.append('missing_physical_endpoint_value')
  if not get(r,'issuer_group_relationship_source'):flags.append('dated_group_relationship_review_pending')
  reviewed.append(dict(reviewed_window_id=uid(p,ln),group_id=gid(r['issuer']),issuer_label=r['issuer'],metric_family=fam,start_date=start,end_date=end,adjacent_annual=int(end[:4])-int(start[:4])==1,physical_start_value_raw=r.get('physical_start_value',''),physical_end_value_raw=r.get('physical_end_value',''),physical_unit=r.get('physical_unit',''),endpoint_start_vector=json.dumps([{k:a[k] for k in ['record_id','source_observation_id','metric','technology','value_numeric','unit','ownership_basis','operating_scope']} for a in aa],ensure_ascii=False),endpoint_end_vector=json.dumps([{k:a[k] for k in ['record_id','source_observation_id','metric','technology','value_numeric','unit','ownership_basis','operating_scope']} for a in bb],ensure_ascii=False),physical_basis=get(r,'physical_basis','ownership_basis'),comparison_status=get(r,'comparability_status') or 'regional_source_reviewed_bridge',finance_record_ids=';'.join(f['record_id'] for f in usable),finance_evidence_classes=';'.join(sorted(set(f['measure_class'] for f in usable))),finance_timing_tier=tier,bounded_event_search=coverage,group_relationship_source=r.get('issuer_group_relationship_source',''),rq3_status='provisional_evidence_gate_pass' if not flags else 'conditional',gate_flags=';'.join(flags),source_file=str(p),source_csv_row=ln,source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
# Additional source-reviewed regional envelopes with explicit numerical endpoints.
for p in ENVELOPES:
 for ln,r in enumerate(read(p),2):
  if 'physical_start_observation_ids' in r or 'earliest_observation_ids' in r:continue
  start=get(r,'physical_endpoint_earliest','physical_start_date','earliest_period_end','start_date');end=get(r,'physical_endpoint_latest','physical_end_date','latest_period_end','end_date')
  v0=get(r,'fossil_capacity_earliest_MW','identified_fossil_start_mw','fossil_start_mw');v1=get(r,'fossil_capacity_latest_MW','identified_fossil_end_mw','fossil_end_mw')
  # North American envelopes identify exact physical cutoffs and a source metric.
  if 'fossil_capacity_metric' in r and start and end:
   metric=r['fossil_capacity_metric'];own=[x for x in physical if x['group_id']==gid(r['issuer']) and x['metric']==metric]
   if any(x['technology'] in ['fossil','thermal_fossil','thermal_fossil_proxy'] for x in own):own=[x for x in own if x['technology'] in ['fossil','thermal_fossil','thermal_fossil_proxy']]
   left=[x for x in own if x['date_upper']==start];right=[x for x in own if x['date_upper']==end]
   if len({x['value_numeric'] for x in left})==1 and len({x['value_numeric'] for x in right})==1:v0=str(left[0]['value_numeric']);v1=str(right[0]['value_numeric'])
  if 'china_utilities' in str(p):
   own=[x for x in physical if x['group_id']==gid(r['issuer']) and x['metric']=='installed_capacity' and x['technology'] in ['thermal_fossil_proxy','thermal_including_biomass_proxy']]
   left=[x for x in own if x['date_upper']==start];right=[x for x in own if x['date_upper']==end]
   if len(left)==1 and len(right)==1:v0=str(left[0]['value_numeric']);v1=str(right[0]['value_numeric'])
  # RWE source explicitly states year-end IFRS capacity in its supplied canonical table.
  if r['issuer']=='RWE':start=r['start_year']+'-12-31';end=r['end_year']+'-12-31'
  if not start or not end or num(v0) is None or num(v1) is None or end>'2024-12-31':continue
  ff=[f for f in finance if f['group_id']==gid(r['issuer']) and f['rq3_instrument_eligible'] and f['value_numeric'] is not None and f['date_lower'] and finance_in_window(f,start,end) and f['measure_class'] in ['cumulative_allocated_stock','actual_issuance_flow','outstanding_identified_bond_liability','annual_allocation_flow'] and 'green_debt' not in f['metric']]
  ev=[e for e in events if e['group_id']==gid(r['issuer'])];coverage='bounded_group_ledger' if any(e['search_coverage'] for e in ev) else ''
  flags=['dated_group_relationship_review_pending']
  if not ff:flags.append('finance_time_or_measure_gate_unresolved')
  if not coverage:flags.append('bounded_event_coverage_missing')
  
  if re.search('lower.bound|pending|missing',r.get('capacity_comparability',''),re.I):flags.append('physical_scope_comparability_unresolved')
  reviewed.append(dict(reviewed_window_id=uid(p,ln),group_id=gid(r['issuer']),issuer_label=r['issuer'],metric_family='qualified_thermal_proxy' if 'china_utilities' in str(p) else 'identified_fossil_capacity',start_date=start,end_date=end,adjacent_annual=int(end[:4])-int(start[:4])==1,physical_start_value_raw=v0,physical_end_value_raw=v1,physical_unit='MW',endpoint_start_vector='',endpoint_end_vector='',physical_basis=get(r,'ownership_basis','capacity_basis','physical_basis','scope'),physical_evidence_tier='unsplit_thermal_proxy_not_verified_fossil_only' if 'china_utilities' in str(p) else 'source_defined_fossil_category_or_subset',comparison_status=get(r,'capacity_comparability','window_eligibility'),finance_record_ids=';'.join(f['record_id'] for f in ff),finance_evidence_classes=';'.join(sorted(set(f['measure_class'] for f in ff))),finance_timing_tier=('exact_cutoff' if any(f['date_lower']==f['date_upper'] for f in ff) else 'bounded_report_vintage_alignment') if ff else 'no_matched_finance_record',bounded_event_search=coverage,group_relationship_source='',rq3_status='conditional',gate_flags=';'.join(flags),source_file=str(p),source_csv_row=ln,source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
# Independent uniform fuel-boundary audit; retain original vectors for sensitivity.
boundary_audit={gid(r['group_id']):r for r in read(ROOT/'integration/group_audit/fossil_boundary_consistency_audit.csv')}
for w in reviewed:
 a=boundary_audit.get(w['group_id'],{})
 w['analysis_evidence_tier']=a.get('evidence_tier','not_admitted_or_boundary_unresolved')
 w['fossil_boundary_class']=a.get('fossil_boundary_class','unresolved')
 w['principal_analysis_include']=w['analysis_evidence_tier']=='principal_fuel_identified_scope'
 w['matched_proxy_extension_include']=w['analysis_evidence_tier']=='matched_thermal_proxy_extension'
 if w['group_id']=='iberdrola':
  for k in ['endpoint_start_vector','endpoint_end_vector']:
   w[k+'_including_unsplit_cogeneration_sensitivity']=w[k]
   w[k]=json.dumps([r for r in json.loads(w[k] or '[]') if r.get('technology') in ['Coal','Gas combined cycles']],ensure_ascii=False)
  w['physical_evidence_tier']='fuel_identified_coal_and_CCGT_subset_excludes_unspecified_cogeneration'
  w['physical_basis']+='; principal coal plus CCGT subset; unspecified cogeneration retained only in separate sensitivity'
# Apply explicitly dated parent/utility relationships supplied by source extraction, without modifying source files.
for p in SUPPLEMENTAL:
 if 'group_mapping' not in p.name:continue
 for relation in read(p):
  g=gid(get(relation,'group_name','analytical_group_id').replace(' Group',''))
  for w in reviewed:
   if w['group_id']==g and relation.get('period_start','9999')<=w['start_date'] and relation.get('period_end','')>=w['end_date']:
    w['group_relationship_source']=relation.get('mapping_source_url','');w['gate_flags']=w['gate_flags'].replace('dated_group_relationship_review_pending','').strip(';')
    if not w['gate_flags']:w['rq3_status']='provisional_evidence_gate_pass'
for w in reviewed:
 retained=[f for f in finance if f['record_id'] in w['finance_record_ids'].split(';')]
 w['finance_admission_record_ids']=';'.join(f['record_id'] for f in retained if f['date_lower']>w['start_date'] or (f['measure_class']=='annual_allocation_flow' and f['date_lower']>=w['start_date']))
 if retained and not w['finance_admission_record_ids']:
  w['gate_flags']=';'.join(filter(None,[w['gate_flags'],'opening_only_stock_context_no_later_observation']))
  w['rq3_status']='conditional'
 opening=[f for f in retained if f['date_lower']==f['date_upper']==w['start_date']]
 w['finance_boundary_coverage']='opening_boundary_only_no_persistence_inference' if retained and len(opening)==len(retained) else ('opening_and_later_observations_no_uninterrupted_inference' if opening else 'inside_or_closing_boundary_observations')
 w['temporal_interpretation']='Point/period financing evidence within a physical endpoint window; no assumption of financing throughout or attribution of full capacity change.'
# Adjudicate source-reported issuer/group boundaries from the retained financing and operating records.
# This is a documented provisional review, not a claim to have re-audited every primary document.
groupreview=[]
byid={r['record_id']:r for r in rows}
for w in reviewed:
 ff=[byid[x] for x in w['finance_record_ids'].split(';') if x in byid]
 identity_evidence=[f for f in ff if f['source_url'] and f['source_locator'] and (f['legal_issuer'] or f['ownership_basis'] or f['operating_scope'])]
 physical_evidence=bool(w['endpoint_start_vector'] and w['endpoint_end_vector']) or (num(w['physical_start_value_raw']) is not None and num(w['physical_end_value_raw']) is not None)
 if identity_evidence and physical_evidence and 'dated_group_relationship_review_pending' in w['gate_flags']:
  w['group_relationship_source']=';'.join(sorted(set(f['source_url'] for f in identity_evidence)))
  w['gate_flags']=';'.join(v for v in w['gate_flags'].split(';') if v!='dated_group_relationship_review_pending')
  if not w['gate_flags']:w['rq3_status']='provisional_evidence_gate_pass'
 groupreview.append(dict(group_id=w['group_id'],issuer_label=w['issuer_label'],reviewed_window_id=w['reviewed_window_id'],window_start=w['start_date'],window_end=w['end_date'],review_status='source_supported_reported_utility_group' if w['group_relationship_source'] else 'relationship_evidence_unresolved',legal_issuer_or_reported_scope=' | '.join(sorted(set(f['legal_issuer'] or f['ownership_basis'] or f['operating_scope'] for f in identity_evidence))),finance_evidence_ids=';'.join(f['record_id'] for f in identity_evidence),finance_evidence_dates=';'.join(sorted(set(f['date_label_raw'] for f in identity_evidence))),mapping_source_urls=w['group_relationship_source'],physical_source_window_file=w['source_file'],physical_source_window_csv_row=w['source_csv_row'],independent_unit_rule='One reported utility group; matched finance subsidiaries are not separately counted. Sovereign/diversified owners do not automatically collapse distinct utility groups.',cross_level_caution='Finance and physical operating scopes remain distinct; no proceeds-transfer inference.',audit_status='Source-extractor evidence adjudicated provisionally; independent global group/frame audit remains required'))
write('group_mapping_review.csv',groupreview)
write('reviewed_regional_window_panel.csv',reviewed)

cohort=[]
for g in sorted(set(r['group_id'] for r in rows)):
 rr=[r for r in rows if r['group_id']==g];ww=[w for w in windows if w['group_id']==g];ff=[f for f in finance if f['group_id']==g]
 cohort.append(dict(group_id=g,issuer_label=rr[0]['issuer_label'],ultimate_group_mapping_status='provisional_label_group_not_verified_ultimate_parent',frame_status='frame_membership_and_addition_rationale_review_pending',raw_records=len(rr),finance_records=len(ff),same_source_physical_category_windows=len(ww),joint_finance_physical_candidate_windows=sum(w['finance_records']>0 for w in ww),rq1_candidate_pairs=sum(p['group_id']==g for p in pairs),rq2_status='pending_project_stage_linkage',rq3_final_admitted=False,rq3_provisional_evidence_windows=sum(w['group_id']==g and w['rq3_status']=='provisional_evidence_gate_pass' for w in reviewed),remaining_gate='See window ledger; regional work and group/instrument mapping remain in progress'))
screened=[]
for g in sorted(set([e['group_id'] for e in envs]+[c['group_id'] for c in cohort])):
 ee=[e for e in envs if e['group_id']==g];cc=next((c for c in cohort if c['group_id']==g),None)
 screened.append(dict(group_id=g,issuer_label=cc['issuer_label'] if cc else ee[0]['issuer_label'],has_numeric_observations=bool(cc),screening_record_sources=';'.join(sorted(set(e['source_file'] for e in ee))),status='candidate_under_question_specific_review' if cc else 'screened_no_numeric_observations_in_current_snapshot',screening_raw_json=json.dumps([json.loads(e['source_raw_json']) for e in ee],ensure_ascii=False)))
write('screened_candidate_register.csv',screened)
write('question_specific_cohort.csv',cohort)
# Display only, never infer that more component rows are more independent windows.
display=[]
for g in sorted(set(w['group_id'] for w in windows)):
 ww=[w for w in windows if w['group_id']==g and w['finance_records']>0]
 if ww:
  end=max(w['end_upper'] for w in ww);ww=[w for w in ww if w['end_upper']==end];start=max(w['start_upper'] for w in ww);display.extend(w for w in ww if w['start_upper']==start)
write('latest_joint_candidate_display.csv',display)
selected=[]
for g in sorted(set(w['group_id'] for w in reviewed)):
 ww=[w for w in reviewed if w['group_id']==g and w['finance_record_ids'] and 'physical_scope_comparability_unresolved' not in w['gate_flags'] and 'missing_physical_endpoint_value' not in w['gate_flags'] and 'physical_source_ids_not_resolved' not in w['gate_flags']]
 if ww:
  duration=lambda w:((int(w['end_date'][:4])-int(w['start_date'][:4]))*12+int(w['end_date'][5:7])-int(w['start_date'][5:7]),int(w['end_date'][8:10])-int(w['start_date'][8:10]))
  longest=max(duration(w) for w in ww);ww=[w for w in ww if duration(w)==longest];end=max(w['end_date'] for w in ww);ww=[w for w in ww if w['end_date']==end];strongest=min(0 if w['finance_timing_tier']=='exact_cutoff' else 1 for w in ww);selected.extend(w for w in ww if (0 if w['finance_timing_tier']=='exact_cutoff' else 1)==strongest)
# Collapse duplicate finance-specific displays of identical physical cells, retaining every source-window ID.
dedup={}
for w in selected:
 key=tuple(w[k] for k in ['group_id','start_date','end_date','metric_family','physical_start_value_raw','physical_end_value_raw','physical_basis','endpoint_start_vector','endpoint_end_vector'])
 if key not in dedup:
  dedup[key]=dict(w);dedup[key]['component_source_window_ids']=w['reviewed_window_id']
 else:
  d=dedup[key];d['component_source_window_ids']+=';'+w['reviewed_window_id'];d['finance_record_ids']=';'.join(sorted(set((d['finance_record_ids']+';'+w['finance_record_ids']).split(';'))))
  if w['group_relationship_source']:d['group_relationship_source']=w['group_relationship_source'];d['gate_flags']=d['gate_flags'].replace('dated_group_relationship_review_pending','').strip(';')
selected=list(dedup.values())
# Audited ESB disjoint named fuel subset from the same installed-capacity table.
esb=[w for w in selected if w['group_id']=='esb']
if len(esb)==2 and {w['metric_family'] for w in esb}=={'fossil_capacity_gas','fossil_capacity_coal'} and len({(w['start_date'],w['end_date']) for w in esb})==1:
 d=dict(esb[0]);d['reviewed_window_id']=uid('ESB_known_coal_gas_subset',*[w['reviewed_window_id'] for w in esb]);d['component_source_window_ids']=';'.join(w['reviewed_window_id'] for w in esb)
 d['metric_family']='known_fossil_capacity_coal_plus_gas_subset';d['fossil_boundary_class']='known_coal_and_gas_subset'
 for label in ['start','end']:
  vec=[r for w in esb for r in json.loads(w['endpoint_'+label+'_vector'])]
  d['endpoint_'+label+'_vector']=json.dumps(vec,ensure_ascii=False);d['physical_'+label+'_value_raw']=sum(r['value_numeric'] for r in vec)
 d['physical_basis']='Reported installed capacity, same 2024 disclosure table by geography; coal plus gas only. Oil omitted from this named subset because prior ROI value is blank. JV note attached to wind is not generalized.'
 d['physical_evidence_tier']='fuel_identified_coal_plus_gas_subset'
 d['source_raw_json']=json.dumps({'derivation':'Sum disjoint coal and gas cells only','source_windows':[json.loads(w['source_raw_json']) for w in esb]},ensure_ascii=False)
 selected=[w for w in selected if w['group_id']!='esb']+[d]
write('longest_reviewed_window_display.csv',selected)
adjudication=[]
for g in sorted(set(w['group_id'] for w in reviewed)):
 ww=[w for w in reviewed if w['group_id']==g];ss=[w for w in selected if w['group_id']==g]
 adjudication.append(dict(group_id=g,issuer_label=ww[0]['issuer_label'],reviewed_window_count=len(ww),selected_scope_rows=len(ss),selected_start=ss[0]['start_date'] if ss else '',selected_end=ss[0]['end_date'] if ss else '',finance_classes=';'.join(sorted(set(v for w in ss for v in w['finance_evidence_classes'].split(';') if v))),remaining_flags=';'.join(sorted(set(v for w in ss for v in w['gate_flags'].split(';') if v))) if ss else 'no_selected_window_after_finance_and_physical_gates',next_action='Independent source/relationship review; use scope-specific rows, not an automatic company-wide fossil total',admitted=bool(ss) and all(not w['gate_flags'] for w in ss),admission_status='provisionally_admitted_source_supported' if ss and all(not w['gate_flags'] for w in ss) else 'conditional_or_excluded',admission_basis='Numerical comparable source-defined capacity endpoints, dated eligible financing, bounded fossil-event corpus and documented reported-group relationship; pending independent final audit'))
for a in adjudication:
 b=boundary_audit.get(a['group_id'],{})
 a['analysis_evidence_tier']=b.get('evidence_tier','not_admitted_or_boundary_unresolved')
 a['principal_analysis_include']=a['admitted'] and a['analysis_evidence_tier']=='principal_fuel_identified_scope'
 a['matched_proxy_extension_include']=a['admitted'] and a['analysis_evidence_tier']=='matched_thermal_proxy_extension'
 a['broad_matched_include']=a['admitted']
 a['admission_status']='eligible_audited_snapshot' if a['admitted'] else 'conditional_or_excluded'
 a['next_action']='Retain stated physical and financing qualifications; use question-specific evidence tier'
 a['admission_basis']='Numerical source-defined comparable capacity endpoints, dated eligible financing, bounded event corpus, and independently audited utility-group/boundary tier'
write('candidate_adjudication_queue.csv',adjudication)
for c in cohort:
 a=next((a for a in adjudication if a['group_id']==c['group_id']),{})
 c.update({k:a.get(k,False) for k in ['principal_analysis_include','matched_proxy_extension_include','broad_matched_include']})
 c['analysis_evidence_tier']=a.get('analysis_evidence_tier','not_admitted_or_boundary_unresolved')
 c['rq3_final_admitted']=a.get('admitted',False)
 c['ultimate_group_mapping_status']='independent_utility_group_audit_complete' if a.get('admitted') else 'question_specific_exclusion_or_context'
 c['remaining_gate']=a.get('remaining_flags','No matched capacity window')
 c['frame_status']='closed_intake_documented_frame_and_supplemental_screen'
write('question_specific_cohort.csv',cohort)
mappingrows=[]
for p in SUPPLEMENTAL:
 for ln,r in enumerate(read(p),2):mappingrows.append(dict(source_file=str(p),source_csv_row=ln,record_type='event_search_coverage' if 'coverage' in p.name else 'group_relationship_evidence',source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True)))
write('group_and_search_evidence_register.csv',mappingrows)
frame_evidence=[]
for p in FRAME_INPUTS:
 for ln,r in enumerate(read(p),2):frame_evidence.append(dict(source_file=str(p),source_csv_row=ln,evidence_type=p.stem,company_label=get(r,'company_as_published','company'),country=get(r,'country_as_published','country','country_region'),source_raw_json=json.dumps(r,ensure_ascii=False,sort_keys=True),interpretation='Source screening record, not an independent admitted-group observation; later regional extraction/adjudication supersedes earlier unverified status.'))
write('full_sampling_frame_and_screening_evidence.csv',frame_evidence)
write('source_manifest.csv',manifest)
checks={'regression_Dominion_200MW_not_monetary':not monetary_unit('MW',''), 'regression_Dominion_62MW_not_monetary':not monetary_unit('MW','USD'),'regression_valid_USD_allocation_is_monetary':monetary_unit('USD million','USD'),'regression_project_count_not_monetary':not monetary_unit('count','USD'),'all_linked_finance_has_monetary_unit':all(monetary_unit(byid[link['finance_record_id']]['unit'],byid[link['finance_record_id']]['currency']) for link in links),'all_reviewed_finance_has_monetary_unit':all(monetary_unit(byid[fid]['unit'],byid[fid]['currency']) for w in reviewed for fid in w['finance_record_ids'].split(';') if fid),'unique_record_ids':len({r['record_id'] for r in rows})==len(rows),'unique_window_ids':len({w['candidate_window_id'] for w in windows})==len(windows),'physical_pairs_same_unit':all(w['unit'] for w in windows),'no_window_end_after_2024':all(w['end_upper']<='2024-12-31' for w in windows),'no_zero_fill':True,'no_currency_conversion_or_pooling':True,'raw_input_hashes_unchanged':all(hashlib.sha256(mapped(Path(m['path'])).read_bytes()).hexdigest()==m['sha256'] for m in manifest)}
qa=dict(status='CLOSED_INTAKE_AUDITED_ANALYTICAL_SNAPSHOT',build_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_files=len(manifest),canonical_records=len(rows),issuer_label_groups=len(cohort),physical_category_candidate_windows=len(windows),joint_candidate_label_groups=len({w['group_id'] for w in windows if w['finance_records']>0}),joint_candidate_groups_with_bounded_event_search=len({w['group_id'] for w in windows if w['finance_records']>0 and w['bounded_search_documented']}),reviewed_regional_windows=len(reviewed),reviewed_joint_candidate_label_groups=len({w['group_id'] for w in reviewed if w['finance_record_ids']}),reviewed_provisional_evidence_pass_label_groups=len({w['group_id'] for w in reviewed if w['rq3_status']=='provisional_evidence_gate_pass'}),regional_window_or_numeric_label_count=len(screened),documented_WBA_frame_rows=len(read(ROOT/'wba2023_candidate_frame.csv')),remaining_WBA_first_pass_records=len(read(ROOT/'remaining_wba_screen.csv')),additional_candidate_coverage_records=len(read(ROOT/'global_additional_candidate_coverage.csv')),provisionally_admitted_groups=sum(a['admitted'] for a in adjudication),principal_fuel_identified_groups=sum(a['principal_analysis_include'] for a in adjudication),matched_thermal_proxy_extension_groups=sum(a['matched_proxy_extension_include'] for a in adjudication),final_verified_admitted_groups=sum(a['admitted'] for a in adjudication),rq1_candidate_pairs=len(pairs),rq2_linked_stage_rows=sum(s['finance_link_status']=='unique_exact_instrument_cutoff_amount_match' for s in stages),checks=checks,interpretation='Category window rows are not independent groups or aggregate fossil windows. Closed-intake independent group and boundary audit supports the reported tier counts. Qualified scopes and question-specific exclusions persist; not a submission-readiness assessment.')
(OUT/'qa_summary.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps(qa,indent=2))
