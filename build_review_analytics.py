"""Source-linked descriptive additions and canonical manuscript tables. Offline only."""
from pathlib import Path
import json,hashlib,shutil,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-utility')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/utility-cache')
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
P=Path(__file__).parent; O=P/'main_exhibits'; I=P/'review_revision_inputs'
def rd(s):return pd.read_csv(P/s,keep_default_na=False)
def save(d,n):d.to_csv(O/n,index=False)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'utility-review-20261010'})
# GB5 only: financial stock weights are joined to physical state at each fiscal cutoff.
links=rd('sse/fixed_cohort_bond_project_links.csv'); links=links[links.bond_group=='GB5'].copy()
links['allocation_stock_gbp_m']=pd.to_numeric(links.allocation_stock_gbp_m)
snap=rd('sse/fixed_cohort_annual_disclosure_snapshots.csv');snap=snap[snap.disclosure_year.isin([2023,2024])].copy()
snap=snap.rename(columns={'disclosure_year':'report_year','source_url':'status_source_url','source_locator':'status_source_locator'})
m=links.merge(snap,on=['project_id','report_year'],validate='one_to_one')
def classify_maturity(row):
 stage=row.get('project_stage','')
 value=pd.to_numeric(row.get('qualifying_output_gwh',''),errors='coerce')
 if stage=='operational': return 'Full operation'
 if stage=='construction_with_generation':
  return 'Construction with generation' if pd.isna(value) or value>0 else 'Maturity unresolved'
 if stage=='construction':
  if pd.isna(value): return 'Maturity unresolved'
  if value==0: return 'Construction; no generation'
  if value>0: return 'Construction with generation'
 return 'Maturity unresolved'
m['maturity_class']=m.apply(classify_maturity,axis=1)
# Regression fixtures: missing production is not evidence of zero production.
fixtures=[({'project_stage':'construction','qualifying_output_gwh':''},'Maturity unresolved'),({'project_stage':'construction','qualifying_output_gwh':None},'Maturity unresolved'),({'project_stage':'construction','qualifying_output_gwh':0},'Construction; no generation'),({'project_stage':'construction','qualifying_output_gwh':1},'Construction with generation'),({'project_stage':'construction_with_generation','qualifying_output_gwh':0},'Maturity unresolved')]
fixture_rows=[]
for data,expected in fixtures:
 actual=classify_maturity(data); assert actual==expected
 fixture_rows.append(dict(project_stage=data['project_stage'],qualifying_output_gwh=data['qualifying_output_gwh'],expected=expected,actual=actual,status='PASS'))
pd.DataFrame(fixture_rows).to_csv(O/'maturity_missing_zero_regression_tests.csv',index=False)
assert m.maturity_class.notna().all()
m['gb5_allocation_total_gbp_m']=m.groupby('report_year').allocation_stock_gbp_m.transform('sum')
m['allocation_stock_share']=m.allocation_stock_gbp_m/m.gb5_allocation_total_gbp_m
m['allocation_stock_share_pct']=100*m.allocation_stock_share
m['measure_limit']='Share of GB5 allocated financial stock, not capacity, generation, total project investment, new annual finance or financing effect.'
save(m,'sse_gb5_maturity_project_weights.csv')
control=m[m.project_id=='SSE_GORDONBUSH_EXT'].copy()
control['supported_comparison']='Endpoint allocation £37.2m, qualifying capacity 38 MW, reported SSE share 100%, and full-operation class unchanged; no inference of absence of all within-year changes.'
assert len(control)==2 and (control.allocation_stock_gbp_m==37.2).all() and (pd.to_numeric(control.disclosed_full_capacity_mw)==38).all() and (pd.to_numeric(control.disclosed_sse_share)==1).all() and (control.project_stage=='operational').all()
save(control,'sse_gordonbush_endpoint_consistency.csv')
mat=m.groupby(['report_year','evidence_date_or_period','maturity_class'],sort=False).agg(allocation_stock_gbp_m=('allocation_stock_gbp_m','sum'),gb5_allocation_total_gbp_m=('gb5_allocation_total_gbp_m','first'),project_ids=('project_id',lambda x:'; '.join(x))).reset_index()
mat['allocation_stock_share_pct']=100*mat.allocation_stock_gbp_m/mat.gb5_allocation_total_gbp_m
save(mat,'sse_gb5_maturity_stock_analysis.csv')
assert len(m)==6 and all(abs(x-543.9)<1e-8 for x in m.groupby('report_year').allocation_stock_gbp_m.sum())
# Fuel-sensitive bridge; exclude multifuel, retain signed reporting-scope contributions.
fuel=rd('sse/capacity_2019_2024_fuel_stratified.csv').set_index('fiscal_year_end')
ev=rd('sse/capacity_2019_2024_event_contributions.csv')
foss=ev[ev.fuel!='multifuel'].copy(); save(foss,'sse_fossil_only_event_contributions.csv')
sums=foss.groupby('event_type').signed_reported_portfolio_mw.sum()
parts=[('Physical closures',sums.get('physical_retirement',0)+sums.get('physical_closure',0)),('Commissioning',sums.get('physical_commissioning',0)),('Acquisition',sums.get('ownership_acquisition',0)),('Reporting / segment changes',sums.get('reporting_scope_change',0)+sums.get('internal_segment_transfer',0))]
opening=float(fuel.loc[2019,'fossil_categories_capacity_mw']);closing=float(fuel.loc[2024,'fossil_categories_capacity_mw'])
assert abs(opening+sum(v for _,v in parts)-closing)<1e-8
br=rd('main_exhibits/appendix_capacity_bridge_components.csv')
br=br[br.scope!='Reported Thermal fossil categories; multifuel excluded'].copy()
new=[]
for c,v in [('Opening stock',opening)]+parts+[('Residual',0),('Closing stock',closing)]:
 new.append(dict(issuer='SSE',scope='Reported Thermal fossil categories; multifuel excluded',period='FY2019 to FY2024 (31 March)',component=c,value_mw=v,source_table='sse/capacity_2019_2024_event_contributions.csv; sse/capacity_2019_2024_fuel_stratified.csv',warning='Fossil categories inside the reported Thermal boundary only; retains segment changes; gas/oil increase is not wholly new build.'))
br=pd.concat([br,pd.DataFrame(new)],ignore_index=True);save(br,'appendix_capacity_bridge_components.csv')
gas0=float(fuel.loc[2019,'gas_oil_subtotal_mw']);gas1=float(fuel.loc[2024,'gas_oil_subtotal_mw'])
gas_events=foss[foss.fuel!='coal'].copy()
assert abs(gas0+gas_events.signed_reported_portfolio_mw.sum()-gas1)<1e-8
save(gas_events,'sse_gas_oil_event_contributions.csv')
sensitivity=pd.DataFrame([dict(boundary='Reported Thermal total',opening_mw=float(fuel.loc[2019,'reported_thermal_total_mw']),closing_mw=float(fuel.loc[2024,'reported_thermal_total_mw'])),dict(boundary='Thermal fossil categories; multifuel excluded',opening_mw=opening,closing_mw=closing),dict(boundary='Gas/oil within Thermal',opening_mw=gas0,closing_mw=gas1)])
sensitivity['net_change_mw']=sensitivity.closing_mw-sensitivity.opening_mw
sensitivity['net_change_pct']=100*sensitivity.net_change_mw/sensitivity.opening_mw
save(sensitivity,'sse_capacity_boundary_sensitivity.csv')
# Enel: retain instrument-vintage separation, including the explicitly labelled 2018 companion.
en=rd('enel/green_reallocations_2023.csv');a=en[en.event=='replacement_allocation'].groupby('issue_year').allocation_change_EUR_m.sum()
companion=pd.DataFrame([{'issue_year':y,'allocation_reassigned_eur_m':float(a[y]),'scope':'Main focal instrument' if y==2019 else 'Companion instrument; excluded from main 2019 numerator','source_url':en.source_url.iloc[0],'pdf_page':4} for y in [2019,2018]])
save(companion,'enel_reallocation_by_issue_companion.csv')
# Canonical four-column Table 3. Word, CSV and workbook consume exactly these strings.
rows=[['Iberdrola: 2019 hybrid, 2019–2024','€800m in each of six reports; two names retained','East Anglia ONE entered operation in 2020; project monetary weights not disclosed','Name/total continuity is observed; monetary composition and financing additionality remain unidentified.'],['Enel: 2019 issue, 2023 replacement',f'€{a[2019]:.2f}m reassigned within the existing issue','Kafireas and Cohuna removed after deconsolidation; Alta Farms II and Seven Cowboy added','The eligible pool changed. The separate 2018 companion (€72.74m) is excluded from this numerator.']]
for year in [2023,2024]:
 q=mat[mat.report_year==year].set_index('maturity_class')
 def f(c):
  z=q.loc[c];return f'£{z.allocation_stock_gbp_m:.1f}m ({z.allocation_stock_share_pct:.2f}%)'
 if year==2023:
  physical='Full operation: '+f('Full operation')+'; construction with generation: '+f('Construction with generation')+'; no generation: '+f('Construction; no generation')
  interp='Seagreen remained under construction but reported 345.3 GWh of qualifying generation; it is not a zero-generation class.'
 else:
  physical='Full operation: '+f('Full operation')+'; construction with no generation: '+f('Construction; no generation')
  interp='Seagreen had reached full operation; Viking had not. Shares describe the unchanged allocation stock, not annual new finance.'
 rows.append([f'SSE GB5: 31 March {year}','£543.9m; identical three project allocations',physical,interp])
t3=pd.DataFrame(rows,columns=['Instrument and observation','Financial observation','Physical evidence','Interpretation']);save(t3,'table3_finance_delivery_comparison.csv')
# Canonical Table 4: each row retains its own accounting boundary.
def n(v):return f'{v:,.0f}'
def signed(v):return f'{v:+,.0f}'.replace('-', '−')
rows=[]
for issuer,scope in [('Iberdrola','Reported gas + cogeneration + coal'),('SSE','Reported Thermal portfolio'),('SSE','Reported Thermal fossil categories; multifuel excluded'),('CLP','Equity coal; reserve-inclusive')]:
 g=br[(br.issuer==issuer)&(br.scope==scope)];d=dict(zip(g.component,g.value_mw));op=d['Opening stock'];cl=d['Closing stock']
 if issuer=='Iberdrola':mech=f"{signed(d['Physical closures'])} closures; {signed(d['Installed / commissioned'])} installed/commissioned; {signed(d['Existing-asset acquisition / rights'])} acquisition/rights; {signed(d['Ownership disposal'])} disposal; {signed(d['Uprating'])} uprating; {signed(d['Residual'])} residual";lim='Reported technology capacity includes pre-COD and lease-ambiguous assets; cogeneration fuel unresolved.'
 elif scope=='Reported Thermal portfolio':mech=f"{signed(d['Physical closures'])} closures; {signed(d['Commissioning'])} commissioning; {signed(d['Acquisition'])} acquisition; {signed(d['Ownership disposal'])} disposal; {signed(d['Reporting / segment changes'])} scope/segment";lim='Opening stock and later commissioning/disposal include multifuel; this is a segment portfolio.'
 elif issuer=='SSE':mech=f"{signed(d['Physical closures'])} closures; {signed(d['Commissioning'])} new gas; {signed(d['Acquisition'])} acquisition; {signed(d['Reporting / segment changes'])} scope/segment";lim=f'Multifuel excluded. Gas/oil rises from {n(gas0)} to {n(gas1)} MW (+{n(gas1-gas0)}); the increase is not wholly new build.'
 else:mech=f"{signed(d['Physical closures'])} closures; {signed(d['Ownership / contract exits'])} ownership/contract exits; {signed(d['Uprating'])} uprating; {signed(d['Residual'])} residual";lim='Equity coal includes reserve; 245 MW of the closures entered reserve in 2022.'
 rows.append([issuer+' — '+scope,f'{n(op)} → {n(cl)} MW',mech,lim])
save(pd.DataFrame(rows,columns=['Issuer and boundary','2019–2024 endpoints','Signed identified contributions (MW)','Interpretive boundary']),'table4_capacity_bridge_summary.csv')
# Four readable within-case panels, not a common-scale ranking.
short={'Opening stock':'Opening','Closing stock':'Closing','Physical closures':'Physical\nclosures','Installed / commissioned':'Installed /\ncommissioned','Existing-asset acquisition / rights':'Acquisition /\nrights','Ownership disposal':'Ownership\ndisposal','Uprating':'Uprating','Residual':'Residual','Commissioning':'Commissioning','Acquisition':'Acquisition','Reporting / segment changes':'Scope /\nsegment','Ownership / contract exits':'Ownership /\ncontract exits'}
order=[('Iberdrola','Reported gas + cogeneration + coal'),('SSE','Reported Thermal portfolio'),('SSE','Reported Thermal fossil categories; multifuel excluded'),('CLP','Equity coal; reserve-inclusive')]
fig,axes=plt.subplots(4,1,figsize=(6.27,8.0))
for ax,(issuer,scope) in zip(axes,order):
 g=br[(br.issuer==issuer)&(br.scope==scope)]; running=0
 for j,r in enumerate(g.itertuples()):
  endpoint=r.component in ['Opening stock','Closing stock'];base=0 if endpoint else min(running,running+r.value_mw);h=r.value_mw if endpoint else abs(r.value_mw)
  ax.bar(j,h,bottom=base,width=.65,color='#385770' if endpoint else '#9d659c' if r.component=='Residual' else '#af6549' if r.value_mw<0 else '#47857a')
  ax.text(j,base+h+max(g.value_mw)*.035,f'{r.value_mw:,.0f}' if endpoint else f'{r.value_mw:+,.0f}',ha='center',fontsize=7)
  if not endpoint and not h:ax.plot([j-.3,j+.3],[running,running],color='#9d659c',lw=1.5)
  running=r.value_mw if endpoint else running+r.value_mw
 ax.set_xticks(range(len(g)),[short[x] for x in g.component],fontsize=6.5);ax.tick_params(axis='x',length=0)
 ax.set_title(issuer+' | '+('Fossil-only sensitivity (multifuel excluded)' if 'excluded' in scope else scope),loc='left',fontsize=9,pad=5)
 ax.set_ylim(0,max(g.value_mw)*1.32);ax.set_ylabel('MW',fontsize=8);ax.tick_params(axis='y',labelsize=7);ax.grid(axis='y',alpha=.13)
fig.subplots_adjust(left=.10,right=.99,top=.97,bottom=.045,hspace=.65)
fig.savefig(O/'figure3_capacity_bridges.png',dpi=240);fig.savefig(O/'figure3_capacity_bridges.svg',metadata={'Date':None});plt.close(fig)
# Final candidate frame and fixed inference matrices are human-audited inputs.
for src,dst in [('table1_main_case_screen.csv','table1_case_coverage.csv'),('table2_main_core_assessment.csv','table2_claim_evidence_synthesis.csv'),('three_core_evidence_matrix.csv','three_core_evidence_matrix.csv')]:
 if (I/src).exists():shutil.copy2(I/src,O/dst)
# EN-G21 traceability is checked against the retained extracted panel.
panel=rd('enel/green_2019_issue_full_annual_panel.csv');p21=panel[(panel.report_year==2021)&(panel.present_in_allocation_table==1)]
assert pd.to_numeric(p21.allocation_EUR_m_reported).sum()==986
assert len(p21)==15 and (p21.source_id=='green_bond_2021').all() and (p21.source_pdf_page==13).all()
source21=rd('enel/source_manifest.csv');source21=source21[source21.source_id=='green_bond_2021'].iloc[0]
audit={'source_code':'EN-G21','title':'Enel Green Bond Report 2021','source_url':source21.url,'pdf_page_1_based':13,'printed_page':13,'panel_file':'enel/green_2019_issue_full_annual_panel.csv','present_report_entries':len(p21),'rounded_allocation_row_sum_eur_m':float(pd.to_numeric(p21.allocation_EUR_m_reported).sum()),'panel_source_id':'green_bond_2021','source_pdf_sha256':source21.sha256,'affected_comparisons':['2020–2021','2021–2022'],'required_visible_locations':['Appendix A','Appendix pool-continuity source note','Table 2 source note where annual identity history is referenced'],'audit_scope':'Existing source page and panel source IDs; report vintage does not establish original public disclosure day.'}
(O/'enel_2021_source_chain_audit.json').write_text(json.dumps(audit,indent=2))
# Machine-readable display contract; numbering and captions are first-appearance ordered.
captions={1:'Selected event timelines. Calendar dates differ from issuer fiscal observations. Horizontal ranges alone represent imprecise dates; points represent exact reported dates. Investment-decision dates may be retrospectively reported and are not automatically contemporaneous public disclosures. Sequencing does not establish financing causation.',2:'Enel allocation replacement by issue. The 2019 focal issue reassigned €156.86m in 2023, equivalent to 15.9% of its original €985.6m allocation stock; the separate 2018 companion reassigned €72.74m. These are replacements within existing allocation stocks. The combined €229.60m is not the 2019 numerator. Source: EN-G23, PDF p.4.',3:'Within-case capacity bridges and SSE boundary sensitivity. Iberdrola and CLP use calendar-year endpoints; SSE uses 31 March fiscal endpoints. Scales and accounting boundaries differ. SSE Thermal and fossil-only rows are separate; the narrower bridge excludes multifuel but retains reporting changes. CLP closures are reserve-inclusive. Residual closure does not establish exhaustive gross-event coverage. Enel is omitted because unit-level closure attribution is incomplete.'}
(O/'FIGURE_CAPTIONS.txt').write_text('\n\n'.join(f'Figure {i}. {s}' for i,s in captions.items())+'\n')
files=['table1_case_coverage.csv','table2_claim_evidence_synthesis.csv','table3_finance_delivery_comparison.csv','table4_capacity_bridge_summary.csv']
titles=['Candidate selection and analytical roles','Common claim–evidence assessment','Allocation records and physical project maturity','Capacity bridges under explicit reporting boundaries']
table_notes={1:'Retrospective, purposive nine-candidate screen, reviewed 10 October 2026. Analytical role, disclosure resolution and completed extraction are separate. Viable additional cases are not ineligible; this is not a representative nine-firm panel. Full sources and unresolved extraction appear in the final screening register.',2:'These are analyst-formulated assessment conditions, not attributed errors or promises by issuers, investors or prior literature. Supported concerns only the named dimension and observation window; unidentified is not contradicted. Enel identity history is source-linked to EN-G19, EN-G20, EN-G21, EN-G22, EN-G23 and EN-G24. Detailed dimensional claims and annual continuity are provided in the data appendix.',3:'SSE percentages are financial allocation-stock weights at 31 March, not shares of generation, capacity, project investment or finance effects. Construction with generation is distinct from no generation. Enel’s €156.86m uses the 2019 instrument only; its 15.91518% comparison uses the original €985.6m allocation base. The rounded €986m report total is not substituted for that denominator. Sources: IB-GREEN matched hybrid tables (2019–2024); SS-G23/SS-G24 Table 6 and actual milestones; EN-G23 PDF p.4.',4:'Iberdrola and CLP endpoints are calendar year-end; SSE endpoints are fiscal year-end, 31 March. Positive removal magnitudes in the accounting identity appear here as negative signed contributions. Different scales and ownership/fuel/segment boundaries preclude pooled climate-performance comparison. A closed bridge does not exclude unidentified offsetting gross events.'}
contract={'table_order':[],'figures':[{'number':i,'file':f'figure{i}_'+['selected_timelines','allocation_replacement','capacity_bridges'][i-1]+'.png','caption':captions[i]} for i in [1,2,3]],'figure_caption_placement':'below_image','table_cells_rule':'Copy header and data strings exactly from canonical CSVs; do not silently shorten or replace values.'}
for i,(file,title) in enumerate(zip(files,titles),1):
 if (O/file).exists():
  d=rd('main_exhibits/'+file);contract['table_order'].append({'number':i,'title':title,'file':file,'headers':list(d.columns),'rows':d.astype(str).values.tolist(),'note':table_notes[i]})
(O/'canonical_manuscript_exhibits.json').write_text(json.dumps(contract,indent=2,ensure_ascii=False))
summary={'sse_gb5':mat.to_dict('records'),'sse_capacity_sensitivity':sensitivity.to_dict('records'),'enel_2019_reallocation_eur_m':float(a[2019]),'enel_2018_companion_eur_m':float(a[2018]),'enel_2021_source_chain':audit,'no_regression':True,'new_analyses_use_existing_csvs':True}
(O/'review_revision_computed_results.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
checks=[{'check':'SSE_GB5_each_snapshot_543_9','pass':bool((m.groupby('report_year').allocation_stock_gbp_m.sum().round(8)==543.9).all())},{'check':'SSE_maturity_shares_sum_100','pass':bool((mat.groupby('report_year').allocation_stock_share_pct.sum().round(8)==100).all())},{'check':'SSE_2023_Seagreen_partial_generation','pass':bool(float(m[(m.project_id=='SSE_SEAGREEN1')&(m.report_year==2023)].qualifying_output_gwh.iloc[0])==345.3)},{'check':'SSE_fossil_bridge_closes','pass':bool(abs(opening+sum(v for _,v in parts)-closing)<1e-8)},{'check':'SSE_gas_oil_bridge_closes','pass':bool(abs(gas0+gas_events.signed_reported_portfolio_mw.sum()-gas1)<1e-8)},{'check':'Enel_2019_reassigned_156_86','pass':bool(abs(a[2019]-156.86)<1e-8)},{'check':'Enel_2021_source_chain_15_entries','pass':len(p21)==15}]
assert all(c['pass'] for c in checks)
(O/'new_analysis_validation.json').write_text(json.dumps(checks,indent=2))
(O/'README.txt').write_text('FINAL EXHIBITS\n\nRun python run_analysis.py at package root. Four canonical table CSVs and their exact headers/cells are specified in canonical_manuscript_exhibits.json. Figure captions are below-image text for Word. Detailed annual report-entry continuity is appendix_pool_continuity.csv; its counts are not plant survival. All displayed Table 3 values concern the selected instrument: Enel 2019 only, with 2018 retained as a separately labelled companion. SSE maturity shares weight financial stock by contemporaneous physical class; construction with generation is separate from non-generation. The capacity sensitivity excludes multifuel without redefining the original Thermal row. Source and final output manifests are written only after all files and workbook are complete.\n')
print(json.dumps({'sse_maturity':mat.to_dict('records'),'sse_gas_oil_net_change':gas1-gas0,'enel_2019':float(a[2019]),'canonical_tables':len(contract['table_order'])},indent=2))
