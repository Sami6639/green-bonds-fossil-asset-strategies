import csv,json,hashlib,re
from pathlib import Path
P=Path(__file__).parent; S=P/'sources'
def url(n):
 if (P/'followup_source_urls.json').exists():
  extra=json.loads((P/'followup_source_urls.json').read_text())
  if n in extra:return extra[n]
 if n.startswith('annual'):return 'https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2024/annuali/en/integrated-annual-report_2024.pdf'
 y=n[-4:];fn=f'green-bond-report-{y}_en.pdf' if n.startswith('green_bond') else f'sustainability-report_{y}.pdf'
 return f'https://www.enel.com/content/dam/enel-com/documenti/investitori/sostenibilita/{y}/{fn}'
def write(n,rs):
 with (P/n).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
# Direct reported data, no equity-share conversion. Earlier years retain 2021 disclosure vintage, 2022-23 retain 2023 vintage.
fuels=['coal','ccgt','oil_gas','nuclear','hydro','wind','geothermal','biomass_other','solar','renewable_total','fossil_total','total']
cap={2019:[11695,14991,12211,3318,27830,10327,878,5,3094,42134,38897,84349],2020:[8903,15009,11711,3328,27820,12412,882,5,3897,45016,35623,83967],2021:[6910,15039,11715,3328,27847,14903,915,6,6395,50066,33664,87058],2022:[6590,13894,7204,3328,28355,15735,931,6,8534,53561,27689,84578],2023:[4627,11983,5942,3328,28340,15853,931,6,10407,55536,22553,81417],2024:[4627,11622,4766,3328,27697,15739,860,6,12306,56608,21015,80951]}
gen={2019:[37592,44980,20887,26279,62580,26668,6149,21,3974,99391,103459,229129],2020:[13155,43353,19401,25839,62437,30992,6167,1,5763,105360,75909,207108],2021:[13858,51718,22709,25504,57001,37791,6086,40,7899,108817,88285,222605],2022:[19722,54436,14652,26508,51728,43255,6117,43,11306,112448,88811,227767],2023:[10755,36705,8021,24865,60991,45339,6001,42,14613,126985,55480,207330],2024:[2377,26410,5606,24152,64358,46078,5500,36,17356,133328,34393,191873]}
rows=[]
for y in cap:
 n='sustainability_2021' if y<=2021 else 'sustainability_2023' if y<=2023 else 'annual_2024'
 for metric,d,unit in [('net_efficient_capacity',cap,'MW'),('net_generation',gen,'GWh')]:
  page=375 if y<=2021 and unit=='MW' else 376 if y<=2021 else 373 if y<=2023 and unit=='MW' else 374 if y<=2023 else '178;184' if unit=='MW' else '177;183'
  for fuel,val in zip(fuels,d[y]):
   derived=y==2024 and fuel in ['fossil_total','total']
   rows.append(dict(issuer='Enel',year=y,metric=metric,fuel=fuel,value=val,unit=unit,scope='Reported consolidated Enel group; not equity-weighted; changing perimeter',source_id=n,source_pdf_page=page,source_url=url(n),source_cell=f'{fuel} row / {y} column',value_type='derived_sum_fuel_cells' if derived else 'reported',boundary_note='Rounding differences retained; nuclear excluded from fossil; Oil/Gas mixes fuels; renewable_total differs by 1 MW/GWh across vintages in 2023. 2024 derived total excludes BESS.'))
write('issuer_fuel_year_2019_2024.csv',rows)
# Full 2019-bond project enumeration at initial and latest vintage; do not sum project MW across issues.
projects=[('Whitney Hill','USA','wind',66,66,10,10,'operating','2019-12','2019-12',163),('Aurora Wind','USA','wind',299,299,10,10,'construction','2020-10','2020-12',993),('Cimarron Bend 3 phase I','USA','wind',199,199,4,4,'Hand Over to Do','2020-11','2020-12',539),('Cohuna','Australia','solar',34,None,31,None,'construction','2020-02','2020-06',None),('Girgarre','Australia','solar',96,None,7,None,'ready to build','2021-02','',None),('Various Italian hydro projects (8)','Italy','hydro',40,33,10,10,'unspecified','','',1567),('Riverview','Canada','wind',115,105,81,81,'construction','2020-04','2020-04',332),('Castle Rock Ridge 2','Canada','wind',31,29,23,23,'construction','2020-02','2020-03',98),('Magdalena 2','Mexico','solar',220,220,112,112,'operating','2019-09','2019-09',499),('Amistad II','Mexico','wind',100,103,55,55,'operating','2019-12','2019-12',277),('Amistad III','Mexico','wind',100,108,59,59,'construction','2020-02','2020-02',19),('Amistad IV','Mexico','wind',149,162,50,57,'construction','2020-04','2020-12',None),('Dolores','Mexico','wind',244,274,192,192,'construction','2020-03','2020-05',539),('High Lonesome I+II','USA','wind',501,504,75,75,'operating','2019-12','2019-12',1181),('Roadrunner','USA','solar',497,497,141,141,'construction','2020-06','2020-06',1005),('Kafireas','Greece','wind',154,None,126,None,'operating','2019-10','2019-10',None),('Alta Farms II','USA','wind',None,201,None,55,'not in original cohort','','2022-12',582),('Seven Cowboy','USA','wind',None,302,None,101,'not in original cohort','','2022-10',989)]
r=[]
for name,country,tech,c19,c24,a19,a24,st,d19,d24,g24 in projects:
 for y,c,a,date,status in [(2019,c19,a19,d19,st),(2024,c24,a24,d24,'operating' if c24 else 'not in allocation table')]:
  r.append(dict(issuer='Enel',issue_year=2019,report_year=y,project=name,country=country,technology=tech,capacity_MW=c,allocated_EUR_m=a,financial_use='finance_or_refinance_capitalized_costs; project-level split unverified',allocation_type='outstanding_allocation_stock_not_annual_flow',project_status=status,reported_operation_date=date,date_semantics='planned_if_not_operating' if y==2019 and status!='operating' else 'reported_actual',generation_GWh=g24 if y==2024 else None,generation_status='reported' if y==2024 and g24 is not None else 'missing_not_zero',source_id=f'green_bond_{y}',source_pdf_page='13' if y==2019 else '7;8;5',source_url=url(f'green_bond_{y}'),boundary_note='Cohuna/Kafireas removed in 2023; Girgarre absent by 2020, reason not yet verified. Italian hydro aggregated repowering generation non-comparable. High Lonesome/Roadrunner/Seven Cowboy also allocated under 2018 issue; avoid duplicate physical capacity.'))
write('green_2019_issue_project_vintages.csv',r)
# Reallocation event amounts from 2023 supporting notes.
r=[]
for project,issue,val,event in [('Cremzow',2018,-9.24,'deconsolidated_removed'),('Kafireas',2018,-63.50,'deconsolidated_removed'),('Kafireas',2019,-125.93,'deconsolidated_removed'),('Cohuna',2019,-30.93,'deconsolidated_removed'),('Seven Cowboy',2018,72.74,'replacement_allocation'),('Seven Cowboy',2019,101.48,'replacement_allocation'),('Alta Farms II',2019,55.38,'replacement_allocation')]:
 r.append(dict(issuer='Enel',year=2023,issue_year=issue,project=project,allocation_change_EUR_m=val,event=event,source_id='green_bond_2023',source_pdf_page=4,source_url=url('green_bond_2023'),note='Same total allocation moved between projects, not new cash issue; amounts rounded.'))
write('green_reallocations_2023.csv',r)
r=[]
for y,v in {2019:[1237,575,665,985.6],2020:[1238,575,665,986],2021:[1238,575,665,986],2022:[1238,575,665,986],2023:[1238,575,666,986],2024:[None,575,665,986]}.items():
 for (issue,cat),val in zip([(2017,'renewables'),(2018,'renewables'),(2018,'grids_excluded'),(2019,'renewables')],v):
  r.append(dict(issuer='Enel',report_year=y,issue_year=issue,category=cat,allocated_EUR_m=val,value_status='not_in_2024_report_do_not_code_zero' if val is None else 'reported_rounded',stock_flow='allocation_stock_repeated_not_new_year_flow',source_id=f'green_bond_{y}',source_pdf_page={2019:4,2020:5,2021:6,2022:6,2023:6,2024:5}[y],source_url=url(f'green_bond_{y}'),note='2023 renewable 2018 = 502 + 73; printed 2018 grand total 1240 vs category sum 1241 reflects disclosed rounding discrepancy; preserve.'))
write('green_allocations_by_issue_vintage.csv',r)
# Selected original-cohort generation series: measured annual observations only, preserve missing marks.
r=[]
vals={'Whitney Hill':[None,189,204.77,207.54,175,163],'Aurora Wind':[None,None,730.11,1184.80,946,993],'Cimarron Bend 3 phase I':[None,None,804.02,811.92,696,539],'Cohuna':[None,None,10.66,18.44,None,None],'Various Italian hydro projects (8)':[None,None,None,None,None,1567]}
for project,vs in vals.items():
 for y,v in zip(range(2019,2025),vs):
  r.append(dict(issuer='Enel',project=project,year=y,annual_generation_GWh=v,value_status='reported' if v is not None else 'missing_or_nonseparable_or_removed_not_zero',source_id=f'green_bond_{y}',source_pdf_page=8 if y==2024 else 13,source_url=url(f'green_bond_{y}'),boundary_note='2019/2020 reports substitute forecasts for recently commissioned plants; forecasts excluded. 2024 cumulative roll-forward and Italian hydro perimeter require reconciliation.'))
write('project_generation_selected_2019_2024.csv',r)
# Source manifest and raw page corpus for verification.
manifest=[]
for f in sorted(S.glob('*.pdf')):
 manifest.append(dict(source_id=f.stem,url=url(f.stem),local_file=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),retrieved_utc_date='2026-10-10',document_type='official issuer report'))
write('source_manifest.csv',manifest)
print('Created core files',len(rows),'fuel-year cells')
# Event ledger: dates retain stated precision; this is an auditable seed ledger, not an exhaustive bridge.
events=[
('2019','decision','Bocamina I / II','Chile','coal',None,'planned closures 2023 / 2040','Enel Chile controlled group','','sustainability_2019',118,'2019 government agreement; historical baseline plan, later accelerated'),
('2019-10-01','sale','Reftinskaya GRES','Russia','coal',None,'sold; physical retirement not established','Enel Russia controlled group','JSC Kuzbassenergo','sustainability_2019',248,'Capacity/generation and EBITDA deconsolidated; licenses, personnel and maintenance responsibilities temporarily retained; never code sale as retirement'),
('2019-12-31','closure','Tarapaca','Chile','coal',None,'closed','Enel Chile controlled group','','sustainability_2022',197,'Date stated retrospectively; 2019 report p118 already confirms December closure'),
('2020-06','closure','Compostilla / Teruel','Spain','coal',None,'closed','Endesa controlled group','','sustainability_2022',197,'2020 report PDF p108 independently lists both shutdowns; event MW not extracted'),
('2020','closure','Brindisi Federico II unit 2','Italy','coal',None,'closed','Enel group','','sustainability_2020',108,'Source reports shutdown during 2020; no exact date extracted'),
('2020-12-31/2021-01','closure','Bocamina I','Chile','coal',128,'closed','Enel Chile controlled group','','sustainability_2023',301,'Boundary-date discrepancy retained: 2020 report says closed Dec31; 2023 says beginning 2021; do not count twice'),
('2021-12','closure','Litoral','Spain','coal',None,'closed','Endesa controlled group','','sustainability_2022',197,'2021 report PDF p228 confirms closure; exact MW not extracted'),
('2022-09-30','closure','Bocamina II','Chile','coal',350,'permanently disconnected','Enel Chile controlled group','','sustainability_2022',202,'MW confirmed 2023 report p301; 2020 plan scheduled May2022, subsequent authorization delay documented in 2022 p151'),
('2022-10-12','sale','Enel Russia portfolio','Russia','mixed_fossil_and_renewable',None,'disposed; physical status not traced','Enel group','','sustainability_2022',454,'Consolidation boundary change; assets, buyer and MW pending separate annual-report extraction'),
('2023','sale','Argentine thermoelectric generation assets','Argentina','mixed_fossil',None,'divested; physical status not traced','Enel group','','sustainability_2023',370,'2024 report p177 identifies Costanera and Central Dock Sud sold in first half2023; no physical-retirement inference'),
('2023','closure','Fusina','Italy','coal',500,'taken out of service','Enel group','','sustainability_2023',109,'Rounded 0.5GW; keep separate from exact annual coal-MW change and 2024 unit decommissioning narrative'),
('2023','closure','As Pontes','Spain','coal',1400,'taken out of service','Endesa controlled group','','sustainability_2023',109,'Rounded1.4GW; 2022 p151 says closure requested2019 for2021 but authorization withheld; critical regulatory timing'),
('2023-11-22','agreement','Enel Generacion Peru / Compania Energetica Veracruz','Peru','mixed_generation',None,'sale agreement','Enel Peru via Enel Americas','Niagara Energy SAC','annual_2024',212,'Pre-completion agreement date stated in2024 annual report'),
('2024-05-10','sale_completed','Enel Generacion Peru / Compania Energetica Veracruz','Peru','mixed_generation',None,'all held stakes sold; physical operation not traced','Enel Peru via Enel Americas','Niagara Energy SAC','annual_2024',212,'Do not infer physical retirement; thermal and renewable assets both leave corporate scope'),
('2024-06-26','minority_sale_and_investment_plan','Enel Libra Flexsys OCGT portfolio','Italy','gas',900,'three renovation projects; not verified commissioned','Enel retains control (51%)','Sosteneo Energy Transition 1 (49%)','annual_2024',212,'Continues full consolidation;900MW is project portfolio, not observed new capacity added in2024'),
('2024','dispatch_change','Consolidated coal fleet','Group','coal',4627,'year-end MW unchanged; generation falls','Enel consolidated group','','annual_2024','177;178','2024 GWh2377 vs2023 10755;2023 Italian preventive gas-consumption measures explain much of decline; no coal retirement in aggregate stock2024')]
r=[]
for date,etype,asset,country,fuel,mw,status,owner,buyer,src,page,note in events:
 r.append(dict(issuer='Enel',event_date=date,event_type=etype,asset=asset,country=country,fuel=fuel,MW=mw,MW_basis='reported_project_or_rounded_asset_not_ownership_adjusted' if mw is not None else 'not_extracted',status=status,ownership_scope=owner,buyer=buyer,source_id=src,source_pdf_page=page,source_url=url(src),boundary_note=note))
write('fossil_asset_events_seed.csv',r)
# Correct summary page locators and record the explicitly explained 2020 replacement.
f=P/'green_allocations_by_issue_vintage.csv'
rs=list(csv.DictReader(f.open()))
for x in rs:
 if x['report_year'] in ['2019','2020']: x['source_pdf_page']='6'
write(f.name,rs)
f=P/'green_2019_issue_project_vintages.csv';rs=list(csv.DictReader(f.open()))
for x in rs:x['boundary_note']=x['boundary_note'].replace('Girgarre absent by 2020, reason not yet verified.','Girgarre awaiting reauthorization: about EUR7m moved to Amistad IV in2020 (2020 report PDF p13 footnote1).')
write(f.name,rs)
# Compact data-quality checks do not silently correct printed totals.
checks=[]
for y in cap:
 for metric,d in [('capacity_MW',cap),('generation_GWh',gen)]:
  a=d[y];checks.append(dict(check='fossil_components_minus_reported_total',year=y,metric=metric,residual=sum(a[:3])-a[10],interpretation='retain printed rounding; not a closure bridge'))
for project,prev,annual,cum in [('Whitney Hill',776,163,1111),('Aurora Wind',2861,993,4873),('Cimarron Bend 3 phase I',2312,539,3439),('Alta Farms II',358,582,1522)]:
 checks.append(dict(check='cumulative_rollforward_requires_scope_reconciliation_'+project,year=2024,metric='GWh',residual=cum-prev-annual,interpretation='unexplained vintage/perimeter/period difference; not proven report error; quarantine cumulative arithmetic'))
write('validation_checks.csv',checks)
