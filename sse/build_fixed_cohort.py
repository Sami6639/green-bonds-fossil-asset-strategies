import csv,json
from pathlib import Path
P=Path(__file__).parent
U23='https://www.sse.com/media/axfpchcj/sse-s-green-bond-report-to-march-2023-green-bonds-1-2-3-4-and-5.pdf'
U24='https://www.sse.com/media/tbjlxitl/sse-green-bond-2024-v4.pdf'
R='https://www.sserenewables.com/'
sources={
'2019':R+'news-and-views/2019/05/sse-full-year-results-renewables/',
'v2019':R+'news-and-views/2019/05/viking-wind-farm-future-financing/',
'g2019':R+'news-and-views/2019/11/consent-for-gordonbush-extension-a-step-towards-first-subsidy-free-onshore-wind-farm-for-sse-renewables/',
'v2020':R+'news-and-views/2020/06/viking-approval-secures-580m-green-recovery-investment-for-shetland/',
's2020':R+'offshore-wind/operational-wind-farms/seagreen/',
'g2020':'https://www.sse.com/media/jqcamklf/sse-32693-annual-report-2020-web-1.pdf',
'2021':'https://www.sse.com/media/xm0nqi43/fy2021_presentation-script-final.pdf',
's2021':'https://www.sse.com/news-and-views/2021/08/scotland-s-largest-offshore-wind-farm-takes-another-step-forward/',
'g2021':R+'news-and-views/2021/04/gordonbush-extension-wind-farm-generates-first-power/',
'2022':R+'media/3iffu2vr/fy2022-statement-combined-final.pdf',
'v2022':R+'news-and-views/2022/07/sse-renewables-secures-cfd-contract-for-viking-energy-wind-farm/',
'g2022':R+'news-and-views/2022/04/sse-steps-up-green-hydrogen-push-with-new-gordonbush-project/',
'v2024':R+'news-and-views/2024/08/landmark-moment-as-sse-powers-up-viking-wind-farm-on-shetland/',
'vfirst':R+'news-and-views/2024/06/first-power-generated-from-viking-wind-farm/',
'sactual':'https://totalenergies.com/newsroom/scotland-totalenergies-commissions-its-biggest-offshore-wind-farm/?lang=eng',
'equinor':'https://www.equinor.com/news/20220628-acquire-triton-power-prepare-transition-hydrogen',
'eqannual':'https://cdn.equinor.com/files/h61q9gi9/global/d6f9b52bd3915255955bbdf09cc238e482693626.pdf?2022-annual-report-on-form-20-f-equinor.pdf='
}
def write(name,rows):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
master=[]
for pid,name,typ,cap,share,fd,cod,codprec,fs,cs in [
('SSE_VIKING','Viking','onshore_wind',443,1,'2020-06-17','2024-08-29','day_announcement',sources['v2020'],sources['v2024']),
('SSE_GORDONBUSH_EXT','Gordonbush Extension','onshore_wind',38,1,'2020-01','2021-08','month',sources['g2020'],U24),
('SSE_SEAGREEN1','Seagreen1','offshore_wind',1075,.49,'2020-06-03','2023-10-17','day_announcement',sources['s2020'],sources['sactual'])]:
 master.append(dict(project_id=pid,project=name,country='United Kingdom',technology=typ,unique_project_capacity_mw=cap,capacity_basis='2024UoP disclosed full project capacity;not sum across bonds',sse_share_in_2024=share,reported_qualifying_mw=527 if share==.49 else cap,investment_decision_date=fd,decision_date_precision='month' if len(fd)==7 else 'day',actual_full_operation_date=cod,operation_date_precision=codprec,investment_source=fs,operation_source=cs,capacity_source=U24,capacity_discrepancy='2024completion release says434MW;2024UoP andJune2024first-power release443MW;unresolved' if pid=='SSE_VIKING' else '',scope_note='SSE share changed over time;see snapshots;capacity not attributable pro rata to bond proceeds'))
write('fixed_cohort_project_master.csv',master)
# Disclosure-year snapshots are NOT fiscal year-end measurements. Dates and measurement periods are separate.
S=[]
def add(pid,year,obs,status,u,locator='',mw=None,share=None,out=None,outputperiod='',forecast='',note=''):
 S.append(dict(project_id=pid,disclosure_year=year,evidence_date_or_period=obs,project_stage=status,source_url=u,source_locator=locator,disclosed_full_capacity_mw=mw,disclosed_sse_share=share,qualifying_output_gwh=out,output_measurement_period=outputperiod,forecast_full_operation=forecast,annual_bond_allocation_flow_gbp_m=None,missing_finance_note='PreGB5 snapshots have no verified cohort-specific green-bond allocation;do not zero-fill',notes=note))
V,G,Sg=[r['project_id'] for r in master]
add(V,2019,'2019-05-30','development_financing_agreement',sources['v2019'],note='Previously50:50funded;SSE agrees all future funding;no legal ownership effective date inferred')
add(G,2019,'2019-11-06','revised_consent_before_FID',sources['g2019'],note='Approval5November;FID still prospective')
add(Sg,2019,'2019-05','development',sources['2019'],share=1,note='SSE acquired remaining50pct September2018;not new physical capacity')
add(V,2020,'2020-06-17','conditional_FID',sources['v2020'],mw=443,share=1,forecast='early2024',note='Conditional transmission/code approvals;GBP580m project investment not greenbond proceeds')
add(G,2020,'2020annualreport;Januarydecision','construction',sources['g2020'],'printed20',mw=38,forecast='spring2021')
add(Sg,2020,'2020-06-03','FID_and_construction',sources['s2020'],mw=1075,share=.49,note='Retrospective operatorhistory;51pct sale toTotal atFID separately verifiedAnnual2021')
add(V,2021,'FY2021results_presentation','construction',sources['2021'],'domesticgrowth',mw=443,forecast='autumn2024')
add(G,2021,'2021-04','first_power',sources['g2021'],mw=38,forecast='mid2021',note='First power distinct fromAugust2021full operation reported later')
add(Sg,2021,'2021-08','construction',sources['s2021'],mw=1075,share=.49,forecast='2023')
add(V,2022,'2022-07','construction_CfD_award',sources['v2022'],mw=443,share=1,note='220MW CfD volume is subset of physical443MW;not additional capacity')
add(G,2022,'FY2022results','commissioned_during_fiscal_year',sources['2022'],mw=38,note='Actual operationalmonthAugust2021 from subsequentUoP')
add(Sg,2022,'FY2022results_afterApril2022','construction',sources['2022'],mw=1075,share=.49,forecast='April2023',note='Forecast followinginstallationvessel incident;not realised COD')
for pid,mw,sh,out,forecast,stage in [(V,443,1,0,'2024-08','construction'),(G,38,1,64.3,'','operational'),(Sg,1075,.49,345.3,'2023-08','construction_with_generation')]:
 add(pid,2023,'2023-03-31',stage,U23,'table6 printed9',mw,sh,out,'2022-04-01/2023-03-31',forecast)
for pid,mw,sh,out,forecast,stage in [(V,443,1,0,'2024-08','construction'),(G,38,1,51.3,'','operational'),(Sg,1075,.49,763,'','operational')]:
 add(pid,2024,'2024-03-31',stage,U24,'table6 printed9;PDF10',mw,sh,out,'2023-04-01/2024-03-31',forecast,note='Viking actualAugust2024completion is later event;not backfilled intoMarch2024status')
write('fixed_cohort_annual_disclosure_snapshots.csv',S)
# Financial linkage: repeated reporting stocks; same project can link to more than one instrument.
L=[]
for yr in [2023,2024]:
 for pid,name,amount in [(V,'Viking',166),(G,'Gordonbush Extension',37.2),(Sg,'Seagreen1',340.7)]:
  L.append(dict(project_id=pid,report_year=yr,bond_group='GB5',isin='XS2510903862',settlement_date='2022-08-01',allocation_stock_gbp_m=amount,allocation_status='reported_numeric',finance_type='refinancing',project_is_physical_new_build=True,allocation_flow_gbp_m=None,source_url=U23 if yr==2023 else U24,source_locator='table6',date_source=U24+'#Table1',deduplication_key=f'{pid}|GB5|{yr}',warning='same allocation repeated acrossyears;do not sum as annualflow;MWkept inprojectmaster'))
for pid,amount in [(V,202.2),(Sg,437.6),(G,None)]:
 L.append(dict(project_id=pid,report_year=2024,bond_group='GB6',isin='XS2675685700',settlement_date='2023-09-05',allocation_stock_gbp_m=amount,allocation_status='reported_dash_no_numeric_allocation' if amount is None else 'reported_numeric',finance_type='refinancing',project_is_physical_new_build=True,allocation_flow_gbp_m=None,source_url=U24,source_locator='table6',date_source=U24+'#Table1',deduplication_key=f'{pid}|GB6|2024',warning='Source dash: no GB6 allocation established. Shared physical attributes do not establish a funded bond-project link; do not impute zero.' if amount is None else 'Shared source-table physical attributes are repeated only in analytical long form; deduplicate project MW and project-year GWh.'))
write('fixed_cohort_bond_project_links.csv',L)
E=[]
for r in master:
 for typ,date,src in [('investment_decision',r['investment_decision_date'],r['investment_source']),('full_operation',r['actual_full_operation_date'],r['operation_source'])]:
  E.append(dict(project_id=r['project_id'],event_type=typ,event_date=date,date_precision='month' if len(date)==7 else 'day_or_announcement_day',source_url=src,notes='Actual or dateddecision;distinct fromforecastinannualsnapshot'))
E.append(dict(project_id=V,event_type='first_power',event_date='2024-06',date_precision='month',source_url=sources['vfirst'],notes='Separate fromAugustfulloperations'))
E.append(dict(project_id=Sg,event_type='first_power',event_date='2022-08',date_precision='month',source_url=sources['s2020'],notes='Separate fromOctober2023fulloperations'))
write('fixed_cohort_actual_milestones.csv',E)
write('triton_counterparty_corroboration.csv',[dict(asset='Triton Power',event='acquisition',agreement_announcement_date='2022-06-28',completion_date='2022-09-01',sse_ownership_fraction=.5,equinor_ownership_fraction=.5,saltend_gross_capacity_mw=1200,classification='ownership_transfer_existing_gas_assets_not_new_build',prior_strategy='Plannedhydrogenblendingfrom2027;prospectiveambition_not_realisedconversion',counterparty_source=sources['equinor'],audited_counterparty_source=sources['eqannual'],audited_locator='Equinor2022Form20-F printed85',independence='Counterpartyprimarysource;separatecompanyfromSSE;notindependentimpactevaluation')])
validation={'unique_projects':3,'annual_disclosure_rows':len(S),'bond_project_snapshot_rows':len(L),'unique_project_capacity_mw_on_UoP_basis':1556,'reported_qualifying_capacity_mw_on_UoP_basis':1008,'note':'Viking434vs443unresolved;1556notbond-attributable;529? no speculative reconciliation','duplicate_project_years':len(S)-len({(r['project_id'],r['disclosure_year']) for r in S})}
validation['note']='Viking434vs443unresolved;1556notbond-attributable;reportedSeagreen527rounded'
(P/'fixed_cohort_validation.json').write_text(json.dumps(validation,indent=2))
print(json.dumps(validation,indent=2))
