import csv,json
from pathlib import Path
P=Path(__file__).parent
U19='https://www.sse.com/media/lgxdmzoo/sse-31464-annual-report-2019-web.pdf'
U20='https://www.sse.com/media/jqcamklf/sse-32693-annual-report-2020-web-1.pdf'
U21='https://www.sse.com/media/rwhbww02/sse-annual-report-2021.pdf'
U22='https://www.sse.com/media/blhnuywb/sse-full-annual-report.pdf'
U23='https://www.sse.com/media/dncdjrcw/sse-annual-report-2023-web-final.pdf'
U24='https://www.sse.com/media/0aibgke4/sse_ar24_interactive.pdf'
def write(n,rows):
 with (P/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# A dash remains blank; a zero is recorded only when explicitly printed.
data={2019:([3929,1292,1510,34,6765,18322,1861,579,294,21056],U20,'printed p68; March2019 comparative'),2020:([4004,1292,0,68,5364,12948,2436,1946,395,17725],U20,'printed p68'),2021:([3992,1292,None,None,5284,15324,2433,None,251,18008],U21,'printed p86; PDF page88'),2022:([3975,1292,None,None,5267,11303,2962,None,None,14265],U22,'printed p103'),2023:([5538,1292,None,None,6830,16781,1532,None,None,18313],U23,'Thermal KPI; printed p104 in indexed text; locate by table title'),2024:([5538,672,None,None,6210,13597,1650,None,None,15247],U24,'printed p78')}
metrics=['gas_oil_gb_mw','gas_oil_roi_mw','coal_mw','multifuel_mw','thermal_total_mw','gas_oil_gb_gwh','gas_oil_roi_gwh','coal_gwh','multifuel_gwh','thermal_total_gwh']
rows=[]
for y,(vs,u,loc) in data.items():
 for m,v in zip(metrics,vs):
  rows.append(dict(issuer='SSE',fiscal_year_end=y,as_of=f'{y}-03-31',metric=m,value=v,unit='MW' if m.endswith('_mw') else 'GWh',status='reported_numeric' if v is not None else 'not_numeric_or_not_separately_reported',boundary='reported_thermal_portfolio;owned_plus_JV_capacity;output_contract_boundary_different',scope_flags='historical_multifuel_in_total;not_whole_company;Enterprise_excluded;GWh_secondary_only',source_url=u,source_locator=loc,source_column=f'March {y}',retrieved='2026-10-10'))
write('capacity_2019_2024_source_cells.csv',rows)
f=[]
for y,(vs,u,loc) in data.items():
 # After FY2020, reported total exactly equals gas/oil; avoid inferring source coal cells as zero.
 val=vs[0]+vs[1]+(vs[2] if vs[2] is not None else 0)
 f.append(dict(issuer='SSE',fiscal_year_end=y,reported_thermal_total_mw=vs[4],gas_oil_subtotal_mw=vs[0]+vs[1],explicit_coal_mw=vs[2],fossil_categories_capacity_mw=val,multifuel_separately_reported_mw=vs[3],derivation='GB gas/oil + ROI gas/oil + explicit coal' if y<=2020 else 'GB gas/oil + ROI gas/oil equals reported total; no additional coal imputation',whole_company_fossil_capacity_mw=None,scope='reported thermal portfolio only;historical scope changes retained',source_url=u))
write('capacity_2019_2024_fuel_stratified.csv',f)
# Signed contributions to reported thermal total; nonselected event types are not zero-filled.
events=[
(2020,'Fiddlers Ferry remaining units','physical_retirement','2020-03-31',-1510,'coal',U20,'p68 note4','Prior proposed closure13June2019;last generation17March2020;official closure31March2020'),
(2020,'Internal operating-model review','reporting_scope_change','FY2020',75,'gas_oil',U20,'p68 note3','4004-3929; issuer explicitly says not additional thermal plant; exact within-year date unknown'),
(2020,'Ferrybridge Multifuel2','physical_commissioning','2019-12',34,'multifuel',U20,'p68 note5','68-34 reported share;not pure fossil;gross plant rating differs from rounded share'),
(2021,'Ferrybridge Multifuel1/2 and Skelton Grange','ownership_disposal','2021-01-07',-68,'multifuel',U21,'p86 note4','Annual footnote says October2020; issuer completion announcement7January2021 distinguishes announcement from completion'),
(2021,'Small plant transfer to Enterprise','internal_segment_transfer','FY2021',-12,'gas_oil',U21,'p86 note5','Not physical retirement; whole-company fossil unchanged by transfer alone'),
(2022,'Small diesel plant','physical_closure','FY2022',-17,'gas_oil',U22,'p103 note4','Exact plant identities and dates not verified'),
(2023,'Keadby2 CCGT','physical_commissioning','2023-03-15',893,'gas',U23,'Thermal KPI note3;capacity contract table','Transmission Entry Capacity;construction commencedAugust2018;FY2023precommissioning output excluded'),
(2023,'Triton Saltend and Indian Queens','ownership_acquisition','2022-09-01',670,'gas',U23,'Thermal KPI note1;capacity contract table','Derived1200*0.5+140*0.5;Deeside decommissioned inertia asset excluded;not new physical plant'),
(2024,'Tarbert old oil station','physical_retirement','2023-12',-620,'oil',U24,'p78 note2','Site may host later new generation;prior licence-required closure disclosedFebruary2023')]
er=[]
for y,a,t,d,m,fuel,u,l,n in events: er.append(dict(issuer='SSE',bridge_fiscal_year=y,asset=a,event_type=t,event_date=d,signed_reported_portfolio_mw=m,fuel=fuel,source_url=u,source_locator=l,notes=n))
write('capacity_2019_2024_event_contributions.csv',er)
br=[]
for y in range(2020,2025):
 opening=data[y-1][0][4];closing=data[y][0][4];known=sum(r['signed_reported_portfolio_mw'] for r in er if r['bridge_fiscal_year']==y)
 br.append(dict(issuer='SSE',fiscal_year_end=y,opening_thermal_mw=opening,closing_thermal_mw=closing,observed_change_mw=closing-opening,identified_signed_contributions_mw=known,arithmetic_residual_mw=closing-opening-known,unidentified_gross_events_mw=None,whole_company_fossil_change_mw=None,status='arithmetic_reconciled_not_exhaustive_asset_census',warning='Zero arithmetic residual does not establish absence of offsetting unobserved events;thermal includes multifuel in2019/2020'))
write('capacity_2019_2024_bridges.csv',br)
coverage=[
(2019,'embedded_project_allocation_report','https://www.sse.com/media/0fpfwjju/sse-sustainability-report-2019-final-spreads.pdf','printed74–75;PDF38',2,'project tables located;not fully transcribed','refinancing_at_settlement'),
(2020,'sustainability_data_summary','https://www.sse.com/media/cw0hmsvv/sse-data-set-2020.pdf','PDF1',3,'bond-level allocations and output summary verified;full project report not retrieved','refinancing_at_settlement'),
(2021,'sustainability_report_summary','https://www.sse.com/media/5brnqtaa/sustainability-report-2021-final-final.pdf','SSE green bond reporting section',4,'bond-level summary verified;full project report not retrieved','refinancing_at_settlement'),
(2022,'standalone_allocation_impact_report','https://www.sse.com/media/gskfwnjn/green-bond-report-2022-v2-final.pdf','printed1 and project tables',4,'official PDF verified;project rows not yet transcribed','refinancing_at_settlement'),
(2023,'standalone_allocation_impact_report','https://www.sse.com/media/axfpchcj/sse-s-green-bond-report-to-march-2023-green-bonds-1-2-3-4-and-5.pdf','printed2;table6 printed9',5,'three GB5 project rows transcribed separately;other tables located','refinancing_at_settlement'),
(2024,'standalone_allocation_impact_report','https://www.sse.com/media/tbjlxitl/sse-green-bond-2024-v4.pdf','tables2/3/6',7,'existing bounded project extraction in same folder;network tables omitted','refinancing_at_settlement')]
write('green_uop_2019_2024_coverage.csv',[dict(report_year=y,report_type=t,source_url=u,locator=l,bond_groups=b,extraction_status=s,financing_class=c,physical_new_capacity_class='independent_project_status_not_inferred_from_refinancing') for y,t,u,l,b,s,c in coverage])
projects=[]
for name,cap,qual,alloc,capex,out,date,status in [('Viking',443,443,166,166,0,'2024-08','expected'),('Gordonbush Extension',38,38,37.2,37.2,64.3,'2021-08','actual'),('Seagreen1',1075,527,340.7,477.2,345.3,'2023-08','expected')]:
 projects.append(dict(report_year=2023,issuer='SSE',bond_id='GB5',isin='XS2510903862',project=name,total_capacity_mw=cap,qualifying_capacity_mw=qual,allocation_stock_gbp_m=alloc,reported_capex_gbp_m=capex,qualifying_output_gwh=out,fully_operational_month=date,operational_date_status=status,finance_class='refinancing',physical_new_build_status='new_project;commissioning_stage_independent_of_refinancing',source_url=coverage[4][2],source_locator='table6 printed9;PDF10',output_period='2022-04-01/2023-03-31',capex_period='2020-04-01/2022-03-31',scope='Seagreen49pct;other100pct;output_not_bond_attributable'))
write('green_uop_2023_gb5_project_rows.csv',projects)
print(json.dumps({'source_cells':len(rows),'annual_years':6,'event_contributions':len(er),'bridges':len(br),'all_arithmetic_residuals_zero':all(r['arithmetic_residual_mw']==0 for r in br),'uop_coverage_rows':len(coverage)},indent=2))
