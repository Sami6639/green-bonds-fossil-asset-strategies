"""Reproducible transcription, arithmetic checks, and data-quality outputs.
Source values are transcribed from official reports; no estimation of fossil electricity.
Run with Python 3 standard library. PDF files are research inputs, not redistribution artifacts.
"""
import csv,json,hashlib,re,shutil
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parent
S=P/'sources';S.mkdir(exist_ok=True)
SRC={
 'OR_GF_2024':dict(title='Ørsted Green Finance Impact Report 2024',url='https://cdn.orsted.com/-/media/annual2024/green-finance-impact-report-2024.pdf?rev=d3c45ba7d27c4a338683f88839964b2b',local=S/'orsted_2024.pdf',pages='6;7;8;9;18'),
 'OR_AR_2024':dict(title='Ørsted Annual Report 2024',url='https://cdn.orsted.com/-/media/annual2024/orsted-annual-report-2024.pdf?hash=A05D897FF6CA71315480487832E17FA2&rev=02bde37dc8424c8eb8e4e9f3b65cc833',local=S/'orsted_annual_2024.pdf',pages='97;98;99;101;102'),
 'OR_AR_2023':dict(title='Ørsted Annual Report 2023',url='https://cdn.orsted.com/-/media/annual-report-2023/orsted-ar-2023.pdf?hash=249937EE100067C98DD7B879EDAD77A8&rev=20c94a62c8e24b45b4901f0e03f04a11',local=S/'orsted_annual_2023.pdf',pages='95;97;98')}
def save(name,rows,fields=None):
 if not rows and not fields:return
 with (P/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def slug(x):return re.sub(r'[^a-z0-9]+','_',x.lower()).strip('_')
def val(x):return '' if x=='-' else int(str(x).replace(',',''))
manifest=[]
for id,s in SRC.items():
 dest=S/s['local'].name
 if dest!=s['local']:shutil.copyfile(s['local'],dest)
 manifest.append(dict(source_id=id,title=s['title'],official_url=s['url'],local_file=str(dest.relative_to(P)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),printed_pages=s['pages'],pdf_page_offset=0,access_date_utc='2026-10-10',provenance='Official issuer PDF; 2024 reports reused from existing official-source research; 2023 downloaded directly for this pilot',license='No open redistribution licence verified; derived factual coding only'))
save('source_manifest.csv',manifest)
cells=[]
def cell(table,key,field,value,source,page,row_label,column_label,unit='',note=''):
 cells.append(dict(table=table,record_key=key,field=field,raw_value=str(value),value_status='reported_dash' if str(value)=='-' else 'reported_value',unit=unit,source_id=source,printed_page=page,pdf_page_1based=page,source_row=row_label,source_column=column_label,source_url=SRC[source]['url'],note=note))
# Finance p6: full 22-project table. Dashes remain null, particularly generation.
project_data=[
('Greater Changhua 1 and 2a','Offshore wind',900,'TW','In operation','2019-2024',277,14941,3330),
('Gode Wind 3','Offshore wind',253,'DE','In operation','2021-2024',804,2444,'-'),
('Borkum Riffgrund 3','Offshore wind',913,'DE','Under construction','2021-2026','-',1520,'-'),
('South Fork Wind','Offshore wind',132,'US','Under construction','2022-2024',436,2156,359),
('Greater Changhua 2b and 4','Offshore wind',920,'TW','Under construction','2023-2025',3735,5825,'-'),
('Revolution Wind','Offshore wind',704,'US','Under construction','2023-2025',5218,8097,'-'),
('Hornsea 3','Offshore wind',2852,'UK','Under construction','2023-2027','-',3963,'-'),
('Hornsea 1','Offshore wind',1218,'UK','In operation','2016-2019','-',10274,4338),
('Borkum Riffgrund 2','Offshore wind',450,'DE','In operation','2016-2018','-',2649,1347),
('Race Bank','Offshore wind',546,'UK','In operation','2015-2018','-',400,2032),
('Walney Extension','Offshore wind',659,'UK','In operation','2015-2018','-',1250,2531),
('Hornsea 2','Offshore wind',1320,'UK','In operation','2018-2022','-',9134,5295),
('Sunflower Wind','Onshore wind',201,'US','In operation','2022-2023','-',865,805),
('Badger','Onshore wind',259,'US','Under construction','2024-2025',952,952,'-'),
('Bahren West 1','Onshore wind',50,'DE','Under construction','2023-2025',197,197,'-'),
('Farranrory','Onshore wind',43,'IE','Under construction','2024-2026',116,116,'-'),
('Old 300','Solar PV',430,'US','In operation','2021-2024','-',1350,798),
('Eleven Mile','Solar PV',300,'US','In operation','2023-2024',814,3394,'-'),
('Mockingbird','Solar PV',471,'US','In operation','2023-2024',1239,1269,'-'),
('Sparta Solar','Solar PV',250,'US','In operation','2021-2024',310,800,'-'),
('Garreenleen','Solar PV',81,'IE','Under construction','2023-2026',143,143,'-'),
('Ballinrea','Solar PV',55,'IE','Under construction','2024-2026',27,27,'-')]
projects=[]
for name,tech,mw,country,status,period,annual,cumul,gwh in project_data:
 id='orsted_'+slug(name)
 note=''
 if name=='Gode Wind 3':note='P6 footnote: fully operational except one turbine; generation dash is not zero.'
 if name=='Eleven Mile':note='P6 footnote: solar PV project with combined power storage unit; 300 MW must not be labelled battery MW.'
 if name=='South Fork Wind':note='Status conflicts with Annual Report 2024 p98 COD in 2024; p6 reports 359 GWh despite Under construction.'
 r=dict(project_id=id,issuer='Ørsted',report_year=2024,project_name=name,technology=tech,country_reported=country,project_status_reported=status,construction_period_reported=period,capacity_full_project_mw=mw,allocation_2024_dkkm=val(annual),allocation_2024_raw=annual,allocation_cumulative_to_2024_dkkm=cumul,energy_generation_2024_full_project_gwh=val(gwh),generation_raw=gwh,attributed_capacity_mw='',attributed_generation_gwh='',allocation_scope='Ørsted ownership share',physical_scope='Full project regardless of Ørsted ownership',generation_type='Reported 2024 generation; operational generation defined as sold; no expected generation substituted',new_vs_refinancing='not_disaggregated_in_table',source_id='OR_GF_2024',source_page=6,notes=note)
 projects.append(r)
 for f,v,u,c in [('project_name',name,'','Project'),('technology',tech,'','Section heading'),('capacity_full_project_mw',mw,'MW','Capacity MW'),('country_reported',country,'','Country'),('project_status_reported',status,'','Project status'),('construction_period_reported',period,'year_range','Construction period Year'),('allocation_2024_dkkm',annual,'DKKm','Proceeds allocated 2024 DKKm'),('allocation_cumulative_to_2024_dkkm',cumul,'DKKm','Total allocated proceeds DKKm'),('energy_generation_2024_full_project_gwh',gwh,'GWh','Energy generation 2024 GWh'),('eu_taxonomy_aligned','true','','EU taxonomy-aligned')]:cell('projects_2024',id,f,v,'OR_GF_2024',6,name,c,u,note)
save('projects_2024.csv',projects)
pid={r['project_name']:r['project_id'] for r in projects}
# Complete p7 bond table: 22 outstanding plus one redeemed bond.
bondtext='''XS1721760541|Senior|EUR|750|1.50|2017-11-24|2029-11-26|5499|5499|-|-
XS1720192696|Hybrid|EUR|500|2.25|2017-11-24|3017-11-24|3674|3674|-|-
XS2010036874|Hybrid|EUR|600|1.75|2019-12-09|3019-12-09|4424|4424|-|-
XS1997070781|Senior|GBP|350|2.125|2019-05-16|2027-05-17|2968|2968|-|-
XS1997070864|Senior|GBP|300|2.50|2019-05-16|2033-05-16|2518|2518|-|-
XS1997071086|Senior CPI-linked|GBP|250|0.375|2019-05-16|2034-05-16|2128|2128|-|-
TW000F156013|Senior|NTD|4000|0.92|2019-11-19|2026-11-19|882|882|-|-
TW000F156021|Senior|NTD|8000|1.50|2019-11-19|2034-11-19|1765|1765|-|-
TW000F156039|Senior|NTD|4000|0.60|2020-11-13|2027-11-13|882|882|-|-
TW000F156047|Senior|NTD|3000|0.70|2020-11-13|2030-11-13|661|661|-|-
TW000F156054|Senior|NTD|8000|0.98|2020-11-13|2040-11-13|1763|1763|-|-
XS2293075680|Hybrid|EUR|500|1.50|2021-02-18|3021-02-18|3697|3697|-|-
XS2293681685|Hybrid|GBP|425|2.50|2021-02-18|3021-02-18|3630|3630|-|-
XS2490471807|Senior|EUR|600|2.25|2022-06-14|2028-06-14|4430|4430|-|-
XS2490472102|Senior|EUR|750|2.875|2022-06-14|2033-06-14|5553|5553|-|-
XS2531569965|Senior|EUR|900|3.25|2022-09-13|2031-09-13|6668|6668|4963|-
XS2531570039|Senior|GBP|375|5.125|2022-09-13|2034-09-13|3193|3193|2093|-
XS2531570112|Senior|GBP|575|5.375|2022-09-13|2042-09-13|4890|3355|2105|1535
XS2563353361|Hybrid|EUR|500|5.25|2022-12-08|3022-12-08|3692|3692|-|-
XS2591026856|Senior|EUR|700|3.625|2023-03-01|2026-03-01|5187|5187|-|-
XS2591029876|Senior|EUR|600|3.75|2023-03-01|2030-03-01|4414|4414|4414|-
XS2591032235|Senior|EUR|700|4.125|2023-03-01|2035-03-01|5146|100|100|5046
XS2778385240|Hybrid|EUR|750|5.125|2024-03-14|3024-03-14|5520|683|683|4837'''
bonds=[]
for line in bondtext.splitlines():
 isin,t,curr,face,coupon,issue,maturity,net,cumul,annual,unalloc=line.split('|')
 d=dict(isin=isin,bond_type=t,face_currency=curr,face_value_million=int(face),coupon_percent=coupon,issue_date=issue,maturity_date_reported=maturity,net_proceeds_dkkm=int(net),cumulative_allocation_dkkm=int(cumul),annual_2024_allocation_reported_dkkm=val(annual),annual_2024_raw=annual,unallocated_dkkm=val(unalloc),unallocated_raw=unalloc,report_year=2024,status='fully_redeemed_in_2024' if isin=='XS1720192696' else 'outstanding',source_id='OR_GF_2024',source_page=7,quality_flag='annual_amount_conflicts_with_p8_detail' if isin=='XS2531570112' else '')
 bonds.append(d)
 for f,v in list(d.items())[:14]:cell('bond_summary_2024',isin,f,v,'OR_GF_2024',7,isin,f,'DKKm' if 'dkkm' in f else '')
save('bond_summary_2024.csv',bonds)
# P8: each bond-project allocation exactly once, retaining the printed technology errors.
a=[]
def alloc(isin,name,amount,tech):
 id=f'{isin}:{pid[name]}:2024'
 r=dict(allocation_id=id,isin=isin,project_id=pid[name],project_name=name,allocation_year=2024,allocation_dkkm=amount,allocation_kind='annual_flow',technology_reported_p8=tech,technology_project_table_p6=next(x['technology'] for x in projects if x['project_name']==name),allocation_scope='Ørsted ownership share',new_vs_refinancing='not_disaggregated',source_id='OR_GF_2024',source_page=8)
 a.append(r)
 cell('allocation_2024',id,'allocation_dkkm',amount,'OR_GF_2024',8,f'{isin} / {name}','2024','DKKm')
 cell('allocation_2024',id,'technology_reported_p8',tech,'OR_GF_2024',8,f'{isin} / {name}','Type of project')
for isin,items in {
'XS2531569965':[('Gode Wind 3',239,'Offshore wind'),('Greater Changhua 2b and 4',2032,'Offshore wind'),('Mockingbird',1000,'Solar PV'),('Revolution Wind',1382,'Offshore wind'),('Sparta Solar',310,'Solar PV')],
'XS2591029876':[('Badger',253,'Onshore wind'),('Greater Changhua 2b and 4',1703,'Offshore wind'),('Eleven Mile',77,'Solar PV'),('Revolution Wind',1783,'Offshore wind'),('South Fork Wind',258,'Offshore wind'),('Ballinrea',27,'Solar PV'),('Bahren West 1',197,'Onshore Wind'),('Farranrory',116,'Onshore Wind')],
'XS2591032235':[('Badger',100,'Offshore wind')],
'XS2531570039':[('Gode Wind 3',565,'Offshore wind'),('Mockingbird',109,'Solar PV'),('Revolution Wind',1419,'Offshore wind')],
'XS2531570112':[('Badger',224,'Solar PV'),('Eleven Mile',737,'Solar PV'),('Mockingbird',130,'Solar PV'),('Revolution Wind',469,'Offshore wind'),('South Fork Wind',178,'Offshore wind'),('Greater Changhua 1 and 2a',277,'Offshore wind')],
'XS2778385240':[('Garreenleen',143,'Solar PV'),('Badger',375,'Offshore wind'),('Revolution Wind',165,'Offshore wind')]
}.items():
 for n,x,t in items:alloc(isin,n,x,t)
save('allocation_2024.csv',a)
# P9 is CUMULATIVE historical allocation over 2017-2023, NOT an annual allocation panel.
cols=['Greater Changhua 1 and 2a','Greater Changhua 2b and 4','Gode Wind 3','Borkum Riffgrund 3','Borkum Riffgrund 2','Hornsea 1','Hornsea 2','Hornsea 3','Revolution Wind','South Fork Wind','Race Bank','Walney Extension','Sunflower Wind','Old 300','Eleven Mile','Mockingbird','Sparta Solar']
histtext='''XS1721760541|4:2149,5:2350,6:100,10:400,11:500
XS1720192696|4:500,5:1924,6:500,11:750
XS2010036874|0:1624,5:100,6:2700
XS1997070781|5:2200,6:768
XS1997070864|5:2100,6:418
XS1997071086|5:1600,6:528
TW000F156013|0:882
TW000F156021|0:1765
TW000F156039|0:882
TW000F156047|0:661
TW000F156054|0:1763
XS2293075680|0:1837,2:640,9:630,12:300,13:290
XS2293681685|6:3630
XS2490471807|0:1500,2:280,3:600,6:490,12:500,13:1060
XS2490472102|7:2603,9:1090,14:1860
XS2531569965|2:720,3:920,12:65
XS2531570039|7:1000,15:10,16:90
XS2531570112|1:560,7:360,15:20,16:400
XS2563353361|0:1780,8:1192,14:720
XS2591026856|0:1970,1:1530,8:1687
XS2591029876|
XS2591032235|'''
h=[]
for line in histtext.splitlines():
 isin,content=line.split('|'); values={int(i):int(v) for i,v in (z.split(':') for z in content.split(',') if z)}
 for i,n in enumerate(cols):
  raw=values.get(i,'-');key=f'{isin}:{pid[n]}:2017-2023'
  h.append(dict(allocation_id=key,isin=isin,project_id=pid[n],project_name=n,period_start_year=2017,period_end_year=2023,allocation_dkkm=val(raw),raw_value=raw,value_status='reported_dash' if raw=='-' else 'reported_value',allocation_kind='cumulative_stock_over_historical_period',annual_allocation_year='',source_id='OR_GF_2024',source_page=9))
  cell('allocation_history_to_2023',key,'allocation_dkkm',raw,'OR_GF_2024',9,isin,n,'DKKm','Do not infer allocation year from bond issue year.')
save('allocation_history_to_2023.csv',h)
# Issuer-year factual observations. These are calendar years, not fiscal years.
observations=[]
def obs(year,metric,v,unit,src,page,row,scope,notes='',raw=None,preferred=True):
 id=f'orsted:{year}:{metric}:{src}:p{page}'
 observations.append(dict(observation_id=id,issuer='Ørsted',year=year,period_start=f'{year}-01-01',period_end=f'{year}-12-31',metric=metric,value=v,unit=unit,raw_value=v if raw is None else raw,observation_status='unavailable_in_scoped_sources' if v=='' else 'reported_or_explicitly_normalized',scope=scope,is_preferred_observation=str(preferred).lower(),source_id=src,printed_page=page,pdf_page_1based=page,source_row=row,source_column=str(year),notes=notes))
 if v!='':cell('issuer_year_observations',id,metric,v if raw is None else raw,src,page,row,str(year),unit,notes)
scop='Issuer reported generation boundary; wind/solar generation sold; thermal net generation sold; not full physical project portfolio'
for year,vals in {2022:[35641,16483,11225,1921,6012,6368,42009],2023:[35572,17761,11228,2146,4437,6587,42159],2024:[38436,18599,11959,3356,4522,6919,45355]}.items():
 src,page=('OR_AR_2023',97) if year==2022 else ('OR_AR_2024',101)
 labels=['Power generation','Offshore wind','Onshore wind','Solar PV','Thermal','Heat generation','Total heat and power generation']
 mets=['electricity_total_gwh','electricity_offshore_wind_gwh','electricity_onshore_wind_gwh','electricity_solar_pv_gwh','electricity_thermal_including_biomass_gwh','heat_generation_gwh','heat_plus_power_generation_gwh']
 for met,v,label in zip(mets,vals,labels):
  note='Thermal includes biomass and cannot be labelled fossil electricity.' if 'thermal_' in met else ''
  obs(year,met,v,'GWh',src,page,label,scop,note)
 obs(year,'electricity_fossil_total_gwh','','GWh',src,page,'Not separately reported','Target metric not identified','Do not multiply heat-plus-power fuel shares by electricity, or treat all thermal electricity as fossil.')
for year,vals in {2022:[11327,4672,3454,661,2540,1228,991,951,474],2023:[12511,4986,3707,1018,2800,1228,991,951,734],2024:[12899,5260,3666,1876,2097,1232,0,882,474]}.items():
 src,page=('OR_AR_2023',95) if year==2022 else ('OR_AR_2024',99)
 mets=['capacity_electricity_total_mw','capacity_offshore_wind_mw','capacity_onshore_wind_mw','capacity_solar_pv_mw','capacity_thermal_total_mw','capacity_thermal_biomass_capable_mw','capacity_thermal_coal_capable_mw','capacity_thermal_gas_capable_mw','capacity_thermal_oil_capable_mw']
 labels=['Power generation capacity','Offshore wind','Onshore wind','Solar PV','Power generation capacity, thermal','Based on biomass','Based on coal','Based on natural gas','Based on oil']
 for met,v,label in zip(mets,vals,labels):
  fuel='capable' in met
  note='Fuel-specific maxima for multi-fuel plants overlap and cannot be summed to unique fossil capacity.' if fuel else 'P99 selected as detailed capacity table; p97 conflicts by 1 MW for total and offshore in 2024.' if year==2024 and met in mets[:2] else ''
  raw='-' if year==2024 and met=='capacity_thermal_coal_capable_mw' else v
  if raw=='-':note+=' Source dash normalized to zero, corroborated by reported -991 MW change from 991 MW; not 991 MW of physical retirement.'
  obs(year,met,v,'MW',src,page,label,('2023 report policy: Gunfleet Sands 1 & 2 and Walney 1 & 2 ownership interest; other wind/solar/CHP financially consolidated' if year==2022 else '2024 report policy: generation capacity financially consolidated; fuel-capable rows are overlapping maxima'),note,raw)
 obs(year,'capacity_unique_fossil_mw','','MW',src,page,'Not separately identified','Target metric not identified','Cannot add coal, natural gas and oil capabilities at multi-fuel assets; thermal total includes biomass.')
# Two conflicting p97 cells retained, not overwritten.
obs(2024,'capacity_electricity_total_mw',12900,'MW','OR_AR_2024',97,'Power generation capacity','Overview by country table','Conflicts with 12,899 MW on p99; no official correction established.',preferred=False)
obs(2024,'capacity_offshore_wind_mw',5261,'MW','OR_AR_2024',97,'Offshore wind power','Overview by country table','Conflicts with 5,260 MW on p99; Germany 800 MW vs 799 MW explains location of 1 MW discrepancy.',preferred=False)
share_rows=['From offshore wind','From onshore wind','From solar PV','From sustainable biomass','From other renewable energy sources','From coal','From natural gas','From other fossil energy sources','Share of renewable energy generation']
share_mets=['share_heat_power_offshore_wind_pct','share_heat_power_onshore_wind_pct','share_heat_power_solar_pv_pct','share_heat_power_sustainable_biomass_pct','share_heat_power_other_renewables_pct','share_heat_power_coal_pct','share_heat_power_natural_gas_pct','share_heat_power_other_fossil_pct','share_heat_power_renewable_pct']
for year,vals in {2022:[39,27,5,20,0,8,1,0,91],2023:[42,27,5,18,1,6,1,0,93],2024:[41,26,7,22,1,2,1,0,97]}.items():
 src,page=('OR_AR_2023',98) if year==2022 else ('OR_AR_2024',102)
 for met,v,label in zip(share_mets,vals,share_rows):obs(year,met,v,'percent',src,page,label,'Combined heat and power denominator; rounded reported shares','Not electricity-only shares; CHP source attribution uses fuel consumption share at plant/unit level.')
for year,vals in {2023:[42158133,39217892,2940241],2024:[45354845,44141989,1212856]}.items():
 for metric,label,v in zip(['heat_plus_power_total_mwh','heat_plus_power_renewable_mwh','heat_plus_power_nonrenewable_mwh'],['Total heat and power generation, MWh','From renewable sources','From non-renewable sources'],vals):obs(year,metric,v,'MWh','OR_AR_2024',102,label,'Combined heat and power','Exact reported MWh; not electricity-only. Do not pool with GWh or sum both representations.')
save('issuer_year_observations.csv',observations)
# A compact three-year view with the fossil target intentionally blank.
wide=[]
for y in [2022,2023,2024]:
 d={'issuer':'Ørsted','year':y}
 for x in observations:
  if x['year']==y and x['is_preferred_observation']=='true':d[x['metric']]=x['value']
 d['fossil_electricity_identified']='no';d['fossil_capacity_identified']='no';wide.append(d)
fields=list(dict.fromkeys(k for r in wide for k in r))
save('issuer_year_panel_view.csv',wide,fields)
# Event ledger separates plant closure, reversible operation status, and fuel capability changes.
events=[
 dict(event_id='orsted_esbjerg_2024',asset='Esbjerg Power Station',country='DK',event_year=2024,event_time_reported='August 2024',event_type='closure',capacity_mw=373,fuel='coal',permanent_retirement_coded='closure_supported; exact unit retirement registration not checked',generation_effect_quantified='no',source_id='OR_AR_2024',source_pages='99;101',evidence='p99 attributes capacity fall mainly to closure of 373 MW Esbjerg; p101 says closed down as of August 2024.',coding_boundary='Physical closure distinct from sale; not a causal green-bond effect.'),
 dict(event_id='orsted_kyndby_2023',asset='Kyndby Peak Load Plant additional unit',country='DK',event_year=2023,event_time_reported='2023',event_type='temporary_return_to_operation',capacity_mw=260,fuel='oil',permanent_retirement_coded='no',generation_effect_quantified='no',source_id='OR_AR_2023',source_pages='95',evidence='Thermal power capacity increased by 260 MW as an extra Kyndby unit was temporarily back in operation.',coding_boundary='Reactivation increases reported capacity without new construction.'),
 dict(event_id='orsted_kyndby_2024',asset='Kyndby Peak Load Plant 260 MW unit',country='DK',event_year=2024,event_time_reported='2024',event_type='taken_out_of_operation',capacity_mw=260,fuel='oil',permanent_retirement_coded='not_established',generation_effect_quantified='no',source_id='OR_AR_2024',source_pages='99',evidence='260 MW Kyndby unit taken out of operation; policy excludes standby or conservation from primary-operation capacity.',coding_boundary='Do not code as permanent retirement; previous temporary return in 2023 is separately recorded.'),
 dict(event_id='orsted_avedore_2024',asset='Avedøre Power Station gas-based part',country='DK',event_year=2024,event_time_reported='2024',event_type='taken_out_of_operation_partial_asset',capacity_mw='',fuel='natural gas',permanent_retirement_coded='not_established',generation_effect_quantified='no',source_id='OR_AR_2024',source_pages='99',evidence='Part of gas-based capacity at Avedøre taken out of operation; narrative does not assign an exact MW to that asset event.',coding_boundary='Do not infer asset MW as residual of rounded category changes.'),
 dict(event_id='orsted_studstrup_2023',asset='Studstrup Power Station',country='DK',event_year=2023,event_time_reported='from April 2023',event_type='gradual_fuel_switch_back_to_biomass',capacity_mw='',fuel='coal_to_biomass',permanent_retirement_coded='no_physical_closure_established',generation_effect_quantified='no',source_id='OR_AR_2024',source_pages='102',evidence='2024 narrative says lower coal generation reflects gradual switch back to biomass from April 2023.',coding_boundary='Fuel substitution at existing asset is distinct from unit retirement.'),
 dict(event_id='orsted_coal_capability_2024',asset='Issuer multi-fuel thermal portfolio',country='DK',event_year=2024,event_time_reported='year-end 2024',event_type='reported_coal_capability_removed',capacity_mw=991,fuel='coal',permanent_retirement_coded='not_a_retirement_total',generation_effect_quantified='no',source_id='OR_AR_2024',source_pages='99',evidence='Coal-capable electricity MW drops from 991 to dash with -991 MW reported change.',coding_boundary='Overlapping multi-fuel capability, not an additive stock of unique coal plants.'),
 dict(event_id='orsted_south_fork_2024',asset='South Fork Wind',country='US',event_year=2024,event_time_reported='2024',event_type='commercial_operation_reached',capacity_mw=132,fuel='offshore_wind',permanent_retirement_coded='not_applicable',generation_effect_quantified='359 GWh reported in finance p6, full project',source_id='OR_AR_2024',source_pages='98',evidence='Annual Report p98 explicitly says COD reached for South Fork (132 MW).',coding_boundary='Conflicts with finance p6 Under construction status; no exact commissioning date inferred from construction endpoint.')]
save('event_ledger.csv',events)
save('cell_provenance.csv',cells)
# Reconciliation and quality profile.
checks=[]
def chk(name,actual,expected,status=None,notes=''):
 checks.append(dict(check=name,actual=actual,expected=expected,status=status or ('PASS' if actual==expected else 'FAIL'),notes=notes))
chk('Project count',len(projects),22)
chk('Unique project IDs',len({x['project_id'] for x in projects}),22)
chk('P6 2024 project allocation sum',sum(x['allocation_2024_dkkm'] or 0 for x in projects),14268,notes='Dashes treated as zero only for arithmetic reconciliation; original raw values preserved.')
chk('P6 cumulative project allocation sum',sum(x['allocation_cumulative_to_2024_dkkm'] for x in projects),71766)
chk('P8 allocation flow sum',sum(x['allocation_dkkm'] for x in a),14268)
chk('P8 distinct projects',len({x['project_id'] for x in a}),14,notes='Report prose says 14 and includes Old 300; 13 positive allocation projects appear in p6 and p8 data rows.')
chk('P7 annual bond rows sum',sum(x['annual_2024_allocation_reported_dkkm'] or 0 for x in bonds),14268,notes='90 DKKm above printed total.')
chk('P7 net proceeds sum',sum(x['net_proceeds_dkkm'] for x in bonds),83184)
chk('P7 cumulative proceeds sum',sum(x['cumulative_allocation_dkkm'] for x in bonds),71766)
chk('P7 unallocated proceeds sum',sum(x['unallocated_dkkm'] or 0 for x in bonds),11418)
chk('Generation populated projects',sum(x['generation_raw']!='-' for x in projects),9)
chk('Generation missing projects',sum(x['generation_raw']=='-' for x in projects),13,notes='Dashes are not generation zeroes; operational assets can also have dashes.')
chk('P9 matrix cell count',len(h),22*17)
chk('P9 matrix cumulative total',sum(x['allocation_dkkm'] or 0 for x in h),57498)
byproject=defaultdict(int);bybond=defaultdict(int);historical=defaultdict(int)
for r in a:byproject[r['project_id']]+=r['allocation_dkkm'];bybond[r['isin']]+=r['allocation_dkkm']
for r in h:historical[r['project_id']]+=r['allocation_dkkm'] or 0
for r in projects:
 chk('Annual project reconciliation: '+r['project_name'],byproject[r['project_id']],r['allocation_2024_dkkm'] or 0)
 chk('Historical + annual = cumulative: '+r['project_name'],historical[r['project_id']]+byproject[r['project_id']],r['allocation_cumulative_to_2024_dkkm'])
for r in bonds:
 old=sum(x['allocation_dkkm'] or 0 for x in h if x['isin']==r['isin'])
 chk('Historical + detail = bond cumulative: '+r['isin'],old+bybond[r['isin']],r['cumulative_allocation_dkkm'])
 chk('Annual summary = bond detail: '+r['isin'],r['annual_2024_allocation_reported_dkkm'] or 0,bybond[r['isin']])
for r in wide:
 y=r['year'];chk(f'{y} electricity category sum',sum(r[k] for k in ['electricity_offshore_wind_gwh','electricity_onshore_wind_gwh','electricity_solar_pv_gwh','electricity_thermal_including_biomass_gwh']),r['electricity_total_gwh'])
 chk(f'{y} electricity capacity category sum',sum(r[k] for k in ['capacity_offshore_wind_mw','capacity_onshore_wind_mw','capacity_solar_pv_mw','capacity_thermal_total_mw']),r['capacity_electricity_total_mw'])
chk('2024 total capacity p97 vs p99',12900,12899,notes='Both observations retained; p99 used in preferred detailed view.')
chk('2024 offshore capacity p97 vs p99',5261,5260,notes='Germany 800 MW in p97 versus 799 MW in p99.')
chk('Badger technology conflicting detail rows',sum(x['project_name']=='Badger' and x['technology_reported_p8'].lower()!='onshore wind' for x in a),0)
save('validation_checks.csv',checks)
profile=dict(projects=len(projects),bonds=len(bonds),annual_allocation_rows=len(a),historical_matrix_cells=len(h),positive_historical_allocation_cells=sum(x['allocation_dkkm']!='' for x in h),issuer_observations=len(observations),provenance_cells=len(cells),events=len(events),checks=len(checks),failed_checks=[x for x in checks if x['status']=='FAIL'])
(P/'quality_profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
print(json.dumps(profile,ensure_ascii=False,indent=2))
