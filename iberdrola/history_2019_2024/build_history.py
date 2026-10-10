from pathlib import Path
import csv,json,hashlib,collections
H=Path(__file__).parent;R=H.parent;O=Path('/workspace/shared/manuscript_upgrade_20261010/data_feasibility')
BASE='https://www.iberdrola.com/documents/20125/'
urls={'annual2020':BASE+'42397/gsm21_FinancialStatements_AuditorsReport_Consolidated.pdf','annual2021':BASE+'1606413/gsm22_FinancialStatements_AuditorsReport_Consolidated2021.pdf','annual2022':BASE+'2931678/gsm23_FinancialStatements_AuditorsReport_Consolidated2022.pdf','annual2023':BASE+'3643974/gsm24-annual-accounts-consolidated-2023.pdf','annual2024':BASE+'4778712/gsm25-annual-accounts-consolidated-2024.pdf','green2019':BASE+'42169/Informe_retornos_financiacion_verde_2019.pdf','green2020':BASE+'42169/Green_financing_returns_report_2020.pdf','green2021':BASE+'42169/Green_financing_returns_report_2021.pdf','green2022':BASE+'42169/Green_financing_returns_report_2022.pdf','green2023':BASE+'42169/green-financing-returns-report-2023.pdf','green2024':BASE+'42169/green-financing-returns-report-2024.pdf','factbook2021':BASE+'41740/Factbook_2021_EN.pdf','results2020':BASE+'42352/2020_Results_FY.pdf','coal_strategy2017':BASE+'668426/l3bj0vvk_qaw.pdf','coal_transition2020':BASE+'642917/gfpyvktq_zie.pdf','infigen_announcement2020':BASE+'646426/16062020_green_announcement_clean_dm_1530_cet_pm.pdf','halfyear2020':BASE+'42352/InformeConsolidado1S20_EN.pdf'}
paths={k:H/(k+'.pdf') for k in urls};paths.update(annual2023=R/'annual2023.pdf',annual2024=O/'iberdrola_annual_2024.pdf',green2022=R/'green2022.pdf',green2023=R/'green2023.pdf',green2024=O/'iberdrola_2024.pdf')
paths={k:(H/(k+'.pdf') if (H/(k+'.pdf')).exists() else p) for k,p in paths.items()}
texts={k:p.with_suffix('.txt') for k,p in paths.items()};texts['annual2024']=(H/'annual2024.txt' if (H/'annual2024.txt').exists() else R/'annual2024.txt')
def wr(n,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with (H/n).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def src(s,p,printed,table,row,field):return dict(source_id=s,source_url=urls[s],pdf_page_1_based=p,printed_page=printed,source_table=table,source_row=row,source_field=field)
manifest=[]
for s,p in paths.items():manifest.append(dict(source_id=s,source_url=urls[s],local_pdf=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pdf_pages=len(texts[s].read_text().split('\f'))-1,retrieved_utc_date='2026-10-10',usage='official issuer PDF; report language English even where archive filename is Spanish'))
_existing_manifest=list(csv.DictReader((H/'source_manifest.csv').open(encoding='utf-8-sig',newline='')))
manifest.extend(r for r in _existing_manifest if r['source_id']=='offering_circular_2019')
wr('source_manifest.csv',manifest)
scopes=['consolidated_at_EBITDA_level','proportional_managed_investees','group_total_consolidated_plus_proportional_investees']
# Values in consistent published ownership columns. Coal after2020 is derived absence, explicitly marked rather than observed table zeros.
series={2019:{'Gas combined cycles':(14655,0,14655),'Cogeneration':(1284,51,1335),'Coal':(874,0,874),'Total Group':(49339,2743,52082)},2020:{'Gas combined cycles':(15821,0,15821),'Cogeneration':(1140,51,1191),'Coal':(0,0,0),'Total Group':(52401,2710,55111)},2021:{'Gas combined cycles':(15821,0,15821),'Cogeneration':(1134,51,1185),'Coal':(0,0,0),'Total Group':(55551,2768,58319)}}
series.update({
2022:{'Gas combined cycles':(16131,204,16335),'Cogeneration':(1134,51,1185),'Coal':(0,0,0),'Total Group':(57793,2970,60763)},
2023:{'Gas combined cycles':(16131,204,16335),'Cogeneration':(1134,51,1185),'Coal':(0,0,0),'Total Group':(61006,1879,62885)},
2024:{'Gas combined cycles':(7654,204,7858),'Cogeneration':(1105,51,1156),'Coal':(0,0,0),'Total Group':(54687,1983,56670)}})
loc={2019:('annual2020',243,231),2020:('annual2021',254,243),2021:('annual2022',258,247),2022:('annual2023',257,254),2023:('annual2024',288,277),2024:('annual2024',288,277)}
cap=[]
for y,tt in series.items():
 for t,vals in tt.items():
  s,p,pr=loc[y]
  if t=='Coal' and y==2020:s,p,pr='annual2020',243,231
  for j,v in enumerate(vals):
   notes='Gas category includes Australian open-cycle gas turbines; retain issuer taxonomy, use broad gas-fired interpretation.' if t=='Gas combined cycles' else 'Cogeneration is a technology category, not independently verified homogeneous fuel.' if t=='Cogeneration' else ''
   status='reported_value'
   if t=='Coal' and y>=2021:status='derived_structural_zero';notes='Coal row omitted from exhaustive technology table; zero inferred from documented complete2020 coal exit and exhaustive totals. Raw missingness is not silently recoded. Revalidate for any extension.'
   cap.append(dict(issuer='Iberdrola',year=y,reported_technology=t,capacity_mw=v,ownership_scope=scopes[j],primary_scope=(j==2),value_status=status,timing='year_end_stock',report_vintage=int(s[-4:]),notes=notes,**src(s,p,pr,'Electricity production and retail / By technology',t,f'{y} / {scopes[j]}')))
wr('capacity_by_fossil_technology_2019_2024.csv',cap)
# Explicit original-vs-later capacity restatement instead of treating it as disposal.
rev=[]
for scope,old,new in zip(scopes,[16335,0,16335],[16131,204,16335]):rev.append(dict(year=2022,technology='Gas combined cycles',ownership_scope=scope,original_capacity_mw=old,later_capacity_mw=new,difference_mw=new-old,original_url=urls['annual2022'],original_pdf_page=258,original_printed_page=247,later_url=urls['annual2023'],later_pdf_page=257,later_printed_page=254,interpretation='204 MW changes accounting column; group total unchanged. Treat as reporting-perimeter reclassification, not asset exit.'))
wr('capacity_reporting_revision.csv',rev)
# Ledger is asset/event-level. Dates carry actual precision; no day invented for year-only source.
events=[]
def event(id,y,date,precision,project,tech,kind,delta,s,p,pr,field,notes='',secondary=''):
 events.append(dict(event_id=id,year=y,event_date_reported=date,date_precision=precision,asset_or_project=project,country='Australia' if 'Smithfield' in project or 'South Australian' in project else 'Brazil' if 'Termopernambuco' in project else 'Mexico' if project in ['Topolobampo III','Enertek','Tamazunchale II','Mexico CCGT portfolio'] else 'Spain',reported_technology=tech,event_class=kind,capacity_delta_mw=delta,physical_retirement_verified=(kind=='physical_retirement'),include_in_capacity_bridge=True,notes=notes,secondary_source=secondary,**src(s,p,pr,'Asset/country operating narrative',project,field)))
event('IB_E01',2020,'2020-H1','half_year','Velilla 1 and 2','Coal','physical_retirement',-516,'annual2020',244,232,'Closure and516 MW','2020 annual report verifies closure; H1 report says closed by30 June2020. H1 uses Velilla1 label; annual says1 and2. Exact closure day not established.',urls['halfyear2020']+'#page=69')
event('IB_E02',2020,'2020; completed by2020-07-31','year_with_upper_bound','Lada','Coal','physical_retirement',-358,'annual2020',244,232,'Closure and358 MW','Annual verifies closure;31 July2020 issuer note confirms last two Spanish coal plants already closed. Exact closure day not established.',urls['coal_transition2020']+'#page=3')
event('IB_E03',2020,'2020-Q1','quarter','Topolobampo III','Gas combined cycles','physical_installation_completion',779,'annual2020',245,233,'Completion Q12020 and779 MW','Licence to start production remained pending in report; installed-capacity addition is not verified operational COD.')
event('IB_E04A',2020,'2020','year','Enertek','Gas combined cycles','technology_reclassification',144,'annual2020',245,233,'Transition from cogeneration to gas combined cycle','Offset by cogeneration reduction; no net fossil-capacity addition or retirement.')
event('IB_E04B',2020,'2020','year','Enertek','Cogeneration','technology_reclassification',-144,'annual2020',245,233,'144 MW expense of cogeneration','Mirror ofIB_E04A; combined fuel-portfolio effect is0.')
event('IB_E05',2020,'2020-08-05','day_for_control_acquisition','Smithfield OCGT via Infigen','Gas combined cycles','acquisition_existing_asset',123,'factbook2021',115,115,'Smithfield OCGT123 MW; installation1996','Control ofInfigen acquired5 August2020; exact capacity attributable at takeover inferred by matching existing Smithfield in acquired portfolio. OCGT is reported within CCGT heading.',urls['annual2020']+'#page=63')
event('IB_E06',2020,'2020-11','month','South Australian Gas Turbines','Gas combined cycles','acquisition_or_operating_rights_existing_asset',120,'factbook2021',115,115,'120 MW;2017 installation; acquired November2020','Factbook says acquired; takeover announcement describes turbines to be leased. Preserve ownership/operating-rights ambiguity; not newly built2020.',urls['infigen_announcement2020']+'#page=8')
event('IB_E07',2021,'2021','year','Eneryworks Villarrobledo','Cogeneration','capacity_reduction_mechanism_unresolved',-6,'annual2021',256,245,'Reduction6 MW','Source identifies asset but not closure/disposal/derating mechanism. Do not count as verified retirement.')
event('IB_E08',2022,'2022-05 (early)','month_qualifier','Tamazunchale II','Gas combined cycles','commissioning',514,'annual2022',265,254,'Entry into production earlyMay;514 MW','New operating capacity, unlike Topolobampo installation/licence caveat.')
event('IB_E09',2024,'2024-02-26','day','Mexico CCGT portfolio','Gas combined cycles','divestment_ownership_transfer',-8494,'annual2024',297,286,'Transferred8494 MW','Sale date verified separately. Plant operation after ownership transfer is not established here; no physical retirement inference.',urls['annual2024']+'#page=182')
event('IB_E10',2024,'2024','year','Termopernambuco','Gas combined cycles','modernisation_uprating',17,'annual2024',298,287,'Modernised;17 MW increase to550 MW','2023 annual printed265/PDF268 reports533 MW; unit physically expanded/uprated.')
event('IB_E11',2024,'2024','year','Spain cogeneration portfolio (asset unidentified)','Cogeneration','capacity_reduction_mechanism_unresolved',-29,'annual2024',291,280,'Spain cogeneration296 to267 MW','Country net decline is identified; asset/event mechanism not identified. Remains unclassified for closure/disposal attribution.')
wr('fossil_capacity_event_ledger.csv',events)
# Reconcile change with strictly classified events; unresolved reductions remain a residual in this bridge.
bridges=[]
for y in range(2020,2025):
 for t in ['Gas combined cycles','Cogeneration','Coal','Gas+Cogeneration+Coal']:
  ts=['Gas combined cycles','Cogeneration','Coal'] if t.startswith('Gas+') else [t]
  opening=sum(series[y-1][x][2] for x in ts);closing=sum(series[y][x][2] for x in ts);change=closing-opening
  ev=[e for e in events if e['year']==y and e['reported_technology'] in ts]
  known=[e for e in ev if e['event_class']!='capacity_reduction_mechanism_unresolved'];explained=sum(e['capacity_delta_mw'] for e in known);res=change-explained
  categories={c:sum(e['capacity_delta_mw'] for e in known if e['event_class']==c) for c in ['physical_retirement','physical_installation_completion','commissioning','technology_reclassification','acquisition_existing_asset','acquisition_or_operating_rights_existing_asset','divestment_ownership_transfer','modernisation_uprating']}
  bridges.append(dict(issuer='Iberdrola',year=y,technology=t,ownership_scope=scopes[2],opening_capacity_mw=opening,closing_capacity_mw=closing,observed_net_change_mw=change,verified_classified_event_net_mw=explained,unexplained_mechanism_net_residual_mw=res,identified_but_unclassified_reduction_mw=sum(e['capacity_delta_mw'] for e in ev if e not in known),classified_event_ids=';'.join(e['event_id'] for e in known),unclassified_event_ids=';'.join(e['event_id'] for e in ev if e not in known),input_capacity_file='capacity_by_fossil_technology_2019_2024.csv',input_event_file='fossil_capacity_event_ledger.csv',opening_source_url=urls[loc[y-1][0]],opening_source_pdf_page=loc[y-1][1],closing_source_url=urls[loc[y][0]],closing_source_pdf_page=loc[y][1],**categories))
wr('annual_capacity_bridges_2020_2024.csv',bridges)
# Prior decisions and project-delivery evidence, with no inference of causal attribution to green funding.
strategy=[dict(evidence_id='IB_S01',decision_date='2017-11-10',date_precision='day',asset='Lada and Velilla',decision_type='request_for_closure_authorisation',capacity_mw=874,relevance='Documented closure strategy predates the matchedFebruary2019 bond; it does not predate entire green financing programme begun2014.',**src('coal_strategy2017',1,1,'Press release','Closure permission request','Date and874 MW')),
dict(evidence_id='IB_S02',decision_date='2023-04',date_precision='month',asset='Mexico generation portfolio',decision_type='divestment_MoU',capacity_mw='',relevance='Agreement precedes2024 sale completion; not a2024 green-finance-induced closure.',**src('annual2023',102,91,'Note18 Assets and liabilities held for sale','Divestment in Mexico','April2023 MoU')),
dict(evidence_id='IB_S03',decision_date='2023-06',date_precision='month',asset='Mexico generation portfolio',decision_type='sale_purchase_agreement',capacity_mw='',relevance='Binding SPA reported as signedJune2023; no exact day assigned from this report.',**src('annual2023',102,91,'Note18 Assets and liabilities held for sale','Divestment in Mexico','June2023 SPA'))]
wr('prior_strategy_evidence.csv',strategy)
# Matched, stable February2019 green hybrid asset basket, all6 annual reports.
with (H/'instrument_date_provenance.csv').open(encoding='utf-8-sig',newline='') as _f:
 _date_record=next(csv.DictReader(_f))
_date_fields={k:v for k,v in _date_record.items() if k not in ['instrument_isin','verified_utc_date']}
bond=[];bp=[]
for yr,p,printed,gen,co2,eayr in [(2019,20,19,232,93265,2019),(2020,22,21,761,209234,2019),(2021,23,22,874,202192,2019),(2022,26,26,821,191783,2020),(2023,27,27,948,221965,2020),(2024,31,31,771,184477,2020)]:
 sid='green'+str(yr)
 for f,v,u in [('investment_allocated_stock',800,'EUR million'),('capacity_attributable',231,'MW'),('actual_generation_attributable',gen,'GWh'),('avoided_co2_reported',co2,'tonnes CO2')]:
  bond.append(dict(instrument_isin='XS1890845875',issuer='Iberdrola International',**_date_fields,report_year=yr,field=f,value=v,unit=u,refinancing_share_pct=None,finance_refinance_status='quantitative_split_not_disclosed_in_selected_instrument_tables',notes='Same two-asset basket; recurring800m is a stock, not six annual flows. Output is bond-attributed and not additionality. Contractual issue date and the distinct allocation-report inventory date are separately source-linked; no pricing-date inference.',**src(sid,p,printed,'February2019 Bond (hybrid) / Total invested and Sustainability indicators','XS1890845875',f)))
 for name,c,y,mw in [('East Anglia 1','United Kingdom',eayr,180),('Wikinger','Germany',2017,51)]:
  bp.append(dict(instrument_isin='XS1890845875',report_year=yr,project_standardised=name,project_name_reported='EAST ANGLIA' if yr<=2022 and name=='East Anglia 1' else 'WIKINGER' if yr<=2022 and name=='Wikinger' else name,technology='Offshore wind',country=c,startup_year_as_reported=y,capacity_attributable_mw=mw,project_money=None,project_actual_generation=None,notes='Reported EA startup changes2019 to2020 across vintages; independent factbook COD2020 retained separately. No project-specific money or generation disclosed.',**src(sid,p,printed,'Allocated assets',name,'Startup year; attributable MW; location')))
wr('matched_green_hybrid_2019_2024.csv',bond);wr('matched_green_hybrid_projects_2019_2024.csv',bp)
delivery=[]
for project,cod,capacity,consent in [('East Anglia ONE',2020,714,2014),('Wikinger',2017,350,2015)]:
 for field,value,unit in [('verified_reported_COD_year',cod,'year'),('full_project_capacity',capacity,'MW'),('reported_consent_year',consent,'year')]:
  delivery.append(dict(project=project,report_year=2021,field=field,value=value,unit=unit,status='Operational in source',notes='Whole-project capacity is not financing-attributed capacity. Source distinguishes COD from green-report startup labels; no treatment effect established.',**src('factbook2021',91,91,'Renewables offshore map',project,field)))
wr('matched_project_delivery_evidence.csv',delivery)
# Summary ratios kept downstream of observed data and explicit structural-zero rule.
metrics=[]
for y in sorted(series):
 fossil=sum(series[y][t][2] for t in ['Gas combined cycles','Cogeneration','Coal']);total=series[y]['Total Group'][2];sid,p,pr=loc[y]
 metrics.append(dict(issuer='Iberdrola',year=y,ownership_scope=scopes[2],reported_gas_capacity_mw=series[y]['Gas combined cycles'][2],cogeneration_capacity_mw=series[y]['Cogeneration'][2],coal_capacity_mw=series[y]['Coal'][2],broad_fossil_technology_capacity_mw=fossil,total_group_capacity_mw=total,broad_fossil_capacity_share_pct=100*fossil/total,notes='Broad technology proxy: cogeneration fuel mix not independently verified; reported gas containsOCGT. Coal2021–24 structural zeros are explicitly derived. Primary scope is accounting capacity, not fixed physical ownership.',**src(sid,p,pr,'By technology','Gas; Cogeneration; Coal; Total','group total capacity')))
wr('primary_capacity_summary.csv',metrics)
# Preserve page-level evidence for all observed facts/events.
E=H/'evidence_pages';E.mkdir(exist_ok=True)
used=collections.defaultdict(set)
for rows in [cap,events,strategy,bond,bp,delivery]:
 for row in rows:used[row['source_id']].add(row['pdf_page_1_based'])
for s,ps in {'annual2020':[61,63,244,245],'annual2023':[102],'annual2024':[182],'factbook2021':[115],'infigen_announcement2020':[8],'coal_transition2020':[3],'halfyear2020':[69]}.items():used[s].update(ps)
for s,ps in used.items():
 pages=texts[s].read_text().split('\f')
 for p in ps:(E/f'{s}_pdfpage{p}.txt').write_text(f'Source: {urls[s]}\nPDF page: {p}\n\n'+pages[p-1])
assert len(cap)==len({(x['year'],x['reported_technology'],x['ownership_scope']) for x in cap})
assert len(events)==len({x['event_id'] for x in events})
assert all(r['closing_capacity_mw']==r['opening_capacity_mw']+r['verified_classified_event_net_mw']+r['unexplained_mechanism_net_residual_mw'] for r in bridges)
assert all(v[0]+v[1]==v[2] for yy in series.values() for v in yy.values())
summary=dict(capacity_fact_rows=len(cap),asset_event_rows=len(events),annual_bridge_rows=len(bridges),matched_bond_fact_rows=len(bond),matched_project_rows=len(bp),primary_keys_unique=True,ownership_column_sums_reconcile=True,bridge_identities_reconcile=True,remaining_mechanism_unresolved=[dict(year=x['year'],technology=x['technology'],residual_mw=x['unexplained_mechanism_net_residual_mw']) for x in bridges if x['unexplained_mechanism_net_residual_mw'] and x['technology']!='Gas+Cogeneration+Coal'],physical_retirement_mw_2020_2024=874,divestment_mw_2020_2024=8494,unresolved_cogeneration_reductions_mw=35)
(H/'validation_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
