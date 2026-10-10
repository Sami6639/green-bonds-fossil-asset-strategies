from pathlib import Path
import csv, hashlib, json, collections
R=Path('/workspace/shared/bse_utility_pilot_20261010/iberdrola')
OLD=Path('/workspace/shared/manuscript_upgrade_20261010/data_feasibility')
S={
'annual2024':dict(title='Iberdrola Annual Financial Report 2024',year=2024,url='https://www.iberdrola.com/documents/20125/4778712/gsm25-annual-accounts-consolidated-2024.pdf',pdf=OLD/'iberdrola_annual_2024.pdf',txt=R/'annual2024.txt'),
'annual2023':dict(title='Iberdrola Annual Financial Report 2023',year=2023,url='https://www.iberdrola.com/documents/20125/3643974/gsm24-annual-accounts-consolidated-2023.pdf',pdf=R/'annual2023.pdf',txt=R/'annual2023.txt'),
'green2024':dict(title='Iberdrola Green financing returns report 2024',year=2024,url='https://www.iberdrola.com/documents/20125/42169/green-financing-returns-report-2024.pdf',pdf=OLD/'iberdrola_2024.pdf',txt=OLD/'iberdrola_2024.txt'),
'green2023':dict(title='Iberdrola Green financing returns report 2023',year=2023,url='https://www.iberdrola.com/documents/20125/42169/green-financing-returns-report-2023.pdf',pdf=R/'green2023.pdf',txt=R/'green2023.txt'),
'green2022':dict(title='Iberdrola Green financing returns report 2022',year=2022,url='https://www.iberdrola.com/documents/20125/42169/Green_financing_returns_report_2022.pdf',pdf=R/'green2022.pdf',txt=R/'green2022.txt')}
def write(name, rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with (R/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def prov(s,p,table,row,field,printed=None):
 return dict(source_id=s,source_url=S[s]['url'],pdf_page_1_based=p,printed_page=p if printed is None else printed,source_table=table,source_row=row,source_field=field)
manifest=[]
for s,v in S.items():
 manifest.append(dict(source_id=s,title=v['title'],report_year=v['year'],source_url=v['url'],retrieved_date_utc='2026-10-10',local_pdf=str(v['pdf']),sha256=hashlib.sha256(v['pdf'].read_bytes()).hexdigest(),pages=len(v['txt'].read_text().split('\f'))-1,extraction_method='pdftotext -layout; manually transcribed tables; selected-page visual QA',source_author='Iberdrola, S.A.'))
write('source_manifest.csv',manifest)
# Order is deliberately the reported technology taxonomy, including subtotals.
tech=['Renewables','Onshore wind','Offshore wind','Hydroelectric','Mini hydroelectric','Solar and other','Batteries','Thermal','Nuclear','Gas combined cycles','Cogeneration','Total Group']
# triples: consolidated, proportional investees, published group total. The latter is not 100% gross physical capacity.
data={
(2022,'capacity_mw'):[(37351,2715,40066),(19720,509,20229),(1258,0,1258),(11664,2184,13848),(254,2,256),(4244,20,4264),(211,0,211),(20442,255,20697),(3177,0,3177),(16131,204,16335),(1134,51,1185),(57793,2970,60763)],
(2022,'actual_generation_gwh'):[(65472,9274,74746),(44345,1072,45417),(4497,0,4497),(12331,8171,20502),(415,5,420),(3811,26,3837),(73,0,73),(88084,197,88281),(23886,0,23886),(58565,7,58572),(5633,190,5823),(153556,9471,163027)],
(2023,'capacity_mw'):[(40564,1624,42188),(20435,450,20885),(1754,39,1793),(11980,1123,13103),(244,0,244),(5940,12,5952),(211,0,211),(20442,255,20697),(3177,0,3177),(16131,204,16335),(1134,51,1185),(61006,1879,62885)],
(2023,'actual_generation_gwh'):[(72980,6568,79548),(43409,891,44300),(5073,0,5073),(18405,5650,24055),(402,0,402),(5613,27,5640),(78,0,78),(88804,246,89050),(23784,0,23784),(59154,6,59160),(5866,240,6106),(161784,6814,168598)],
(2024,'capacity_mw'):[(42751,1728,44479),(20298,450,20748),(2230,143,2373),(11977,1123,13100),(234,0,234),(7784,12,7796),(228,0,228),(11936,255,12191),(3177,0,3177),(7654,204,7858),(1105,51,1156),(54687,1983,56670)],
(2024,'actual_generation_gwh'):[(80158,3182,83340),(43724,851,44575),(5783,39,5822),(23654,2267,25921),(429,0,429),(6496,25,6521),(72,0,72),(48922,240,49162),(22589,0,22589),(19658,5,19663),(6675,235,6910),(129080,3422,132502)]}
scopes=['consolidated_at_EBITDA_level','proportional_managed_investees','group_total_consolidated_plus_proportional_investees']
facts=[]
for (yr,metric),triples in data.items():
 s='annual2023' if yr==2022 else 'annual2024';p=(257 if metric=='capacity_mw' else 258) if yr==2022 else (288 if metric=='capacity_mw' else 289);printed=p-(3 if yr==2022 else 11)
 for t,vals in zip(tech,triples):
  for j,value in enumerate(vals):
   notes=[]
   if t=='Thermal': notes.append('Subtotal includes nuclear; must not be classified as fossil.')
   if t=='Solar and other' and metric=='capacity_mw':notes.append('Solar capacity in MWdc, unlike generic MW.')
   if t=='Batteries':notes.append('Reported taxonomy retained; annual2024 p285 narrative calls corresponding US 72 GWh fuel-cell production. Not a verified pure-storage/fossil-free category.')
   if yr==2022:notes.append('2022 comparative as published in 2023 report; no like-for-like restatement to 2024 accounting perimeter established.')
   if yr==2023 and metric=='actual_generation_gwh':notes.append('Latest 2024 comparator retained; 240 GWh cogeneration shifted from consolidated to investees versus 2023 publication.')
   facts.append(dict(issuer='Iberdrola',observation_year=yr,metric=metric,value=value,unit='MW' if metric=='capacity_mw' else 'GWh',reported_technology=t,aggregation_role='total' if t=='Total Group' else 'subtotal' if t in ['Renewables','Thermal'] else 'component',ownership_scope=scopes[j],timing='year_end_stock' if metric=='capacity_mw' else 'calendar_year_actual_flow',report_year=S[s]['year'],notes=' '.join(notes),**prov(s,p,'2.2.2 Electricity production and retail / By technology',t,f'31.12.{yr} / '+scopes[j],printed)))
write('issuer_year_technology_facts.csv',facts)
# Comparators from original 2023 report, distinct from the latest-value core file.
rev=[]
for t,old,new in [('Cogeneration',(6106,0,6106),(5866,240,6106)),('Thermal',(89044,6,89050),(88804,246,89050)),('Total Group',(162024,6574,168598),(161784,6814,168598))]:
 for j in range(3):rev.append(dict(observation_year=2023,metric='actual_generation_gwh',reported_technology=t,ownership_scope=scopes[j],earlier_value=old[j],latest_value=new[j],difference=new[j]-old[j],earlier_source_url=S['annual2023']['url'],earlier_pdf_page_1_based=258,earlier_printed_page=255,latest_source_url=S['annual2024']['url'],latest_pdf_page_1_based=289,latest_printed_page=278,source_table='By technology / 31.12.2023',source_field=scopes[j],interpretation='Published consolidated/investee classification differs; total preserved. Cause not independently established.'))
write('comparative_revision_audit.csv',rev)
# New 2024 holding bond cohort: eight ISINs, six transactions (two dual-tranche).
instruments=[
('XS2748213290','2024-01-16','EUR',700,700,5,76,700,100,512,693,91299,'Renewables','hybrid','2024-03-22','refinancing_existing_green_hybrid'),
('CH1357852685','2024-07-11','CHF',190,203,5,79,196,0,0,0,0,'Networks (Smart Grid projects)','senior','not_reported','financing_future_network_capex'),
('CH1357852677','2024-07-11','CHF',145,154,5,80,149,0,0,0,0,'Networks (Smart Grid projects)','senior','not_reported','financing_future_network_capex'),
('XS2861000235','2024-07-18','EUR',750,750,5,81,750,100,410,947,353656,'Renewables','senior','mixed_see_project_rows','refinancing_existing_renewables'),
('XS2930118265','2024-10-31','GBP',500,602,6,83,602,0,169,0,0,'Renewables','senior','not_reported','financing_future_offshore_wind_capex'),
('AU3CB0315802','2024-11-28','AUD',350,209,6,84,216,0,244,0,0,'Renewables','senior','not_reported','financing_future_solar_battery_capex'),
('AU3CB0315810','2024-11-28','AUD',400,239,6,85,247,0,275,0,0,'Renewables','senior','not_reported','financing_future_solar_battery_capex'),
('XS2949317676','2024-11-28','EUR',800,800,6,87,800,100,0,0,0,'Renewables','hybrid','2025-02-07','refinancing_existing_green_hybrid_after_year_end')]
IF=[]
def addif(isin,yr,name,value,unit,page,table,field=None,notes='',cohort='2024_new_holding_bonds'):
 IF.append(dict(issuer='Iberdrola Finanzas',instrument_isin=isin,report_year=yr,cohort=cohort,field=name,value=value,unit=unit,notes=notes,**prov('green'+str(yr),page,table,isin,field or name)))
for isin,date,ccy,nom,eur,ip,ap,allocated,refi,cap,gen,co2,area,kind,allocation_start,purpose in instruments:
 for k,v,u in [('issue_date',date,'ISO_date'),('currency',ccy,''),('nominal_original_currency_million',nom,ccy+' million'),('nominal_eur_year_end_fx_million',eur,'EUR million'),('instrument_type',kind,'')]:
  addif(isin,2024,k,v,u,ip,'Green bonds instrument inventory',notes='Original non-EUR nominal from footnotes 9–11; EUR equivalent at 2024 closing FX. Hybrid dates shown in maturity column are call dates, not final maturity.')
 for k,v,u in [('investment_area',area,''),('investment_allocated_million',allocated,'EUR million'),('refinancing_share_at_issuance_pct',refi,'%'),('reported_attributable_capacity_mw',cap,'MW'),('actual_attributable_generation_gwh',gen,'GWh'),('avoided_co2_tonnes',co2,'tonnes CO2')]:
  note='Reported investment assigned to instrument, including forward-designated spending; neither annual expenditure flow nor verified deployed capex. Never sum repeated report-year allocations as fresh financing.' if k=='investment_allocated_million' else 'Attribution follows financing share and assignment period; not whole-project or whole-firm output. Capacity may describe future assets; see projects.'
  if isin=='XS2949317676': note+=' No returns attributed before 7 February 2025 reassignment despite 2017/2019 start-up years and EUR800m allocation.'
  addif(isin,2024,k,v,u,ap,'Total amount invested by area / Sustainability indicators',notes=note)
 addif(isin,2024,'allocation_effective_date_or_period',allocation_start,'',75 if isin=='XS2748213290' else ap,'Allocated assets / footnotes',notes='not_reported is missing, not issue-date assumption.')
 addif(isin,2024,'financing_purpose',purpose,'',6 if isin!='XS2949317676' and not isin.startswith('AU') else 7,'2024 new bond narrative',notes='Categorisation from stated use of proceeds; not a causal treatment indicator.')
# Complete project rows for all eight ISINs. No per-project money/generation split is disclosed in these instrument tables.
projects=[]
def P(isin,name,tech,location,start,mw,page,alloc_from='',alloc_to='',yr=2024,cohort='2024_new_holding_bonds',status=''):
 if not status:status='expected_future_startup' if start.startswith('>') or int(start[:4])>yr else 'reported_historical_or_current_startup_not_verified_final_COD'
 projects.append(dict(report_year=yr,instrument_isin=isin,cohort=cohort,project_name_reported=name,technology_reported=tech,country_reported=location,startup_year_reported=start,startup_status=status,capacity_attributable_mw=mw,capacity_status='future_project_financing_attribution_not_current_operating_capacity' if status=='expected_future_startup' else 'financing_attributable_capacity_not_full_project_capacity',allocation_effective_from=alloc_from,allocation_effective_to=alloc_to,project_allocation_money=None,project_actual_generation_gwh=None,missingness_reason='Money and generation reported at instrument/area aggregate only; no project-specific values disclosed.',**prov('green'+str(yr),page,'Allocated assets',name,'Technology; Location; Start-up year; Installed capacity attributable; project-name date qualifier')))
jan=[('East Anglia 1','Offshore wind','United Kingdom','2019',21),('Wikinger','Offshore wind','Germany','2017',3),('Whitelee','Onshore wind','United Kingdom','2008',28),('Ewe Hill 16','Onshore wind','United Kingdom','2017',15),('Hare Hill Extension','Onshore wind','United Kingdom','2017',3),('Dos Arbolitos','Onshore wind','Mexico','2015',7),('Támega','Hydraulic','Portugal','2022-2024',100),('Dólar III','Onshore wind','Spain','2006',36),('Cabezuelo','Onshore wind','Spain','2006',30),('Cruz de Carrutero','Onshore wind','Spain','2011',30),('Viñas','Onshore wind','Spain','2010',1),('Ferreira II','Onshore wind','Spain','2006',50),('Hueneja','Onshore wind','Spain','2006',50),('Sil Ampliación','Onshore wind','Spain','2006',40),('O Vieiro','Onshore wind','Spain','2006',20),('Luzón-Norte','Onshore wind','Spain','2006',38),('Bordecorex Norte','Onshore wind','Spain','2006',42)]
for i,x in enumerate(jan):P('XS2748213290',*x,75 if i<13 else 76,'2024-03-22')
P('CH1357852685','EGL1','Networks','United Kingdom','2029',None,79,status='expected_future_startup')
P('CH1357852677','EGL1','Networks','United Kingdom','2029',None,80,status='expected_future_startup')
for name,t,y,mw in [('Montague','Photovoltaic Solar','2023',74),('Midland','Onshore Wind','2023',103),('Lundhill','Photovoltaic Solar','2022',46),('La Joya','Onshore Wind','2021',51),('WY´East','Photovoltaic Solar','2018',9),('Deerfield','Onshore Wind','2017',28),('Amazon','Onshore Wind','2017',57),('Gala','Photovoltaic Solar','2017',42)]:P('XS2861000235',name,t,'USA',y,mw,81,'2024-12-01' if name in ['Amazon','Gala'] else '')
P('XS2930118265','East Anglia 2','Offshore Wind','United Kingdom','2028',169,83)
P('AU3CB0315802','Broadsound SF','Photovoltaic Solar','Australia','2026',165,84)
P('AU3CB0315802','Broadsound BESS','Batteries','Australia','2026',79,84)
for name,t,y,mw in [('Broadsound SF','Photovoltaic Solar','2026',24),('Broadsound BESS','Batteries','2026',12),('Smithfield','Batteries','2026',65),('Gin Gin','Batteries','2027',174)]:P('AU3CB0315810',name,t,'Australia',y,mw,85)
for name,loc,y in [('East Anglia 1','United Kingdom','2019'),('Wikinger','Germany','2017')]:P('XS2949317676',name,'Offshore Wind',loc,y,0,87,'2025-02-07')
# The 2022 original-issue bond is a separate longitudinal continuity case, not added to 2024 issuance totals.
for yr,p,cap,gen,co2 in [(2022,41,310,0,0),(2023,44,356,19,1306),(2024,50,356,321,59893)]:
 for k,v,u in [('investment_allocated_million',1000,'EUR million'),('reported_attributable_capacity_mw',cap,'MW'),('actual_attributable_generation_gwh',gen,'GWh'),('avoided_co2_tonnes',co2,'tonnes CO2')]:addif('XS2455983861',yr,k,v,u,p,'March 2022 Bond / Total amount invested / Sustainability indicators',notes='Continuity case; allocation and startup expectations change across reports. 2022 zero output explicitly reflects projects under construction.',cohort='matched_2022_bond_continuity_case')
P('XS2455983861','St. Brieuc','Offshore wind','France','2023',81,41,yr=2022,cohort='matched_2022_bond_continuity_case')
P('XS2455983861','Baltic Eagle','Offshore wind','Germany','2023',229,41,yr=2022,cohort='matched_2022_bond_continuity_case')
for name,c,y,mw,fr,to in [('St. Brieuc','France','2023',81,'',''),('Baltic Eagle','Germany','>2024',229,'','2023-11-01'),('Baltic Eagle','Germany','>2024',184,'2023-11-02',''),('East Anglia 3','United Kingdom','2026',91,'2023-11-02','')]:P('XS2455983861',name,'Offshore wind',c,y,mw,44,fr,to,yr=2023,cohort='matched_2022_bond_continuity_case')
for name,c,y,mw in [('St. Brieuc','Francia','2023',81),('Baltic Eagle','Germany','2024',184),('East Anglia 3','United Kingdom','2026',91)]:P('XS2455983861',name,'Offshore Wind',c,y,mw,50,yr=2024,cohort='matched_2022_bond_continuity_case')
write('green_bond_instrument_facts.csv',IF)
write('green_bond_project_allocations.csv',projects)
# Event facts: divestment is not retirement.
events=[]
for year,metric,value in [(2023,'Mexico_CCGT_capacity_MW',9660),(2024,'Mexico_CCGT_capacity_MW',1166),(2024,'Mexico_CCGT_divested_MW',8494),(2023,'Mexico_CCGT_actual_generation_GWh',52557),(2024,'Mexico_CCGT_actual_generation_GWh',15001),(2023,'Mexico_thermal_actual_generation_GWh',53954),(2024,'Mexico_thermal_actual_generation_GWh',16389)]:
 events.append(dict(issuer='Iberdrola',observation_year=year,field=metric,value=value,event_type='sale_divestment_to_Mexico_Infrastructure_Partners',physical_retirement_established=False,notes='Capacity reduction and generation decline attributed by issuer to sale. No plant closure or global emissions reduction inferred.',**prov('annual2024',297,'Mexico / Thermal capacity and production',metric,metric,286)))
write('ownership_events.csv',events)
# Allocation/currency/table mismatch record: preserve without silently repairing originals.
issues=[]
def Q(id,severity,finding,impact,evidence):issues.append(dict(issue_id=id,severity=severity,finding=finding,analytical_impact=impact,evidence=evidence))
Q('IB01','critical','2024 green-finance coverage excludes Avangrid/Neoenergia instruments while issuer generation includes those operating businesses.','The bounded holding cohort cannot measure total-group green financing; no group-level financing-to-generation causal inference.','green2024 p2 and p4 fn5; annual2024 pp277–278')
Q('IB02','high','Mexico transfer of 8494 MW CCGT explains the large generation decline.','Issuer portfolio divestment must not be treated as physical fossil retirement.','annual2024 printed286 / PDF297')
Q('IB03','high','Published 2023 consolidated cogeneration shifts from 6106 to 5866 GWh; 240 moves to proportional investees.','Use latest comparators, retain revisions, and test group-total boundary; do not assume 2022 was retrospectively harmonised.','annual2023 printed255/PDF258 versus annual2024 printed278/PDF289')
Q('IB04','high','Future project MW is labelled installed capacity attributable in green reports, including 2028 East Anglia 2 and 2026/2027 Australian assets.','Financing attribution capacity is not newly commissioned or operating capacity; future startup years remain expectations.','green2024 pp83–85')
Q('IB05','high','2024 summary mislabels XS2748213290 Networks and CH1357852685 Renewables; XS2861000235 UK Networks.','Use detailed asset pages, preserve discrepancy audit; do not ingest summary taxonomy unchecked.','green2024 pp12–13 versus pp75–76,79,81; p12 visually confirmed')
Q('IB06','medium','CH1357852685 nominal EUR203m in inventory, EUR202m in summary, EUR196m allocated at issuance FX. CHF145m tranche EUR154m inventory vs EUR149m allocated. AUD tranches EUR209m/239m inventory vs EUR216m/247m allocated.','Keep original currency and distinct EUR conversion dates; do not sum different FX bases as same measure. CHF203/202 discrepancy unresolved.','green2024 pp5–6,12–13,79–80,84–85')
Q('IB07','high','2022 p49 wrongly repeats ISIN XS2455983861 for a November 2022 allocation while p41 clearly identifies March 2022 issue; p49 project allocation does not belong to extracted March continuity case.','Naive ISIN extraction would merge incompatible assets and double count; select verified issue-date/heading combination, exclude anomalous p49.','green2022 pp3,41,49; repeated heading as printed')
Q('IB08','medium','January2024 17 project capacity rows sum to 514 MW while instrument total is 512 MW.','Keep stated total and individual rounded rows; discrepancy2 MW is compatible with rounding, not reconciled by altering values.','green2024 pp75–76')
Q('IB09','high','Thermal includes nuclear; Batteries output narrative identifies fuel cells; solar capacity measured in MWdc.','Avoid binary fossil/renewable recoding without fuel validation; storage must not be treated as primary energy generation.','annual2024 printed277–278 and285/PDF288–289,296')
Q('IB10','medium','Montague start-up year is2023 in green2024 p81, whereas annual2024 p284 says final5 MW installed and commercial operation began April2024.','Reported start-up is not necessarily final COD; retain source-specific year without resolving project-stage ambiguity.','green2024 p81; annual2024 printed284/PDF295')
Q('IB11','high','Financing-attributed generation covers assignment periods: January hybrid from22 March; Amazon/Gala only December; November hybrid zero until February2025.','Not full-year project output or additional output caused by funding. Do not sum successive instruments without period-aware overlap controls.','green2024 fn49 p75; fn53 p81; fn58 p87')
write('quality_issues.csv',issues)
# Machine-auditable arithmetic; no economic recoding beyond declared scope.
checks=[]
for (yr,metric),vals in data.items():
 for j,sc in enumerate(scopes):
  for label,idx,target in [('renewable_components',[1,2,3,4,5,6],0),('thermal_components',[8,9,10],7),('two_subtotals',[0,7],11)]:
   calc=sum(vals[i][j] for i in idx);reported=vals[target][j]
   checks.append(dict(check='issuer_component_sum',year=yr,metric=metric,scope=sc,group=label,calculated=calc,reported=reported,difference=calc-reported,status='pass' if calc==reported else 'rounding_or_source_discrepancy'))
 for t,v in zip(tech,vals):checks.append(dict(check='ownership_scope_sum',year=yr,metric=metric,scope='consolidated_plus_investees',group=t,calculated=v[0]+v[1],reported=v[2],difference=v[0]+v[1]-v[2],status='pass' if v[0]+v[1]==v[2] else 'rounding_or_source_discrepancy'))
for i in instruments:
 isin=i[0];ps=[p for p in projects if p['instrument_isin']==isin and p['report_year']==2024]
 vals=[p['capacity_attributable_mw'] for p in ps]
 if None not in vals:
  calc=sum(vals);reported=i[9];checks.append(dict(check='instrument_project_capacity_sum',year=2024,metric='attributable_capacity_mw',scope=isin,group='all_projects',calculated=calc,reported=reported,difference=calc-reported,status='pass' if calc==reported else 'rounding_or_source_discrepancy'))
write('validation_checks.csv',checks)
# Evidence excerpts are page-specific and traceable, not substitute public reports.
E=R/'evidence_pages';E.mkdir(exist_ok=True)
pages={'annual2024':[288,289,295,296,297],'annual2023':[257,258],'green2024':[2,5,6,7,12,13,50,75,76,79,80,81,83,84,85,87],'green2023':[2,44],'green2022':[2,3,41,49]}
for sid,ps in pages.items():
 text=S[sid]['txt'].read_text().split('\f')
 for p in ps:(E/f'{sid}_pdfpage{p}.txt').write_text(f"Source: {S[sid]['url']}\nPDF page (1 based): {p}\n\n"+text[p-1])
# Short derived descriptive result, never an impact estimate.
desc=[]
for yr in [2022,2023,2024]:
 for j,scope in enumerate(scopes):
  g=data[(yr,'actual_generation_gwh')];c=data[(yr,'capacity_mw')]
  for field,value,formula in [('ccgt_generation_share_pct',100*g[9][j]/g[11][j],'100 * Gas combined cycles GWh / Total Group GWh'),('ccgt_plus_cogeneration_share_pct_sensitivity',100*(g[9][j]+g[10][j])/g[11][j],'100 * (Gas combined cycles + Cogeneration GWh) / Total Group GWh; cogeneration fuel not fully verified'),('ccgt_capacity_share_pct',100*c[9][j]/c[11][j],'100 * Gas combined cycles MW / Total Group MW')]:
   desc.append(dict(issuer='Iberdrola',year=yr,ownership_scope=scope,field=field,value=round(value,6),unit='%',formula=formula,input_file='issuer_year_technology_facts.csv',notes='Descriptive ownership-portfolio metric; not physical system decarbonisation.'))
write('descriptive_metrics.csv',desc)
summary={'issuer_year_technology_rows':len(facts),'instrument_fact_rows':len(IF),'project_allocation_rows':len(projects),'new2024_isins':len(instruments),'new2024_project_rows':sum(p['cohort']=='2024_new_holding_bonds' for p in projects),'longitudinal_case_rows':sum(p['cohort']=='matched_2022_bond_continuity_case' for p in projects),'validation_checks':len(checks),'nonzero_arithmetic_differences':[x for x in checks if x['difference']!=0]}
(R/'validation_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
# Supplement: requested CCGT capacity bridge, keeping unexplained residuals explicit at each stage.
bridge=[]
for order,field,value,p,printed,table,row,note in [
(1,'opening_consolidated_ccgt_capacity_2023',16131,288,277,'By technology','Gas combined cycles / 2023 consolidated','Year-end stock'),
(2,'closing_consolidated_ccgt_capacity_2024',7654,288,277,'By technology','Gas combined cycles / 2024 consolidated','Year-end stock'),
(3,'observed_net_change',-8477,288,277,'By technology','Gas combined cycles / Chg. Consolidated MW','7654 - 16131'),
(4,'mexico_divestment_contribution',-8494,297,286,'Mexico / Thermal capacity and production','Gas combined cycles / Change MW','Sale to MIP; ownership transfer, not retirement'),
(5,'residual_after_mexico_sale_only',17,288,277,'Derived bridge using pp277 and286','Gas combined cycles','7654 - (16131 - 8494); residual before accounting for Brazil uprating'),
(6,'termopernambuco_modernisation_uprating',17,298,287,'Brazil / Thermal capacity and production','Termopernambuco narrative','Issuer states modernisation increased capacity by17 MW to550 MW'),
(7,'unexplained_net_residual_after_verified_events',0,298,287,'Derived bridge using pp277,286,287','Consolidated global CCGT','7654 - (16131 - 8494 +17); zero net residual does not prove absence of offsetting unreported gross changes')]:
 bridge.append(dict(issuer='Iberdrola',period='2023-12-31 to 2024-12-31',ownership_scope='consolidated_at_EBITDA_level',step=order,field=field,value_mw=value,interpretation=note,additional_source_pdf_pages='288;297;298' if field.startswith('residual') or field.startswith('unexplained') else '',**prov('annual2024',p,table,row,field,printed)))
write('ccgt_capacity_bridge_2023_2024.csv',bridge)
events.append(dict(issuer='Iberdrola',observation_year=2024,field='Mexico_sale_completion_date',value='2024-02-26',event_type='sale_divestment_to_Mexico_Infrastructure_Partners',physical_retirement_established=False,notes='Transaction completed after approval and conditions precedent. This is completion of sale, not closure of operating plants.',**prov('annual2024',182,'Administrative proceedings in other countries','Mexico transaction completion paragraph','On26 February2024 transaction completed',171)))
events.append(dict(issuer='Iberdrola',observation_year=2024,field='Mexico_transaction_combined_cycle_plus_wind_headline_capacity_MW',value=8539,event_type='transaction_headline_scope',physical_retirement_established=False,notes='Headline12 CCGT plus1 wind farm; not interchangeable with8494 MW CCGT decrease in operating table. Together with103 MW wind capacity reduction, operating-table decrease is8597 MW;58 MW mismatch remains unresolved.',**prov('annual2024',182,'Administrative proceedings in other countries','Mexico transaction completion paragraph','Total installed capacity of transferred assets',171)))
events.append(dict(issuer='Iberdrola',observation_year=2024,field='Termopernambuco_capacity_uprating_MW',value=17,event_type='modernisation_uprating',physical_retirement_established=False,notes='Reported increase of17 MW to550 MW. 2023 source reports533 MW.',**prov('annual2024',298,'Brazil / Thermal capacity and production','Termopernambuco','Increase in capacity',287)))
write('ownership_events.csv',events)
Q('IB12','medium','Mexico transaction headline capacity8539 MW includes wind, whereas operational-table CCGT decline8494 MW plus wind103 MW equals8597 MW.','Do not merge headline deal scope with operating-table bridge;58 MW cross-source denominator mismatch remains unexplained. The CCGT bridge itself uses consistently reported operating-table figures.','annual2024 printed171/PDF182 and printed285–286/PDF296–297')
for q in issues:
 ids=[s for s in S if s in q['evidence']]
 q['source_urls']=' | '.join(S[s]['url'] for s in ids)
write('quality_issues.csv',issues)
for d in desc:
 sid='annual2023' if d['year']==2022 else 'annual2024';is_cap='capacity' in d['field'];p=(257 if is_cap else 258) if d['year']==2022 else (288 if is_cap else 289)
 d.update(prov(sid,p,'By technology','Gas combined cycles; Cogeneration if sensitivity; Total Group',d['ownership_scope'],p-(3 if d['year']==2022 else 11)))
write('descriptive_metrics.csv',desc)
for sid,ps in [('annual2024',[182,298]),('annual2023',[268])]:
 text=S[sid]['txt'].read_text().split('\f')
 for p in ps:(E/f'{sid}_pdfpage{p}.txt').write_text(f"Source: {S[sid]['url']}\nPDF page (1 based): {p}\n\n"+text[p-1])
# Primary-key and provenance validation.
assert len(facts)==len({(x['observation_year'],x['metric'],x['reported_technology'],x['ownership_scope']) for x in facts})
assert len(IF)==len({(x['report_year'],x['instrument_isin'],x['field']) for x in IF})
assert len(projects)==len({(x['report_year'],x['instrument_isin'],x['project_name_reported'],x['allocation_effective_from'],x['allocation_effective_to']) for x in projects})
for x in facts+IF+projects+events:
 assert x['source_url'].startswith('https://www.iberdrola.com/') and x['pdf_page_1_based']>0
summary.update(primary_keys_unique=True,all_observed_facts_have_url_page_table_row_field=True,ccgt_bridge_final_net_residual_mw=0,quality_issue_count=len(issues))
(R/'validation_summary.json').write_text(json.dumps(summary,indent=2))
