import csv,json,pathlib
B=pathlib.Path(__file__).parent
U23='https://www.sse.com/media/dncdjrcw/sse-annual-report-2023-web-final.pdf'
U24='https://www.sse.com/media/0aibgke4/sse_ar24_interactive.pdf'
UB='https://www.sse.com/media/tbjlxitl/sse-green-bond-2024-v4.pdf'
UP='https://www.sse.com/media/ej5l4w14/sse-plc_prospectus-2024_final-version.pdf'
def write(name,rows):
 with (B/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Values are manually transcribed source cells, not estimates. Each field retains exact row+column provenance.
metrics={
'onshore_generation':('GWh',[3962,4413,4064],'Total onshore wind output','renewable'),
'offshore_generation':('GWh',[1430,1846,2477],'Offshore wind output (GB)','renewable'),
'hydro_generation':('GWh',[3107,3037,3071],'Conventional hydro output (GB)','renewable'),
'pumped_storage_generation':('GWh',[227,301,315],'Pumped storage output (GB)','renewable'),
'renewable_generation_including_storage':('GWh',[8726,9597,9927],'Total renewable generation (inc. pumped storage)','renewable'),
'renewable_headline_including_constraints':('GWh',[9423,10159,11158],'Total renewable generation (also inc. constrained off)','renewable'),
'onshore_constrained_off':('GWh',[469,456,530],'Note 3 onshore constrained off','renewable'),
'offshore_constrained_off':('GWh',[228,106,701],'Note 3 offshore constrained off','renewable'),
'biomass_generation_excluded_from_renewables':('GWh',[73,68,78],'Note 4 biomass output excluded','renewable'),
'onshore_capacity':('MW',[1974,1969,1984],'Total onshore wind capacity','renewable'),
'offshore_capacity':('MW',[487,487,1014],'Offshore wind capacity (GB)','renewable'),
'hydro_capacity':('MW',[1159,1159,None],'Conventional hydro capacity (GB)','renewable'),
'pumped_storage_capacity':('MW',[300,300,300],'Pumped storage capacity (GB)','renewable'),
'renewable_capacity_including_storage':('MW',[3920,3915,4457],'Total renewable generation capacity (inc. pumped storage)','renewable'),
'gas_oil_generation_gb':('GWh',[11303,16781,13597],'Gas- and oil-fired output (GB)','thermal'),
'gas_oil_generation_roi':('GWh',[2962,1532,1650],'Gas- and oil-fired output (ROI)','thermal'),
'gas_oil_generation_total':('GWh',[14265,18313,15247],'Total thermal generation','thermal'),
'gas_oil_capacity_total':('MW',[5267,6830,6210],'Total thermal generation capacity','thermal'),
'gas_oil_capacity_gb':('MW',[3975,5538,None],'Gas- and oil-fired generation capacity (GB)','thermal'),
'gas_oil_capacity_roi':('MW',[1292,1292,672],'Gas- and oil-fired generation capacity (ROI)','thermal'),
}
rows=[]
for metric,(unit,vals,label,cat) in metrics.items():
 for i,y in enumerate([2022,2023,2024]):
  v=vals[i];url=U23 if y<2024 else U24
  page=('print100–101; PDF51' if cat=='renewable' else 'print106–107; PDF54') if y<2024 else ('print75' if cat=='renewable' else 'print78')
  flags=('wholly_owned_plus_JV_share;biomass_excluded' if cat=='renewable' else 'includes_100pct_Marchwood_PPA;gas_and_oil_not_separate')
  if y==2022 and cat=='thermal':flags+=';Seabank_scope_change_2021_09'
  if y==2023 and cat=='thermal':flags+=';Triton_acquisition;Keadby2_precommissioning_1184GWh_excluded'
  if y==2024 and cat=='thermal':flags+=';Tarbert_closure'
  rows.append(dict(issuer='SSE',fiscal_year_end=y,period_start=f'{y-1}-04-01',period_end=f'{y}-03-31',metric=metric,value='' if v is None else v,unit=unit,value_status='not_verified' if v is None else 'reported',scope_flags=flags,source_url=url,source_locator=page,source_row=label,source_column=f'March {y}',retrieved='2026-10-10'))
write('issuer_year_cells.csv',rows)
# Report-year2024 direct-generation project rows: all such rows in tables2,3,6, plus HVDC rows in2/3 for completeness.
project_data=[
(2,'Strathy North','onshore_wind',102.9,67,67,'2015-11','actual',102.9,130.2,'1'),
(2,'Tievenameenta','onshore_wind',42.9,34,34,'2017-02','actual',41.5,86.4,'1'),
(2,'Comhlach Gaoithe Teoranta (Galway Wind Park)','onshore_wind',85.6,66,66,'2017-06','actual',81.9,175.8,'1'),
(2,'Dunmaglass','onshore_wind',88.9,94,47,'2017-08','actual',88.9,111.4,'1'),
(2,'Clyde Extension','onshore_wind',100.3,173,87,'2017-09','actual',100.1,177.0,'1'),
(2,'Bhlaraidh','onshore_wind',117.1,108,108,'2017-10','actual',106.6,161.0,'1'),
(2,'Caithness-Moray transmission link','transmission',1020.0,1200,1200,'2019-01','actual',26.5,None,'1'),
(3,'Leanamore','onshore_wind',30.8,18,18,'2018-02','actual',30.8,56.5,'2'),
(3,'Stronelairg','onshore_wind',147.6,228,114,'2018-12','actual',147.6,253.5,'2'),
(3,'Caithness-Moray transmission link','transmission',1020.0,1200,1200,'2019-01','actual',413.0,None,'2'),
(6,'Viking','onshore_wind',556.2,443,443,'2024-08','expected_at_report',166.0,0.0,'5'),
(6,'Viking','onshore_wind',556.2,443,443,'2024-08','expected_at_report',202.2,0.0,'6'),
(6,'Gordonbush Extension','onshore_wind',37.2,38,38,'2021-08','actual',37.2,51.3,'5'),
(6,'Gordonbush Extension','onshore_wind',37.2,38,38,'2021-08','actual',None,51.3,'6'),
(6,'Seagreen 1','offshore_wind',901.7,1075,527,'2023-10','actual',340.7,763.0,'5'),
(6,'Seagreen 1','offshore_wind',901.7,1075,527,'2023-10','actual',437.6,763.0,'6'),
]
prows=[]; pcells=[]
for table,project,tech,capex,mw,qmw,date,status,alloc,gwh,bond in project_data:
 page={2:5,3:6,6:10}[table]
 rid=f'SSE_2024_GB{bond}_{project.replace(" ","_")}'
 p=dict(record_id=rid,issuer='SSE',report_year=2024,bond_group=bond,project=project,technology=tech,total_capex_gbp_million=capex,full_capacity_mw=mw,qualifying_capacity_mw=qmw,operational_month=date,operational_date_status=status,allocated_gbp_million='' if alloc is None else alloc,allocation_status='source_dash' if alloc is None else 'reported',qualifying_output_gwh='' if gwh is None else gwh,generation_period_start='2023-04-01',generation_period_end='2024-03-31',generation_status='not_applicable_transmission' if gwh is None else 'reported_actual',financing_type='refinancing',allocation_flow_or_stock='stock_at_reporting;fully_allocated_at_settlement',country='',country_status='not_individually_verified',source_url=UB,source_locator=f'Table {table}; printed/PDF page {page}',double_count_flag='shared_physical_row_repeated_only_in_analytical_long_form' if table==6 else ('network_capacity_not_generation' if tech=='transmission' else 'none'))
 prows.append(p)
 for key in ['total_capex_gbp_million','full_capacity_mw','qualifying_capacity_mw','operational_month','allocated_gbp_million','qualifying_output_gwh']:
  pcells.append(dict(record_id=rid,field=key,value=p[key],source_url=UB,source_locator=p['source_locator'],source_row=project,source_column=key,verification='manual_web_pdf_text;visual_PDF_not_available',retrieved='2026-10-10'))
write('bond_project_rows_2024.csv',prows);write('bond_project_cell_provenance.csv',pcells)
# Instrument facts used to link financial subsidiary and reporting parent.
bonds=[]
for n,issuer,isin,date,gbp in [
(1,'SSE plc','XS1676952481','2017-09-06',548426017.30),(2,'SSE plc','XS1875284702','2018-09-04',591446676.80),
(3,'SHET plc','XS2057092236','2019-09-27',350000000),(4,'SHET plc','XS2321663473/XS2322933495','2021-03-24',500000000),
(5,'SSE plc','XS2510903862','2022-08-01',543933054.39),(6,'SSE plc','XS2675685700','2023-09-05',639822555.9),(7,'SHET plc','XS2747603624','2024-01-15',500000000)]:
 bonds.append(dict(bond_group=n,issuer_entity=issuer,parent='SSE',isin=isin,issue_date=date,issue_sterling_equivalent_gbp=gbp,allocation_status='fully_allocated_at_settlement',financing_type='refinancing',source_url=UB,source_locator='Table1 p4; allocation principle p3',scope_flag='combined_two_tranches' if n==4 else ('SHET75pct_owned;reported_capex100pct' if issuer=='SHET plc' else 'parent_issuer')))
write('bond_register_2024.csv',bonds)
events=[dict(event_id='SSE_Tarbert_2023',asset='Tarbert oil-fired station',country='Ireland',event_type='physical_closure',event_date='2023-12',date_precision='month_end',capacity_mw=620,scope='specific_oil_station;not_all_future_generation_at_site',source_url=UP,source_locator='printed p105',source_basis='explicit closure statement',interpretation='retirement event;no bond causal attribution'),
dict(event_id='SSE_Triton_2022',asset='Triton Power portfolio',country='United Kingdom',event_type='acquisition',event_date='2022-09-01',date_precision='day',capacity_mw='',scope='portfolio change',source_url=U23,source_locator='Thermal KPI notes print106–107; PDF54',source_basis='capacity incorporates acquisition from this date',interpretation='not new physical capacity'),
dict(event_id='SSE_Keadby2_2023',asset='Keadby2 CCGT',country='United Kingdom',event_type='commissioning',event_date='2023-03-15',date_precision='day',capacity_mw=893,scope='Transmission Entry Capacity',source_url=U23,source_locator='Thermal KPI notes/capacity contracts print106–107; PDF54',source_basis='explicit commissioned date;1184GWh precommissioning output excluded',interpretation='physicaladdition;generation series boundary flag'),
dict(event_id='SSE_Seabank_2021',asset='Seabank CCGT',country='United Kingdom',event_type='PPA_expiry_reporting_scope',event_date='2021-09',date_precision='month',capacity_mw='',scope='output accounting from100pctPPA to50pctequity',source_url=U23,source_locator='Thermal KPI note2 print106–107; PDF54',source_basis='explicit PPA expiry',interpretation='not retirement')]
write('asset_event_ledger.csv',events)
# Non-overlapping derived output: include wind+conventional hydro, not storage/compensated constrained-off.
der=[]
for i,y in enumerate([2022,2023,2024]):
 v=sum(metrics[k][1][i] for k in ['onshore_generation','offshore_generation','hydro_generation'])
 der.append(dict(issuer='SSE',fiscal_year_end=y,metric='wind_plus_conventional_hydro_generation',value=v,unit='GWh',status='derived',formula='onshore_generation + offshore_generation + hydro_generation',input_file='issuer_year_cells.csv',note='excludes_biomass_storage_and_constrained_off'))
write('derived_comparable_generation.csv',der)
# Verify source totals arithmetic; no regression.
checks=[]
for i,y in enumerate([2022,2023,2024]):
 checks.append({'year':y,'thermal_sum_matches':metrics['gas_oil_generation_gb'][1][i]+metrics['gas_oil_generation_roi'][1][i]==metrics['gas_oil_generation_total'][1][i],'renewable_components_match':der[i]['value']+metrics['pumped_storage_generation'][1][i]==metrics['renewable_generation_including_storage'][1][i],'headline_constraints_match':metrics['renewable_generation_including_storage'][1][i]+metrics['onshore_constrained_off'][1][i]+metrics['offshore_constrained_off'][1][i]==metrics['renewable_headline_including_constraints'][1][i]})
(B/'validation.json').write_text(json.dumps(checks,indent=2))
print('issuer cells',len(rows),'project rows',len(prows),'cell provenance',len(pcells),'all arithmetic',all(all(v for k,v in r.items() if k!='year') for r in checks))
