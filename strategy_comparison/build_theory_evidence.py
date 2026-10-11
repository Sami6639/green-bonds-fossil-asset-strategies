#!/usr/bin/env python3
"""Source-frozen companion comparison and descriptive event-presence cross-tab.
No network, no source edits. Usage: python build_theory_evidence.py [release_directory].
"""
import sys,json,hashlib
from pathlib import Path
import pandas as pd
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'frozen_inputs'
OUT=Path(__file__).resolve().parent
inputs={}
def read(rel):
 p=BASE/rel; inputs[rel]=hashlib.sha256(p.read_bytes()).hexdigest();d=pd.read_csv(p).fillna('');d['_release_csv_row']=range(2,len(d)+2);return d

def save(d,name):d.to_csv(OUT/name,index=False)
N='nested_histories/'; O=N+'original_three/'; E=N+'expanded_cases/'; A='analysis_panel/';R=A+'results/'
fig=read('figures/figure_1_plot_data.csv'); principal=fig[fig.principal_analysis_include.eq(True)].copy()
assert len(fig)==37 and len(principal)==33 and fig.matched_proxy_extension_include.sum()==4
assert principal.fossil_direction.value_counts().to_dict()=={'decrease':20,'increase':9,'unchanged_at_reported_precision':4}
ev=read(R+'selected_window_event_evidence.csv'); ev=ev[ev.group_id.isin(principal.group_id)].copy()
valid=ev[(ev.timing=='wholly_within_opening_exclusive_interval')&(ev.event_family!='coverage_or_unresolved_statement')].copy()
families=sorted(set(valid.event_family))
rows=[]
for _,g in principal.iterrows():
 e=valid[(valid.group_id==g.group_id)&(valid.selected_window_id==g.selected_window_id)]
 assert set(e.event_family)==set(filter(None,g.reported_event_families_present.split(';')))
 for family in families:
  s=e[e.event_family==family]
  rows.append(dict(group_id=g.group_id,issuer=g.issuer_label,selected_window_id=g.selected_window_id,start_date=g.start_date,end_date=g.end_date,physical_basis=g.physical_basis,fossil_direction=g.fossil_direction,event_family=family,presence_state='documented' if len(s) else 'not_documented_unknown',event_record_ids=';'.join(sorted(set(s.event_record_id))),source_urls=' | '.join(sorted(set(s.source_url))),source_locators=' | '.join(sorted(set(s.source_locator))),selected_event_release_rows=';'.join(map(str,s._release_csv_row)),direction_release_file='figures/figure_1_plot_data.csv',direction_release_row=g._release_csv_row))
pres=pd.DataFrame(rows);save(pres,'principal33_direction_event_presence_long.csv');save(ev,'principal33_selected_window_event_evidence.csv')
# Expose original fuel descriptors without inventing missing fuel classifications.
fuel=[]
for _,r in valid.iterrows():
 raw=json.loads(r.event_raw_json)
 desc={k:raw[k] for k in ['fuel','technology','fossil_technology','notes','perimeter_effect','interpretive_caution'] if raw.get(k)}
 fuel.append(dict(event_record_id=r.event_record_id,group_id=r.group_id,issuer=r.issuer_label,asset=r.asset,event_family=r.event_family,retained_fuel_descriptor=raw.get('fuel',raw.get('technology',raw.get('fossil_technology','unknown_in_direct_fields'))),retained_context_json=json.dumps(desc,ensure_ascii=False),source_url=r.source_url,source_locator=r.source_locator,release_csv_row=r._release_csv_row))
save(pd.DataFrame(fuel),'event_family_fuel_scope_audit.csv')
ct=[]
for direction,groups in principal.groupby('fossil_direction'):
 for family in families:
  s=pres[(pres.fossil_direction==direction)&(pres.event_family==family)]
  n=int(s.presence_state.eq('documented').sum())
  ct.append(dict(fossil_direction=direction,event_family=family,denominator_groups=len(groups),documented_presence_groups=n,not_documented_unknown_groups=len(groups)-n,documented_group_ids=';'.join(s.loc[s.presence_state.eq('documented'),'group_id'])))
ct=pd.DataFrame(ct);save(ct,'principal33_direction_event_crosstab.csv')
# The compact table focuses on completed/status/ownership families, not planned projects.
focus=['reported_physical_closure_or_retirement','ownership_exit_or_dispatch_right_exit','operational_cessation_or_reserve','commissioning_or_uprating','existing_asset_acquisition']
compact=ct[ct.event_family.isin(focus)].pivot(index='fossil_direction',columns='event_family',values='documented_presence_groups').reset_index();save(compact,'principal33_direction_event_compact.csv')
# All-seven matrix uses explicit source-row bundles; narratives are bounded documentary synthesis.
M=[];P=[]
def case(name,scope,amount,membership,weights,implementation,ownership,link,unknown,refs):
 ids=[]; urls=set()
 for rel in refs:
  d=read(rel)
  for _,row in d.iterrows():
   rid=f'{name}:{rel}:{row._release_csv_row}';ids.append(rid)
   urlcols=[c for c in d if 'url' in c or c in ['operation_source','investment_source','capacity_source']]
   us=' | '.join(str(row[c]) for c in urlcols if str(row[c]))
   if us:urls.add(us)
   P.append(dict(case=name,evidence_id=rid,release_file=rel,release_csv_row=row._release_csv_row,source_urls=us,source_row_json=json.dumps({k:v for k,v in row.items() if k!='_release_csv_row'},ensure_ascii=False,default=str)))
 M.append(dict(case=name,scope_and_dates=scope,amount_continuity=amount,project_membership=membership,allocation_weights=weights,achieved_implementation=implementation,ownership_and_control=ownership,explicit_documentary_link=link,unresolved_and_noninferences=unknown,evidence_ids=';'.join(ids),source_urls=' | '.join(sorted(urls))))
handcoding=pd.read_csv(OUT/'seven_history_handcoding.csv').fillna('')
for _,h in handcoding.iterrows():
 case(h['case'],h.scope_and_dates,h.amount_continuity,h.project_membership,h.allocation_weights,h.achieved_implementation,h.ownership_and_control,h.explicit_documentary_link,h.unresolved_and_noninferences,h.source_files.split(';'))
# Filter broad support files to relevant issuer for clean row-level traceability.
pro=pd.DataFrame(P)
keep=[]
for _,r in pro.iterrows():
 raw=json.loads(r.source_row_json)
 issuer=raw.get('issuer',raw.get('issuer_label',''))
 keep.append(not (r.release_file.startswith(E) and 'new_nested_continuity' in r.release_file or r.release_file.endswith('na_nested_project_facts.csv')) or ((r['case']=='Dominion' and issuer=='Dominion Energy')or(r['case']=='Eletrobras' and issuer=='Eletrobras')or(r['case']=='Constellation' and issuer=='Constellation Energy')))
pro=pro[keep];matrix=pd.DataFrame(M)
for idx,r in matrix.iterrows():
 s=pro[pro['case']==r['case']];matrix.loc[idx,'evidence_ids']=';'.join(s.evidence_id);matrix.loc[idx,'source_urls']=' | '.join(sorted(set(s.source_urls)-{''}))
save(matrix,'seven_history_comparison.csv');save(pro,'seven_history_row_provenance.csv')
# Recompute the matched allocation-weight/stage comparisons rather than merely copying figure values.
stage=read(E+'wec_project_stage_panel.csv');checks=[]
for date,g in stage.groupby('allocation_cutoff'):
 total=g.allocated_usd_million.sum();v=(g.allocated_usd_million*g.fully_operating_indicator).sum()/total*100
 assert abs(total-g.total_allocated_usd_million.iloc[0])<1e-8
 assert abs(g.allocation_weight.sum()-1)<1e-8
 checks.append(dict(case='WEC',cutoff=date,total_million=total,currency='USD',fully_operating_share_pct=v,weight_basis='cutoff_specific',source_file=E+'wec_project_stage_panel.csv',source_rows=';'.join(map(str,g._release_csv_row))))
s1=read(O+'sse/green_uop_2023_gb5_project_rows.csv');s2=read(O+'sse/bond_project_rows_2024.csv');s2=s2[s2.bond_group==5];assert sorted(s1.allocation_stock_gbp_m)==sorted(s2.allocated_gbp_million)
master=read(O+'sse/fixed_cohort_project_master.csv')
for date in ['2023-03-31','2024-03-31']:
 operating=sum(float(r.allocation_stock_gbp_m) for _,r in s1.iterrows() if str(master.loc[master.project.eq(r.project),'actual_full_operation_date'].iloc[0])<=date)
 checks.append(dict(case='SSE',cutoff=date,total_million=s1.allocation_stock_gbp_m.sum(),currency='GBP',fully_operating_share_pct=100*operating/s1.allocation_stock_gbp_m.sum(),weight_basis='fixed_amounts_both_cutoffs',source_file=O+'sse/green_uop_2023_gb5_project_rows.csv;'+O+'sse/fixed_cohort_actual_milestones.csv',source_rows='2;3;4 / full_operation milestone rows'))
save(pd.DataFrame(checks),'recomputed_allocation_stage_comparison.csv')
assert len(matrix)==7 and matrix['case'].nunique()==7
assert pro.evidence_id.is_unique and not pro.source_urls.eq('').all()
assert len(pres)==33*len(families) and not pres.duplicated(['group_id','event_family']).any()
assert all(ct.documented_presence_groups+ct.not_documented_unknown_groups==ct.denominator_groups)
for rel,h in inputs.items():assert hashlib.sha256((BASE/rel).read_bytes()).hexdigest()==h
manifest={'handcoding_sha256':hashlib.sha256((OUT/'seven_history_handcoding.csv').read_bytes()).hexdigest(),'source_release':str(BASE),'source_status':'Core comparison uses frozen source-derived release records; two Enel closing releases were separately verified during this revision and recorded in supplemental_enel_ownership_sources.csv, not reverified by this script','inputs_sha256':inputs,'validation':{'passed':True,'broad_groups':37,'principal_groups':33,'proxy_extension_groups':4,'seven_histories':len(matrix),'event_families':len(families),'presence_rows':len(pres),'event_evidence_rows':len(ev),'all_source_hashes_unchanged':True,'zero_states_are_unknown_not_absence':True},'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.csv'))}}
(OUT/'validation_and_provenance.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['validation'],indent=2));print(compact.to_string(index=False))
