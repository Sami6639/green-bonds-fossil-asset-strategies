import csv,json
from pathlib import Path
P=Path(__file__).parent;S=P/'sources'; urls={x['source_id']:x['url'] for x in csv.DictReader((P/'source_manifest.csv').open())}
def write(n,r):
 with (P/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
# Fixed crosswalk. Distinct original report lines remain separate; no false plant deduplication across issues.
ids=['whitney_hill','aurora_wind','cimarron_bend_3_phase_1','cohuna','girgarre','italian_hydro_aggregate_8','riverview','castle_rock_ridge_2','magdalena_2','amistad_2','amistad_3','amistad_4','dolores','high_lonesome_1_2','roadrunner','kafireas','alta_farms_2','seven_cowboy']
names=['Whitney Hill','Aurora Wind','Cimarron Bend 3 phase I','Cohuna','Girgarre','Various Italian hydro projects (8)','Riverview','Castle Rock Ridge 2','Magdalena 2','Amistad II','Amistad III','Amistad IV','Dolores','High Lonesome I+II','Roadrunner','Kafireas','Alta Farms II','Seven Cowboy']
countries=['USA','USA','USA','Australia','Australia','Italy','Canada','Canada','Mexico','Mexico','Mexico','Mexico','Mexico','USA','USA','Greece','USA','USA']
tech=['wind','wind','wind','solar','solar','hydro','wind','wind','solar','wind','wind','wind','wind','wind','solar','wind','wind','wind']
a19=[10,10,4,31,7,10,81,23,112,55,59,50,192,75,141,126,None,None]
cap={2019:[66,299,199,34,96,40,115,31,220,100,100,149,244,501,497,154,None,None],2020:[66,299,199,34,None,40,105,29,220,100,108,162,274,501,497,154,None,None],2021:[66,298.8,198.84,34.3,None,40,105,29.4,220,100,108,162,273.9,501,497.46,154,None,None],2022:[66,299,199,34,None,33,105,29,220,100,108,162,274,500,497,154,None,None],2023:[66,299,199,None,None,33,105,29,220,100,108,162,274,500,497,None,201,302],2024:[66,299,199,None,None,33,105,29,220,103,108,162,274,504,497,None,201,302]}
initial_status=['In Operation','Under Construction','Hand Over to Do','Under Construction','Ready to Build','','Under Construction','Under Construction','In Operation','In Operation','Under Construction','Under Construction','Under Construction','In Operation','Under Construction','In Operation','','']
initial_dates=['2019-12','2020-10','2020-11','2020-02','2021-02','','2020-04','2020-02','2019-09','2019-12','2020-02','2020-04','2020-03','2019-12','2020-06','2019-10','','']
actual_dates=['2019-12','2020-12','2020-12','2020-06','','','2020-04','2020-03','2019-09','2019-12','2020-02','2020-12','2020-05','2019-12','2020-06','2019-10','2022-12','2022-10']
R=[]; by={}
for y in range(2019,2025):
 amounts=a19.copy()
 if y>=2020:amounts[4]=None;amounts[11]=57
 if y>=2023:amounts[3]=None;amounts[15]=None;amounts[16]=55;amounts[17]=101
 by[y]={ids[i]:v for i,v in enumerate(amounts) if v is not None}
 for i,pid in enumerate(ids):
  present=amounts[i] is not None
  if present:
   rawstatus=initial_status[i] if y==2019 else '' if i==5 and y<=2021 else 'In Operation'
   date=initial_dates[i] if y==2019 else actual_dates[i]
   status='operating' if rawstatus.lower()=='in operation' else 'construction' if rawstatus=='Under Construction' else 'ready_to_build' if rawstatus=='Ready to Build' else 'status_not_disclosed' if not rawstatus else 'handover_pending_source_wording'
   datebasis='reported_actual_first_production_not_necessarily_full_COD' if status=='operating' and date else 'expected_future_date' if date else 'not_disclosed'
  else:
   rawstatus='';status='not_in_current_allocation_table';date='';datebasis='not_applicable';
  reason=''
  if not present:
   reason='awaiting_reauthorization; allocation_transferred_to_Amistad_IV' if i==4 and y>=2020 else 'deconsolidated; proceeds_reassigned_in_2023' if i in [3,15] and y>=2023 else 'not_yet_in_2019_issue_allocation_pool'
  R.append(dict(issuer='Enel',instrument_cohort='2019 green use-of-proceeds bond ONLY',report_year=y,project_id=pid,canonical_project_name=names[i],country=countries[i],technology=tech[i],row_type='aggregate_8_unnamed_projects' if i==5 else 'named_project',underlying_project_count_reported=8 if i==5 else 1,present_in_allocation_table=int(present),allocation_EUR_m_reported=amounts[i],allocation_basis='reported_stock_in_2019_issue_column; not_annual_flow',allocation_unit_precision_EUR_m=1 if present else None,project_status_reported=rawstatus,project_status_normalized=status,operation_date_reported=date,operation_date_semantics=datebasis,capacity_MW_reported=cap[y][i],absence_reason=reason,physical_exit_established='no',source_id=f'green_bond_{y}',source_pdf_page=7 if y==2024 else 13,source_url=urls[f'green_bond_{y}'],identity_note='Castle/Castel spellings and High Lonesome/High Lonesome I+II linked by location/technology/date/allocation; aggregate internal identities remain unknown',financing_use_axis='finance_or_refinance_capitalized_expenditure; new_money_share_unverified'))
write('green_2019_issue_full_annual_panel.csv',R)
# Transition statistics: all21? named rows observed; no zero inferred for physical production or capacity.
T=[]
for ya,yb in [(2019,2020),(2020,2021),(2021,2022),(2022,2023),(2023,2024),(2019,2024)]:
 a,b=by[ya],by[yb];sa,sb=set(a),set(b);joint=sa&sb;ex=sa-sb;ent=sb-sa
 overlap=sum(min(a[x],b[x]) for x in joint);sameids_old=sum(a[x] for x in joint);sameids_new=sum(b[x] for x in joint)
 aggregate='italian_hydro_aggregate_8';namedjoint=joint-{aggregate};overlap_named=sum(min(a[x],b[x]) for x in namedjoint)
 den=sum(a.values());n_old=len(a)-1+8;n_new=len(b)-1+8
 T.append(dict(from_report_year=ya,to_report_year=yb,comparison='adjacent' if yb==ya+1 else 'endpoint',old_reported_project_lines=len(a),new_reported_project_lines=len(b),retained_reported_lines=len(joint),exited_reported_lines=len(ex),entered_reported_lines=len(ent),retained_named_projects_excluding_aggregate=len(namedjoint),old_underlying_project_count_reported=n_old,new_underlying_project_count_reported=n_new,underlying_identity_retention_count_lower=len(namedjoint),underlying_identity_retention_count_upper=len(namedjoint)+8,underlying_identity_retention_share_lower=len(namedjoint)/n_old,underlying_identity_retention_share_upper=(len(namedjoint)+8)/n_old,old_sum_rounded_line_allocations_EUR_m=den,new_sum_rounded_line_allocations_EUR_m=sum(b.values()),old_printed_total_EUR_m=986,new_printed_total_EUR_m=986,exiting_allocations_old_EUR_m=sum(a[x] for x in ex),entering_allocations_new_EUR_m=sum(b[x] for x in ent),retained_ids_old_allocation_EUR_m=sameids_old,retained_ids_new_allocation_EUR_m=sameids_new,allocation_overlap_min_by_reported_line_EUR_m=overlap,allocation_overlap_share_of_old_line_sum=overlap/den,identity_verified_allocation_overlap_lower_EUR_m=overlap_named,identity_conditional_allocation_overlap_upper_EUR_m=overlap,identity_overlap_share_lower=overlap_named/den,identity_overlap_share_upper=overlap/den,entered_ids=';'.join(sorted(ent)),exited_ids=';'.join(sorted(ex)),boundary='Ranges reflect unknown identities within8-project hydro aggregate, not statistical uncertainty or physical retirement. Named-line capacities may also represent phases/repowering. Monetary ratios use rounded line sums; totals and published precise reallocation notes retained separately.'))
write('green_2019_issue_pool_continuity.csv',T)
# Report-year summary plus rounding preservation.
Q=[]
for y,a in by.items():
 rr=[r for r in R if r['report_year']==y and r['present_in_allocation_table']]
 st={s:sum(r['project_status_normalized']==s for r in rr) for s in ['operating','construction','ready_to_build','handover_pending_source_wording','status_not_disclosed']}
 Q.append(dict(report_year=y,reported_project_lines=len(a),named_project_lines=len(a)-1,aggregate_lines=1,unnamed_projects_in_aggregate=8,source_reported_total_EUR_m=986,source_summary_total_EUR_m=985.6 if y==2019 else 986,sum_rounded_project_lines_EUR_m=sum(a.values()),line_sum_minus_printed_total_EUR_m=sum(a.values())-986,operating_lines=st['operating'],construction_lines=st['construction'],ready_to_build_lines=st['ready_to_build'],handover_pending_lines=st['handover_pending_source_wording'],status_not_disclosed_lines=st['status_not_disclosed'],source_id=f'green_bond_{y}',source_pdf_page=7 if y==2024 else 13,source_url=urls[f'green_bond_{y}']))
write('green_2019_issue_annual_summary.csv',Q)
# Exactly scoped reallocation disclosures, distinct from rounded table-cell arithmetic.
F=[dict(disclosure_report_year=2020,source_project='Girgarre',destination_project='Amistad IV',allocation_moved_EUR_m=7,precision='approximately',issue_year=2019,source_pdf_page=13,source_url=urls['green_bond_2020'],interpretation='existing project receives allocation after excluded project awaits reauthorization; not bond issuance'),dict(disclosure_report_year=2023,source_project='Cohuna; Kafireas',destination_project='Alta Farms II; Seven Cowboy',allocation_moved_EUR_m=156.86,precision='two decimals as source; removed30.93+125.93; assigned55.38+101.48',issue_year=2019,source_pdf_page=4,source_url=urls['green_bond_2023'],interpretation='deconsolidation-related pool replacement; receiving plants were already operating in2022; do not attribute contemporaneous new capacity')]
write('green_2019_issue_reassignment_disclosures.csv',F)
# Preserve source Table A pages and notes; this full panel supersedes initial endpoint-only extraction.
for y in range(2019,2025):
 pg=7 if y==2024 else 13;txt=(S/f'green_bond_{y}.txt').read_text().split('\f')[pg-1]
 (P/'source_cells'/f'green_2019_issue_snapshot_{y}_pdfpage_{pg}.txt').write_text(txt)
assert len(R)==108
assert len(by[2019])==16 and all(len(by[y])==15 for y in range(2020,2025))
assert set(by[2020])==set(by[2021])==set(by[2022])
assert set(by[2023])==set(by[2024])
assert sum(by[2019].values())==986 and sum(by[2023].values())==985
print(json.dumps({'rows':len(R),'present_rows':sum(r['present_in_allocation_table'] for r in R),'transitions':T,'summary':Q},indent=2))
