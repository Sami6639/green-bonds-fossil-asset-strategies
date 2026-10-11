from pathlib import Path
import pandas as pd, json
P=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;O.mkdir(parents=True,exist_ok=True)
g=pd.read_csv(P/'analysis_panel/results/group_capacity_results.csv');s=pd.read_csv(P/'analysis_panel/screened_candidate_register.csv');a=pd.read_csv(P/'analysis_panel/results/finance_aligned_adjacent_robustness.csv');prov=pd.read_csv(P/'analysis_panel/results/capacity_endpoint_provenance.csv');fin=pd.read_csv(P/'analysis_panel/canonical_finance.csv');obs=pd.read_csv(P/'analysis_panel/canonical_observations.csv');audit=pd.read_csv(P/'inputs/25037bd32be1_independent_group_admission_audit.csv')
rows=[]
for _,r in s.iterrows():
 selected=g[g.group_id==r.group_id]; reasons=[]
 for x in json.loads(r.screening_raw_json):
  for k in ['missing_or_exclusion_reasons','notes','joint_analysis_gate','eligibility_status','rq3_finance_screen','gate_flags']:
   if x.get(k) and str(x[k]) not in reasons:reasons.append(str(x[k]))
 au=audit[audit.group_id==r.group_id]
 rows.append({'group_id':r.group_id,'issuer':r.issuer_label,'selection_status':('principal' if selected.iloc[0].principal_analysis_include else 'thermal_proxy_extension') if len(selected) else 'not_admitted_numeric_record' if r.has_numeric_observations else 'not_admitted_no_numeric_snapshot','same_window_pair':bool(len(selected) and pd.notna(selected.iloc[0].renewable_start_mw)),'audit_verdict':'; '.join(au.readiness_verdict),'recorded_reasons':'; '.join(reasons),'record_source':r.screening_record_sources})

for row in rows:
 if row['group_id']=='constellation_energy':
  row['recorded_reasons']=row['recorded_reasons'].replace('Allocation categories round1m above total.', 'Allocation categories sum USD1m above the reported total; signed residual -USD1m. Rounding is plausible but not source-explained and remains unreconciled.')
 if row['group_id']=='orsted' and not row['recorded_reasons']:
  row['recorded_reasons']='Reviewed fossil-capacity window has unresolved physical source IDs; no selected window after finance and physical gates.'
  row['record_source']+='; analysis_panel/reviewed_regional_window_panel.csv; analysis_panel/question_specific_cohort.csv'
pd.DataFrame(rows).to_csv(O/'selection_reconciliation.csv',index=False)
flow=[['WBA 2023 candidate frame',68,'Published company labels; historical 2019–2024 observations assessed retrospectively. Not a global population.'],['Remaining WBA screening records',37,'Overlapping first-pass records; not 37 additional candidates.'],['Additional coverage records',49,'Contains WBA and supplementary names; not 49 additional independent groups.'],['Detailed candidate register',64,'Distinct canonical candidate IDs; different coverage from the 68-name frame.'],['Detailed candidate IDs with numeric records',49,'Includes 37 admitted groups and 12 not admitted.'],['Detailed candidate IDs without numeric snapshot',15,'No numeric extraction does not prove ineligibility.'],['Not admitted from detailed register',27,'12 with numeric records + 15 without; reasons include unresolved records and explicit exclusions.'],['Admitted contextual groups',37,'33 fuel-identified principal scopes + 4 unsplit-thermal proxies.'],['Principal groups',33,'Includes ESB coal-plus-gas subset; ESB same-window renewable aggregate unresolved.'],['Principal paired groups',32,'33 minus ESB; missing renewable capacity remains missing.']]
pd.DataFrame(flow,columns=['stage','recorded_count','interpretation']).to_csv(O/'selection_flow.csv',index=False)
# Illustrative same-source aggregate fossil timing comparisons: all retained finance-aligned adjacent rows for these five groups, nested within their principal windows.
groups=['ameren','aes_corporation','wec_energy_group','nextera_energy','shikoku_electric_power'];metrics=['fossil_capacity','capacity_fossil_derived','fossil_installed_capacity'];t=[];finance_ids=set();obsids=set()
for _,r in a[a.group_id.isin(groups)&a.metric.isin(metrics)].iterrows():
 z=g[g.group_id==r.group_id].iloc[0];start=r.start_upper;end=r.end_upper
 if start<z.start_date or end>z.end_date:continue
 ids=str(r.finance_linked_record_ids).split(';');f=fin[fin.record_id.isin(ids)];finance_ids.update(ids);obsids.update([r.start_record_id,r.end_record_id]);delta=r.capacity_end-r.capacity_start
 t.append({'group_id':r.group_id,'issuer':r.issuer_label,'main_start':z.start_date,'main_end':z.end_date,'main_start_mw':z.fossil_start_mw,'main_end_mw':z.fossil_end_mw,'main_delta_mw':z.fossil_delta_mw,'main_direction':z.fossil_direction,'short_start':start,'short_end':end,'source_start_lower':r.start_lower,'source_start_upper':r.start_upper,'source_end_lower':r.end_lower,'source_end_upper':r.end_upper,'short_start_mw':r.capacity_start,'short_end_mw':r.capacity_end,'short_delta_mw':delta,'short_direction':'increase' if delta>0 else 'decrease' if delta<0 else 'unchanged_at_reported_precision','finance_date_bounds':'; '.join(sorted(set(f.date_lower+' to '+f.date_upper))),'finance_classes':r.finance_linked_classes,'finance_ids':r.finance_linked_record_ids,'start_record_id':r.start_record_id,'end_record_id':r.end_record_id,'ownership_basis':r.ownership_basis,'scope':r.operating_scope,'source_url':r.physical_source_url,'caution':'Descriptive aggregate fossil comparison, not a new paired renewable/fossil test. Calendar-year labels use year-end headings in the reviewed source; original date bounds retained. Not a post-issue causal design.'})
pd.DataFrame(t).to_csv(O/'timing_comparison.csv',index=False);fin[fin.record_id.isin(finance_ids)].to_csv(O/'timing_finance_provenance.csv',index=False);obs[obs.record_id.isin(obsids)].to_csv(O/'timing_capacity_provenance.csv',index=False)
# Economic examples have consistent reporting bases, not necessarily a constant asset perimeter.
e=g[g.group_id.isin(['ameren','jsw_energy','wec_energy_group'])];cols=['group_id','issuer_label','start_date','end_date','physical_basis','fossil_start_mw','fossil_end_mw','fossil_delta_mw','fossil_change_pct','renewable_start_mw','renewable_end_mw','renewable_delta_mw','renewable_change_pct','caveats'];e[cols].to_csv(O/'economic_magnitude_examples.csv',index=False);prov[prov.group_id.isin(e.group_id)].to_csv(O/'economic_magnitude_provenance.csv',index=False)
summary={'version':'BSE-2026-10-11-r3','contextual':37,'principal':33,'principal_paired':32,'selected_timing_groups':len(set(x['group_id'] for x in t)),'selected_timing_rows':len(t),'economic_example_groups':len(e),'finance_aligned_category_rows':len(a),'finance_aligned_distinct_groups':int(a.group_id.nunique()),'main_elapsed_pre_finance_groups':int((g.antecedent_fraction_lower>0).sum()),'principal_elapsed_pre_finance_groups':int(((g.antecedent_fraction_lower>0)&g.principal_analysis_include).sum()),'no_new_causal_estimates':True,'selection_candidate_denominator_caution':'The 68-name WBA frame and 64-ID detailed candidate register are overlapping but nonnested. No summed or global unique screened denominator is asserted.'};(O/'technical_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(pd.DataFrame(t)[['issuer','main_delta_mw','short_start','short_end','short_delta_mw','finance_date_bounds']].to_string(index=False))
checks=[]
def check(name,actual,expected):
 ok=abs(actual-expected)<1e-8 if isinstance(expected,(int,float)) else actual==expected
 checks.append({'check':name,'actual':actual,'expected':expected,'passed':bool(ok)})
check('contextual groups',len(g),37);check('principal groups',int(g.principal_analysis_include.sum()),33);check('principal pairs',int((g.principal_analysis_include&g.renewable_start_mw.notna()&g.renewable_end_mw.notna()).sum()),32);check('Dominion excluded from main panel','dominion_energy' not in set(g.group_id),True)
bands=pd.read_csv(P/'analysis_panel/results/sign_band_direction_summary.csv')
for band,down,up in [(0,18,8),(.5,13,8),(1,13,8)]:
 b=bands[(bands.cohort=='principal_fuel_identified_groups')&(bands.boundary=='reported_source_boundary')&(bands.band_pct_of_opening_capacity==band)]
 for direction,n in [('decrease',down),('increase',up)]:check(f'band {band}: renewable increase / fossil {direction}',int(b[(b.RE_direction=='increase')&(b.fossil_direction==direction)].group_rows.sum()),n)
stages=pd.read_csv(P/'strategy_comparison/recomputed_allocation_stage_comparison.csv')
for case,date,value in [('SSE','2023-03-31',6.84),('SSE','2024-03-31',69.48),('WEC','2024-06-30',33.46)]:
 check(case+' operating share '+date,round(float(stages[(stages['case']==case)&(stages.cutoff==date)].iloc[0].fully_operating_share_pct),2),value)
r=pd.read_csv(P/'nested_histories/original_three/enel/green_reallocations_2023.csv');positive=r[r.allocation_change_EUR_m>0]
check('Enel 2019 bond reassignment EUR million',float(positive[positive.issue_year==2019].allocation_change_EUR_m.sum()),156.86);check('Enel all-issue reassignment EUR million',float(positive.allocation_change_EUR_m.sum()),229.60)
check('all detailed candidates accounted',len(rows),64);check('nonadmitted detailed candidates',sum(x['selection_status'].startswith('not_admitted') for x in rows),27)
result={'version':'BSE-2026-10-11-r3','passed':all(x['passed'] for x in checks),'checks':checks,'limits':'Computational and recorded-source consistency checks. Not independent verification of all original reports or causal inference.'};(O/'invariant_checks.json').write_text(json.dumps(result,indent=2));assert result['passed'],result
# Expose portable source locators rather than historical execution-machine paths.
manifest=json.loads((P/'inputs/snapshot_manifest.json').read_text())
for path in O.glob('*.csv'):
 text=path.read_text()
 for entry in sorted(manifest,key=lambda e:len(e['original_path']),reverse=True):
  text=text.replace(entry['original_path'],'inputs/'+Path(entry['frozen_path']).name)
 path.write_text(text)
