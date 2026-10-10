import csv,json,pathlib
P=pathlib.Path(__file__).parent
S={
'CLP_ESG24':'https://sustainability.clpgroup.com/en/2024/esg-data-hub',
'CLP_CA24':'https://www.clpgroup.com/content/dam/clp-group/channels/investor/document/2024_CA_Finance_Report_en.pdf.coredownload.pdf',
'CLP_SCOPE24':'https://sustainability.clpgroup.com/en/2024/about-this-report/reporting-scope-and-data-verification',
'CLP_ASSETS23':'https://www.clpgroup.com/content/dam/clp-group/channels/investor/document/3-3-financial-reports/2023/e_2023E114.pdf.coredownload.pdf',
'CLP_AR24':'https://www.clpgroup.com/content/dam/clp-group/channels/investor/document/3-3-financial-reports/2024/e_2024%20Annual%20Report.pdf.coredownload.pdf',
'CLP_ASSURE24':'https://www.clpgroup.com/content/dam/clp-group/channels/sustainability/document/sustainability-report/2024/CLP_Independent_Assurance_Statement_2024.pdf.coredownload.pdf',
'CLP_STRATEGY24':'https://www.clpgroup.com/content/dam/clp-group/channels/investor/document/3-3-financial-reports/2024/e_2024E109.pdf.coredownload.pdf'}
def save(name,rows):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Values transcribed from official 2024 retrospective equity-basis table. Years in source run 2024,2023,2022.
fuel=['total','coal','gas','nuclear','wind','hydro','solar','waste_to_energy','energy_storage','others']
gens=[[62383,30372,14154,12064,3056,1776,932,31,0,1],[62052,30364,13817,12128,3164,1626,920,32,0,0],[69726,37031,14435,12346,3146,1835,901,29,0,1]]
caps=[[17893,7222,4976,1600,2227,489,1013,10,147,210],[18123,8486,4938,1600,1827,489,548,7,18,210],[17970,8486,4934,1600,1680,489,554,7,10,210]]
facts=[]
for yi,y in enumerate([2024,2023,2022]):
 for measure,unit,vals,section in [('energy_sent_out','GWh',gens,'Energy sent out by asset type, on an equity basis'),('capacity','MW',caps,'Generation and energy storage capacity by asset type, on an equity basis')]:
  for f,v in zip(fuel,vals[yi]):
   facts.append(dict(fact_id=f'CLP_{y}_{measure}_{f}',issuer_id='CLP',fiscal_year=y,period_start=f'{y}-01-01',period_end=f'{y}-12-31',metric=measure,asset_type=f,value=v,unit=unit,ownership_basis='equity_share',measurement_basis='actual_net_sent_out' if measure=='energy_sent_out' else 'reported_capacity_stock',value_status='observed',source_id='CLP_ESG24',source_url=S['CLP_ESG24'],source_locator=section+f'; row={f}; column={y}',notes='Asset-type classification, not fuel-input apportionment. Coal can include biomass co-firing. Others not assigned to oil in this extract. Rounded integer data. 2024 report vintage; historical original-vintage cross-check pending.'))
save('issuer_year_facts.csv',facts)
# Full seven-bond cohort in report p5; loans excluded by design, not omitted accidentally.
bonds=[
('XS1648263926','CCGT_D1','Energy Transition','2017-07-25','USD',500,3453,449,3902,7,'excluded_gas_transition'),
('HK0000924818','CCGT_D1','Energy Transition','2023-05-10','CNY',300,0,339,339,7,'excluded_gas_transition'),
('202355293','WENT_LFG','New Energy','2019-07-09','HKD',170,120,50,170,7,'renewable_generation_boundary_case'),
('XS2190958301','HK_LNG','Energy Transition','2020-06-22','USD',350,1546,1167,2713,7,'excluded_gas_infrastructure'),
('XS2307742267','CCGT_D2','Energy Transition','2021-03-03','USD',300,2011,315,2326,8,'excluded_gas_transition'),
('HK0001015061','CCGT_D2','Energy Transition','2024-05-08','USD',70,0,548,548,8,'excluded_gas_transition'),
('XS2366836133','SMART_METERS','New Energy','2021-07-21','USD',100,0,777,777,8,'excluded_non_generation')]
rows=[]
for isin,project,label,date,cur,nom,new,ref,total,page,eligible in bonds:
 rows.append(dict(record_id='CLP24_'+isin,issuer_id='CLP',instrument_id=isin,instrument_type='bond',issuing_entity='CLP Power Hong Kong Financing Limited' if project=='SMART_METERS' else 'Castle Peak Power Finance Company Limited',project_id='CLP_'+project,report_year=2024,reporting_date='2024-12-31',project_country='Hong Kong SAR, China',label=label,issue_date=date,nominal_currency=cur,nominal_amount_million=nom,allocation_currency='HKD',allocated_finance_million=new,allocated_refinance_million=ref,allocated_total_million=total,unallocated_million=0,allocation_basis='cumulative_stock_at_reporting_date',eligibility=eligible,source_id='CLP_CA24',source_url=S['CLP_CA24'],source_locator=f'pp5,{page}; ISIN/Common Code {isin}; Finance/Refinance/Total columns',notes='Dash encoded as zero only in exhaustive allocation table where total finance+refinance and unallocated reconcile; original dash retained in cell provenance. No annual-flow inference.'))
save('bond_allocations_2024.csv',rows)
projects=[]
for p,tech,mw,gen,start,page in [('CCGT_D1','CCGT',550,None,'2020-10',10),('WENT_LFG','landfill_gas',10,42,'2020-03',11),('HK_LNG','LNG_terminal',None,None,'2023-07',12),('CCGT_D2','CCGT',600,None,'2024-04',13),('SMART_METERS','smart_metering',None,None,None,14)]:
 projects.append(dict(project_id='CLP_'+p,issuer_id='CLP',report_year=2024,technology=tech,capacity_mw=mw,capacity_status='observed_operational' if mw else 'not_applicable',actual_generation_gwh=gen,generation_status='observed' if gen is not None else ('not_reported' if tech=='CCGT' else 'not_applicable'),generation_basis='full_project_actual_generation' if gen else '',commissioning_date=start,date_precision='month' if start else '',commissioning_status='actual' if start else 'not_applicable',bond_attributed_generation_gwh=None,ownership_adjusted_generation_gwh=None,ownership_link_status='not_harmonized_to_group_equity',source_id='CLP_CA24',source_url=S['CLP_CA24'],source_locator=f'p{page}; Project Updates; '+p,notes='Do not infer actual generation from modeled avoided emissions. D2 capacity reported approximately 600MW. WENT10MW and42GWh are full-project values; no pro-rata allocation to bonds assumed.'))
save('project_delivery_2024.csv',projects)
# Field-level provenance for all finance/project numerics/strings, with exact source table columns.
prov=[]
for r in facts:
 prov.append(dict(table='issuer_year_facts',record_id=r['fact_id'],field='value',value=r['value'],unit=r['unit'],source_id=r['source_id'],source_url=r['source_url'],source_locator=r['source_locator'],coding='reported',raw_symbol=str(r['value'])))
for r in rows:
 for field in ['instrument_id','issue_date','nominal_currency','nominal_amount_million','allocated_finance_million','allocated_refinance_million','allocated_total_million','unallocated_million']:
  prov.append(dict(table='bond_allocations_2024',record_id=r['record_id'],field=field,value=r[field],unit='million currency units' if 'million' in field else '',source_id=r['source_id'],source_url=r['source_url'],source_locator=('p5 Summary of Climate Action Bonds' if field in ['instrument_id','issue_date','nominal_currency','nominal_amount_million'] else r['source_locator'])+'; column='+field,coding='reported_dash_interpreted_as_zero' if r[field]==0 else 'reported',raw_symbol='-' if r[field]==0 else str(r[field])))
for r in projects:
 for field in ['capacity_mw','actual_generation_gwh','commissioning_date']:
  prov.append(dict(table='project_delivery_2024',record_id=r['project_id'],field=field,value=r[field],unit='MW' if field=='capacity_mw' else ('GWh' if field=='actual_generation_gwh' else 'YYYY-MM'),source_id=r['source_id'],source_url=r['source_url'],source_locator=r['source_locator'],coding='reported' if r[field] is not None else 'not_reported_or_not_applicable',raw_symbol=str(r[field]) if r[field] is not None else ''))
save('cell_provenance.csv',prov)
save('source_manifest.csv',[dict(source_id=k,url=v,retrieved_utc='2026-10-10',format='HTML' if '/en/' in v and '.pdf' not in v else 'PDF',access_route='web tool official-source parsed content',local_full_download_status='HTTP403; not included',license='No open redistribution licence verified; derived factual data only') for k,v in S.items()])
print('CLP facts',len(facts),'bond cohort',len(rows),'projects',len(projects),'provenance',len(prov))
events=[]
for unit in ['A1','A2','A3']:
 events.append(dict(event_id='CLP_CPA_'+unit+'_2024',issuer_id='CLP',asset_id='CASTLE_PEAK_'+unit,event_date='2024-04',date_precision='month',event_type='physical_retirement',fuel='coal',gross_capacity_mw=350,ownership_fraction=0.70,equity_capacity_mw=245,equity_capacity_coding='derived:350*0.70',capacity_change_equity_mw=-245,source_url=S['CLP_SCOPE24'],source_locator='Reporting scope; explicit A1/A2/A3 retirement April 2024',capacity_source_url=S['CLP_ASSETS23'],capacity_source_locator='printed p294 (PDFp1), Castle Peak row and footnote2',notes='A1 in emergency reserve from2022-05-31; do not count that reserve transition as a prior permanent closure. 70% equity, not100% Scheme-of-Control long-term-purchase basis.'))
for plant,gross,equity in [('Heze_II',600,176),('Liaocheng_I',1200,353)]:
 events.append(dict(event_id='CLP_'+plant+'_2024',issuer_id='CLP',asset_id=plant,event_date='2024-09',date_precision='month',event_type='ownership_exit',fuel='coal',gross_capacity_mw=gross,ownership_fraction=0.294,equity_capacity_mw=equity,equity_capacity_coding='reported_rounded',capacity_change_equity_mw=-equity,source_url=S['CLP_AR24'],source_locator='printed p297, footnote15; early exit September2024 from Shandong Zhonghua',capacity_source_url=S['CLP_ASSETS23'],capacity_source_locator='printed p295 (PDFp2), '+plant+' row',notes='Ownership exit not physical retirement; exact legal consideration/recipient not verified. Capacity loss uses reported rounded equity176+353MW; unrounded529.2MW.'))
save('asset_event_ledger.csv',events)
bridges=[dict(issuer_id='CLP',year=2024,asset_type='coal',opening_equity_mw=8486,closing_equity_mw=7222,observed_change_mw=-1264,physical_retirement_mw=-735,ownership_exit_mw=-529,identified_net_change_mw=-1264,unexplained_residual_mw=0,status='reconciles_at_reported_integer_precision',source_ids='CLP_ESG24; CLP_SCOPE24; CLP_ASSETS23; CLP_AR24',notes='Event capacities rounded consistently with company table. Alternative exact-share exit529.2 yields residual+0.2MW within rounding. Generation change cannot be decomposed into utilization using end-year capacity only.')]
save('capacity_bridge.csv',bridges)
checks=[]
for yi,y in enumerate([2024,2023,2022]):
 for name,v in [('generation',gens[yi]),('capacity',caps[yi])]:
  residual=v[0]-sum(v[1:]);checks.append(dict(check_id=f'CLP_{y}_{name}_sum',status='PASS_rounding' if abs(residual)<=5 else 'FAIL',value=residual,expected='absolute residual <=5 integer units (9 rounded components plus total)',notes='Reported total minus sum of categories; tolerance is conservative rounding bound, not an error correction.'))
checks.append(dict(check_id='CLP_2024_coal_bridge',status='PASS',value=0,expected='zero at reported integer MW',notes='735MW equity physical closure plus529MW ownership exit; no inference of generation causality.'))
save('quality_checks.csv',checks)
(P/'quality_note.txt').write_text('CLP pilot scope: 2022–2024 equity-basis portfolio observations from2024 vintage; complete7 bond instrument cohort outstanding in2024 CAFF report,5 projects. Source report also has loans which are outside bond cohort. Primary renewable-electricity classification admits WENT landfill-gas only as an explicit boundary stratum; gas/LNG/smartmeters excluded from wind/solar core. Allocation amounts are cumulative stocks, never annual flows. Actual WENT output42GWh is full project and must not be mixed with equity-basis issuer totals or interpreted as bond-attributed output. Coal is plant-type generation and includes biomass cofiring. Reported renewable total5793GWh differs from rounded component sum5795; keep reported total when quoted, do not silently force closure. Three CastlePeak units are retiredApril2024; HezeII/LiaochengI ownershipexitSeptember2024 yields1264MW coal capacity decline after equity adjustment. This is an accounting case, no financing attribution or causal estimate. Annual utilization cannot be inferred from output/end-year-capacity ratios where closure/disposal occurs within year.2022/2023 finance-history extension inprogress. Full source file download403, official web parsed tables verified; no visual screenshot check completed for allCLP tables.\n')
# Consecutive official-report snapshots; each year's table independently checked.
allbonds=list(rows)
for year,excluded in [(2023,{'HK0001015061'}),(2022,{'HK0001015061','HK0000924818'})]:
 sid=f'CLP_CA{str(year)[2:]}'
 S[sid]=S['CLP_CA24'].replace('2024_CA',str(year)+'_CA')
 for orig in rows:
  if orig['instrument_id'] in excluded:continue
  r=dict(orig);r.update(record_id=f'CLP{year}_{orig["instrument_id"]}',report_year=year,reporting_date=f'{year}-12-31',source_id=sid,source_url=S[sid],source_locator=f'pp4–5; ISIN/Common Code {orig["instrument_id"]}; Finance/Refinance/Total columns')
  allbonds.append(r)
save('bond_allocations_2022_2024.csv',allbonds)
fullprojects=list(projects)
for year,gen in [(2022,43),(2023,46)]:
 for orig in projects:
  r=dict(orig);r.update(report_year=year,source_id=f'CLP_CA{str(year)[2:]}',source_url=S[f'CLP_CA{str(year)[2:]}'])
  p=r['project_id'].replace('CLP_','');pg={'CCGT_D1':7,'WENT_LFG':8,'HK_LNG':9,'CCGT_D2':10,'SMART_METERS':11}[p]
  r['source_locator']=f'p{pg}; Project Updates; {p}'
  if p=='WENT_LFG':r['actual_generation_gwh']=gen
  if p=='CCGT_D2':
   r.update(capacity_status='planned_under_construction',commissioning_date='2024',date_precision='year',commissioning_status='expected_at_report',actual_generation_gwh=None,generation_status='not_reported')
  if p=='HK_LNG' and year==2022:r.update(commissioning_date='2023',date_precision='year',commissioning_status='expected_at_report')
  fullprojects.append(r)
save('project_delivery_2022_2024.csv',fullprojects)
# Separate provenance table permits field-level audit without copying long source text.
longprov=list(prov)
for r in allbonds:
 if r['report_year']==2024:continue
 for field in ['instrument_id','issue_date','nominal_currency','nominal_amount_million','allocated_finance_million','allocated_refinance_million','allocated_total_million','unallocated_million']:
  longprov.append(dict(table='bond_allocations_2022_2024',record_id=r['record_id'],field=field,value=r[field],unit='million currency units' if 'million' in field else '',source_id=r['source_id'],source_url=r['source_url'],source_locator=r['source_locator']+'; column='+field,coding='reported_dash_interpreted_as_zero' if r[field]==0 else 'reported',raw_symbol='-' if r[field]==0 else str(r[field])))
for r in fullprojects:
 if r['report_year']==2024:continue
 for field in ['capacity_mw','actual_generation_gwh','commissioning_date']:
  longprov.append(dict(table='project_delivery_2022_2024',record_id=r['project_id']+'_'+str(r['report_year']),field=field,value=r[field],unit='MW' if field=='capacity_mw' else ('GWh' if field=='actual_generation_gwh' else 'date'),source_id=r['source_id'],source_url=r['source_url'],source_locator=r['source_locator'],coding='reported_'+r['commissioning_status'] if field=='commissioning_date' else ('reported' if r[field] is not None else 'not_reported_or_not_applicable'),raw_symbol=str(r[field]) if r[field] is not None else ''))
save('cell_provenance.csv',longprov)
save('source_manifest.csv',[dict(source_id=k,url=v,retrieved_utc='2026-10-10',format='HTML' if '/en/' in v and '.pdf' not in v else 'PDF',access_route='web tool official-source parsed content',local_full_download_status='not included; attempted CLP downloads returned HTTP403',license='No open redistribution licence verified; derived factual data only') for k,v in S.items()])
with (P/'quality_note.txt').open('a') as f:f.write('Extension completed:2022/2023/2024 CAFF report bond cohorts5/6/7 instruments;18 bond-year rows and15 project-year records. WENT full-project generation43/46/42GWh; cumulative170m HKD allocation unchanged across all3years, so do not report510m as new financing. 2023 D2 expected2024 operation independently confirmed on report p10; expected status never treated as realized.\n')
