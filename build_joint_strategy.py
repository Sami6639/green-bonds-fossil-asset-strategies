"""Reproducible, bounded within-case interval analysis; no downloads or causal model.

All adjacent available finance observations are joined to the matching issuer
accounting interval. A zero in an identified-event field means no such event
in the bounded ledger, never exhaustive proof of absence. Missing = unresolved.
"""
from pathlib import Path
import os, json, hashlib, datetime, calendar, textwrap
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-utility-strategy')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/utility-strategy-cache')
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib.lines import Line2D
P=Path(__file__).parent; O=P/'main_exhibits'; J=P/'joint_strategy'; J.mkdir(exist_ok=True)
INPUTS=[]
def rd(s):
 INPUTS.append(s); return pd.read_csv(P/s,keep_default_na=False)
def save(d,n):d.to_csv(J/n,index=False,lineterminator='\n')
def f(x):return float(x)
def ss(x):return '; '.join(sorted(set(str(v) for v in x if str(v))))
def check(name,ok,detail=''):
 CHECKS.append({'check':name,'pass':bool(ok),'detail':str(detail)})
 assert ok, name+': '+str(detail)
CHECKS=[]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'utility-strategy-20261010'})
# Finance observations: source-specific status semantics remain separate.
en=rd('enel/green_2019_issue_full_annual_panel.csv')
en=en[en.present_in_allocation_table==1].copy()
ens=rd('enel/green_2019_issue_annual_summary.csv').set_index('report_year')
reassign=rd('enel/green_2019_issue_reassignment_disclosures.csv')
encont=rd('enel/green_2019_issue_pool_continuity.csv')
ib=rd('iberdrola/history_2019_2024/matched_green_hybrid_projects_2019_2024.csv')
ibmoney=rd('iberdrola/history_2019_2024/matched_green_hybrid_2019_2024.csv')
ibmoney=ibmoney[ibmoney.field=='investment_allocated_stock'].set_index('report_year')
ibdelivery=rd('iberdrola/history_2019_2024/matched_project_delivery_evidence.csv')
links=rd('sse/fixed_cohort_bond_project_links.csv'); links=links[links.bond_group=='GB5'].copy()
snap=rd('sse/fixed_cohort_annual_disclosure_snapshots.csv')
snap=snap[snap.disclosure_year.isin([2023,2024])].rename(columns={'disclosure_year':'report_year','source_url':'status_source_url','source_locator':'status_source_locator'})
sm=links.merge(snap,on=['project_id','report_year'],validate='one_to_one')
sm.allocation_stock_gbp_m=pd.to_numeric(sm.allocation_stock_gbp_m)
fin=[]
for y,g in en.groupby('report_year'):
 amounts=pd.to_numeric(g.allocation_EUR_m_reported)
 fin.append(dict(issuer='Enel',instrument='2019 green use-of-proceeds issue',observation_year=int(y),cutoff_date='',observation_basis='observed report vintage; precise allocation cutoff not independently established',currency='EUR',reported_allocation_stock_m=f(ens.loc[y,'source_reported_total_EUR_m']),line_sum_allocation_stock_m=amounts.sum(),report_lines=len(g),named_project_lines=sum(g.row_type=='named_project'),operating_status_lines=sum(g.project_status_normalized=='operating'),operating_status_amount_m=amounts[g.project_status_normalized=='operating'].sum(),operating_status_share_of_line_sum_pct=100*amounts[g.project_status_normalized=='operating'].sum()/amounts.sum(),full_operation_amount_m='',full_operation_share_pct='',money_weights_status='rounded project-line amounts observed; eight underlying hydro identities unresolved',maturity_semantics='source-reported operating status; not harmonized full COD',source_url=ss(g.source_url),source_locator=ss(g.source_pdf_page)))
for y,g in ib.groupby('report_year'):
 fin.append(dict(issuer='Iberdrola',instrument='2019 hybrid XS1890845875',observation_year=int(y),cutoff_date='',observation_basis='observed report vintage; precise allocation cutoff not independently established',currency='EUR',reported_allocation_stock_m=f(ibmoney.loc[y,'value']),line_sum_allocation_stock_m='',report_lines=len(g),named_project_lines=len(g),operating_status_lines='',operating_status_amount_m='',operating_status_share_of_line_sum_pct='',full_operation_amount_m='',full_operation_share_pct='',money_weights_status='project-level money not disclosed; continuity unidentified',maturity_semantics='independent COD evidence: Wikinger 2017; East Anglia ONE 2020; no monetary maturity weights estimated',source_url=ss(g.source_url),source_locator=ss(g.pdf_page_1_based)))
for y,g in sm.groupby('report_year'):
 full=g.loc[g.project_stage=='operational','allocation_stock_gbp_m'].sum(); total=g.allocation_stock_gbp_m.sum()
 fin.append(dict(issuer='SSE',instrument='GB5 XS2510903862',observation_year=int(y),cutoff_date=f'{y}-03-31',observation_basis='dated fiscal-year-end allocation and maturity stock',currency='GBP',reported_allocation_stock_m=total,line_sum_allocation_stock_m=total,report_lines=len(g),named_project_lines=len(g),operating_status_lines='',operating_status_amount_m='',operating_status_share_of_line_sum_pct='',full_operation_amount_m=full,full_operation_share_pct=100*full/total,money_weights_status='three project allocation amounts observed at both cuts',maturity_semantics='full operation separated from construction with generation and explicitly reported zero production',source_url=ss(g.source_url),source_locator=ss(g.source_locator)))
fin=pd.DataFrame(fin)
fin['allocation_precision_note']=fin.issuer.map({'Enel':'Published table total rounded to EUR1m (986); original 2019 summary is EUR985.6m. Zero changes denote continuity at reported precision, not exact underlying monetary constancy.','Iberdrola':'Published total EUR800m; individual monetary weights unavailable.','SSE':'Project amounts reported to GBP0.1m; endpoint comparisons use those reported amounts.'})
save(fin,'finance_observation_states.csv')
check('finance_observations_6_6_2',fin.groupby('issuer').size().to_dict()=={'Enel':6,'Iberdrola':6,'SSE':2})
# Identified fossil-event inventories retain event-specific source and capacity bases.
iev=rd('iberdrola/history_2019_2024/fossil_capacity_event_ledger.csv')
sev=rd('sse/capacity_2019_2024_event_contributions.csv')
eev=rd('enel/coal_decision_event_dossier.csv')
events=[]
for r in iev.to_dict('records'):
 events.append(dict(issuer='Iberdrola',event_id=r['event_id'],accounting_year=int(r['year']),event_date_reported=r['event_date_reported'],date_precision=r['date_precision'],asset=r['asset_or_project'],event_class=r['event_class'],signed_bridge_mw=r['capacity_delta_mw'],standalone_event_mw='',mw_basis='reported technology capacity; consolidated plus proportional investees',common_window_inclusion='included',source_url=r['source_url'],source_locator='PDF '+str(r['pdf_page_1_based']),notes=r['notes']))
for k,r in enumerate(sev.to_dict('records')):
 inside=int(r['bridge_fiscal_year'])==2024
 events.append(dict(issuer='SSE',event_id=f'SS_{r["bridge_fiscal_year"]}_{k+1:02d}',accounting_year=int(r['bridge_fiscal_year']),event_date_reported=r['event_date'],date_precision='day' if len(r['event_date'])==10 else 'month' if len(r['event_date'])==7 else 'fiscal_year',asset=r['asset'],event_class=r['event_type'],signed_bridge_mw=r['signed_reported_portfolio_mw'],standalone_event_mw='',mw_basis='Thermal reported portfolio; Transmission Entry Capacity, owned plus JV share; fuel '+r['fuel'],common_window_inclusion='included' if inside else 'antecedent_context_only',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']))
for r in eev.to_dict('records'):
 year=int(r['event_id'].split('_')[2])
 events.append(dict(issuer='Enel',event_id=r['event_id'],accounting_year=year,event_date_reported=r['implementation_date'],date_precision='source-specific; legal date may differ from accounting recognition',asset=r['asset'],event_class=r['event_type'],signed_bridge_mw='',standalone_event_mw=r['event_capacity_MW'],mw_basis=r['event_MW_basis'],common_window_inclusion='included' if year>=2020 else 'antecedent_context_only',source_url=r['implementation_url'],source_locator='PDF '+str(r['implementation_pdf_page']),notes=r['boundary_note']+' Associated regional stock change is not automatically a same-basis event contribution.'))
events=pd.DataFrame(events)
# The prior extract gives December; the added prospectus cross-check reveals September/December conflict.
mask=(events.issuer=='SSE') & (events.asset=='Tarbert old oil station')
events.loc[mask,'event_date_reported']='2023; month unresolved (September/December)'
events.loc[mask,'date_precision']='conflicting month disclosures; fiscal-interval membership certain'
events.loc[mask,'source_url']=events.loc[mask,'source_url']+'; https://www.sse.com/media/ej5l4w14/sse-plc_prospectus-2024_final-version.pdf'
events.loc[mask,'source_locator']=events.loc[mask,'source_locator']+'; prospectus printed pp.105–106'
events.loc[mask,'notes']=events.loc[mask,'notes']+' Added audit: prospectus p.105 says end-December2023, p.106 footnote says September2023. No exact month chosen; both in matched fiscal interval.'
save(events,'bounded_fossil_event_inventory.csv')
# Exhaustive over the identified rows in the input ledgers, not over real-world events.
check('event_row_coverage',len(events)==len(iev)+len(sev)+len(eev))
bridge=rd('iberdrola/history_2019_2024/annual_capacity_bridges_2020_2024.csv')
bridge=bridge[bridge.technology=='Gas+Cogeneration+Coal'].set_index('year')
ecoal=rd('enel/coal_capacity_regional_bridge_2019_2024.csv');ecoal=ecoal[ecoal.region=='Group'].set_index('flow_year')
stocks=rd('sse/capacity_2019_2024_fuel_stratified.csv').set_index('fiscal_year_end')
rows=[]
for issuer in ['Enel','Iberdrola','SSE']:
 ff=fin[fin.issuer==issuer].set_index('observation_year')
 years=list(ff.index)
 for a,b in zip(years[:-1],years[1:]):
  x=ff.loc[a];z=ff.loc[b]; g=events[(events.issuer==issuer)&(events.accounting_year==b)&(events.common_window_inclusion=='included')]
  base=dict(interval_id=f'{issuer.upper()}_{a}_{b}',issuer=issuer,instrument=x.instrument,opening_observation_year=a,closing_observation_year=b,finance_window=f'observed {a}/{b} report vintages' if issuer!='SSE' else '2023-03-31 / 2024-03-31',fossil_interval_start=f'{a}-12-31' if issuer!='SSE' else f'{a}-03-31',fossil_interval_end=f'{b}-12-31' if issuer!='SSE' else f'{b}-03-31',temporal_alignment='annual report-vintage alignment; finance intra-year timing unresolved' if issuer!='SSE' else 'exact matched fiscal cuts; events after opening and on/before closing',currency=x.currency,opening_allocation_stock_m=x.reported_allocation_stock_m,closing_allocation_stock_m=z.reported_allocation_stock_m,allocation_stock_change_m=z.reported_allocation_stock_m-x.reported_allocation_stock_m,opening_report_lines=x.report_lines,closing_report_lines=z.report_lines,entered_report_lines=0,exited_report_lines=0,common_line_allocations_changed='',disclosed_reassignment_m='',reassignment_precision='',financial_state='',renewable_maturity_observation='',full_operation_share_open_pct=x.full_operation_share_pct,full_operation_share_close_pct=z.full_operation_share_pct,full_operation_share_change_pp='',fossil_scope='',opening_capacity_mw='',closing_capacity_mw='',net_change_mw='',identified_physical_closure_mw='',identified_new_installation_or_commissioning_mw='',identified_acquisition_or_rights_mw='',identified_disposal_mw='',identified_uprating_mw='',identified_reporting_or_reclassification_mw='',unresolved_net_residual_mw='',event_ids=ss(g.event_id),event_classes=ss(g.event_class),gross_event_coverage='bounded source-ledger inventory; not proved exhaustive',finance_fossil_link='no direct selected-bond-to-fossil-event link established in bounded evidence',documented_other_link='',joint_interpretation='',finance_source_urls=ss([x.source_url,z.source_url]),fossil_source_urls='',source_files='')
  if issuer=='Iberdrola':
   o=ib[ib.report_year==a].set_index('project_standardised');n=ib[ib.report_year==b].set_index('project_standardised')
   base.update(entered_report_lines=len(n.index.difference(o.index)),exited_report_lines=len(o.index.difference(n.index)),financial_state='same two names and EUR 800m total; project monetary continuity unresolved',fossil_scope='reported gas + cogeneration + coal; consolidated plus proportional investees; pre-COD and operating-rights caveats retained',source_files='iberdrola/history_2019_2024/matched_green_hybrid_2019_2024.csv; iberdrola/history_2019_2024/matched_green_hybrid_projects_2019_2024.csv; iberdrola/history_2019_2024/annual_capacity_bridges_2020_2024.csv; iberdrola/history_2019_2024/fossil_capacity_event_ledger.csv')
   r=bridge.loc[b]
   base.update(opening_capacity_mw=r.opening_capacity_mw,closing_capacity_mw=r.closing_capacity_mw,net_change_mw=r.observed_net_change_mw,identified_physical_closure_mw=r.physical_retirement,identified_new_installation_or_commissioning_mw=r.physical_installation_completion+r.commissioning,identified_acquisition_or_rights_mw=r.acquisition_existing_asset+r.acquisition_or_operating_rights_existing_asset,identified_disposal_mw=r.divestment_ownership_transfer,identified_uprating_mw=r.modernisation_uprating,identified_reporting_or_reclassification_mw=r.technology_reclassification,unresolved_net_residual_mw=r.unexplained_mechanism_net_residual_mw,fossil_source_urls=ss([r.opening_source_url,r.closing_source_url]+list(g.source_url)))
   base['renewable_maturity_observation']='East Anglia ONE reaches COD during 2020, verified retrospectively in Factbook 2021; Wikinger COD 2017; maturity weights unavailable' if b==2020 else 'No additional COD event identified for the two projects after 2020; annual operating-state or money-weight continuity not independently recoded'
   base['joint_interpretation']={2020:'Stable finance names/total accompanies coal closure offset by larger identified gas installation and acquisition/rights additions; net reported fossil stock rises.',2021:'Stable finance names/total accompanies a 6 MW unresolved cogeneration reduction; no closure/disposal class is inferred.',2022:'Stable finance names/total accompanies 514 MW gas commissioning.',2023:'Stable finance names/total accompanies unchanged aggregate fossil stock; no-change stock does not exclude offsetting gross events.',2024:'Stable finance names/total accompanies ownership disposal, uprating and unresolved reduction; the net stock decline is not a retirement total.'}[b]
  elif issuer=='Enel':
   o=en[en.report_year==a].set_index('project_id');n=en[en.report_year==b].set_index('project_id');common=o.index.intersection(n.index)
   changed=sum(pd.to_numeric(o.loc[common,'allocation_EUR_m_reported'])!=pd.to_numeric(n.loc[common,'allocation_EUR_m_reported']))
   rr=reassign[reassign.disclosure_report_year==b]
   base.update(entered_report_lines=len(n.index.difference(o.index)),exited_report_lines=len(o.index.difference(n.index)),common_line_allocations_changed=int(changed),disclosed_reassignment_m='' if rr.empty else rr.allocation_moved_EUR_m.sum(),reassignment_precision='' if rr.empty else ss(rr.precision),financial_state='reported allocation total unchanged; substitution disclosed' if not rr.empty else 'reported allocation total and line identities unchanged; aggregate underlying identities unresolved',renewable_maturity_observation=f'Source-reported operating lines {int(x.operating_status_lines)} → {int(z.operating_status_lines)}; this is not a harmonized full-COD count',fossil_scope='coal only; group consolidated net-efficient installed capacity; other fossil technologies outside this joint branch',opening_capacity_mw=ecoal.loc[b,'opening_coal_MW'],closing_capacity_mw=ecoal.loc[b,'closing_coal_MW'],net_change_mw=ecoal.loc[b,'change_MW'],fossil_source_urls=ss([ecoal.loc[b,'source_url']]+list(g.source_url)),source_files='enel/green_2019_issue_full_annual_panel.csv; enel/green_2019_issue_reassignment_disclosures.csv; enel/coal_capacity_regional_bridge_2019_2024.csv; enel/coal_decision_event_dossier.csv')
   base['documented_other_link']='Renewable subsidiary deconsolidation → selected allocation-pool replacement; no direct coal-event connection established' if b==2023 else ''
   base['joint_interpretation']={2020:'Allocation substitution and reported project maturation coexist with coal-stock decline and named closure records; exact event-MW reconciliation remains unresolved.',2021:'Unchanged allocation names/total coexist with coal-stock decline and closure records; changes in coal do not require observed pool replacement.',2022:'Unchanged allocation names/total coexist with further coal-stock decline and Bocamina II closure; gross 350 MW is not equated to net 320 MW.',2023:'Deconsolidation-related allocation replacement coexists with coal-stock decline and coal closures; documented link concerns renewable ownership/allocation, not the coal closures.',2024:'Reported allocation identities/total and coal stock are unchanged; no named coal event identified in this bounded ledger, not proof of no gross activity.'}[b]
  else:
   o=sm[sm.report_year==a].set_index('project_id');n=sm[sm.report_year==b].set_index('project_id')
   base.update(common_line_allocations_changed=int(sum(o.allocation_stock_gbp_m!=n.allocation_stock_gbp_m)),financial_state='same three names and all project allocation amounts; GBP 543.9m at both cuts',renewable_maturity_observation='Seagreen moves from construction with generation to full operation; Gordonbush remains fully operational; Viking remains construction with explicit zero output',full_operation_share_change_pp=z.full_operation_share_pct-x.full_operation_share_pct,fossil_scope='reported Thermal gas/oil portfolio; Transmission Entry Capacity, owned plus JV share',opening_capacity_mw=stocks.loc[a,'fossil_categories_capacity_mw'],closing_capacity_mw=stocks.loc[b,'fossil_categories_capacity_mw'],net_change_mw=stocks.loc[b,'fossil_categories_capacity_mw']-stocks.loc[a,'fossil_categories_capacity_mw'],identified_physical_closure_mw=g.loc[g.event_class.isin(['physical_retirement','physical_closure']),'signed_bridge_mw'].astype(float).sum(),identified_new_installation_or_commissioning_mw=0,identified_acquisition_or_rights_mw=0,identified_disposal_mw=0,identified_uprating_mw=0,identified_reporting_or_reclassification_mw=0,unresolved_net_residual_mw=0,fossil_source_urls=ss([stocks.loc[a,'source_url'],stocks.loc[b,'source_url']]+list(g.source_url)),source_files='sse/fixed_cohort_bond_project_links.csv; sse/fixed_cohort_annual_disclosure_snapshots.csv; sse/capacity_2019_2024_event_contributions.csv; sse/capacity_2019_2024_fuel_stratified.csv',joint_interpretation='A fixed refinancing allocation stock matures while Tarbert retires in the same fiscal interval. Keadby 2 commissioning and Triton acquisition precede the opening cut and are antecedent context only.')
  base['allocation_precision_note']=x.allocation_precision_note
  if issuer=='Enel':
   base['financial_state']=base['financial_state'].replace('reported allocation total','rounded report-table allocation total (EUR986m)')
   base['allocation_stock_change_basis']='difference at published EUR1m table precision; original 2019 summary EUR985.6m retained for reallocation share only'
  else: base['allocation_stock_change_basis']='difference in reported stocks; not inferred new annual finance'
  rows.append(base)
q=pd.DataFrame(rows); save(q,'matched_interval_panel.csv')
# Algorithmic pattern audit; labels are interval findings, never issuer types.
pattern=[]
for r in q.to_dict('records'):
 if r['issuer']=='Enel':
  fossil='unchanged coal stock; gross inventory unresolved' if r['net_change_mw']==0 else 'coal decline with closure records; full gross bridge unresolved'
 else:
  classes=[]
  for c,label in [('identified_physical_closure_mw','closure'),('identified_new_installation_or_commissioning_mw','installation/commissioning'),('identified_acquisition_or_rights_mw','acquisition/rights'),('identified_disposal_mw','disposal'),('identified_uprating_mw','uprating'),('identified_reporting_or_reclassification_mw','reporting/classification'),('unresolved_net_residual_mw','unresolved reduction')]:
   if r[c]!='' and r[c]!=0:classes.append(label)
  fossil=' + '.join(classes) if classes else 'unchanged stock; no gross event identified'
 pattern.append(dict(interval_id=r['interval_id'],issuer=r['issuer'],closing_year=r['closing_observation_year'],financial_total_change_m=r['allocation_stock_change_m'],identity_change_observed=bool(r['entered_report_lines'] or r['exited_report_lines']),project_money_continuity='unidentified' if r['issuer']=='Iberdrola' else 'changed' if r['entered_report_lines'] or r['exited_report_lines'] or r['common_line_allocations_changed'] else 'observed at report-line precision only' if r['issuer']=='Enel' else 'observed at both cuts',fossil_event_mixture=fossil,net_capacity_change_mw=r['net_change_mw'],classification_scope='interval-specific; no company ranking or causal estimate'))
pattern=pd.DataFrame(pattern); save(pattern,'interval_pattern_audit.csv')
check('all_adjacent_pairs_and_no_extra_sse',q.groupby('issuer').size().to_dict()=={'Enel':5,'Iberdrola':5,'SSE':1})
check('unique_interval_grain',not q.interval_id.duplicated().any())
check('all_selected_allocation_totals_unchanged',(q.allocation_stock_change_m.abs()<1e-8).all())
check('SSE_only_Tarbert_in_window',len(q[q.issuer=='SSE'].iloc[0].event_ids.split(';'))==1 and 'Tarbert old oil station' in events[(events.issuer=='SSE')&(events.common_window_inclusion=='included')].asset.tolist())
check('SSE_preopening_Keadby_Triton',all(events[events.asset.isin(['Keadby2 CCGT','Triton Saltend and Indian Queens'])].common_window_inclusion=='antecedent_context_only'))
for r in q[q.issuer!='Enel'].to_dict('records'):
 cols=['identified_physical_closure_mw','identified_new_installation_or_commissioning_mw','identified_acquisition_or_rights_mw','identified_disposal_mw','identified_uprating_mw','identified_reporting_or_reclassification_mw','unresolved_net_residual_mw']
 check('interval_bridge_'+r['interval_id'],abs(sum(r[c] for c in cols)-r['net_change_mw'])<1e-8)
check('Enel_gross_not_imputed',q[q.issuer=='Enel'].identified_physical_closure_mw.eq('').all())
check('IB_unresolved_periods_retained',list(q[q.interval_id.isin(['IBERDROLA_2020_2021','IBERDROLA_2023_2024'])].unresolved_net_residual_mw)==[-6,-29])
check('unchanged_periods_retained',set(q[q.net_change_mw==0].interval_id)=={'ENEL_2023_2024','IBERDROLA_2022_2023'})
check('SSE_maturity_same_denominator',abs(q[q.issuer=='SSE'].full_operation_share_change_pp.iloc[0]-340.7/543.9*100)<1e-9)
# Compact canonical Table 2, backed by every interval rather than selected anecdotes.
contract=json.loads((O/'canonical_manuscript_exhibits.json').read_text())
# Old matrices remain exact supplements; pipeline regenerates originals before this script.
for old,new in [('table2_claim_evidence_synthesis.csv','appendix_claim_evidence_synthesis.csv'),('table3_finance_delivery_comparison.csv','appendix_finance_delivery_comparison.csv')]:
 (J/new).write_bytes((O/old).read_bytes())
headers=['Core case and matched window','Finance and renewable trajectory','Fossil decision mixture in that window','Joint finding and limit']
trows=[
 ['Enel: five adjacent 2019–2024 report-vintage comparisons','Approximately €986m total throughout; about €7m substituted in 2020 and €156.86m in 2023. Operating-status lines rise from 5/16 to 14/15 in 2020; this is not a full-COD measure.','Annual coal-stock changes: −2,792, −1,993, −320, −1,963 and 0 MW. Named closures accompany the declines, but event MW do not form a fully reconciled gross bridge.','Coal declines occur both with and without allocation substitution; 2024 preserves an unchanged observation. The documented 2023 link is renewable deconsolidation to allocation replacement, not financing to coal closure.'],
 ['Iberdrola: five adjacent 2019–2024 report-vintage comparisons','€800m and two names remain; project money weights are unidentified. East Anglia ONE reaches COD in 2020.','2020: −874 MW coal closure, +779 installation and +243 acquisition/rights, net +148. 2021: −6 unresolved. 2022: +514 commissioning. 2023: 0 net. 2024: −8,494 disposal, +17 uprating and −29 unresolved, net −8,506.','The same observed financing names/total accompanies closure with expansion, later commissioning and ownership exit. Zero net change does not prove inactivity; sale is not physical retirement.'],
 ['SSE: 31 March 2023–31 March 2024 only','GB5 retains all three allocations, £543.9m. Full-operation share rises from 6.84% to 69.48%; Seagreen supplies the 62.64 percentage-point change.','Thermal gas/oil capacity falls from 6,830 to 6,210 MW with Tarbert’s −620 MW closure. Keadby 2 +893 MW and Triton +670 MW occurred before the opening cut.','A fixed refinancing stock matures alongside an in-window closure. Earlier gas expansion remains antecedent context; no bond-caused retirement or exhaustive gross-event inventory is established.']]
note='All available adjacent finance observations are included: five Enel pairs, five Iberdrola pairs and one SSE pair. Enel and Iberdrola are annual report-vintage alignments, not exact within-year financing dates; fossil changes use the destination calendar year. SSE uses exact 31 March cuts and events in (opening, closing]. Zeros describe observed stock changes or bounded identified ledgers. Fossil boundaries differ across cases and are never pooled. Enel’s reported operating status is not equated with SSE full operation. Complete interval, event, source and unresolved-state records accompany the data package.'
contract['table_order'][1]=dict(number=2,title='Matched financing and fossil-asset decision sequences',file='table2_matched_strategy_sequences.csv',headers=headers,rows=trows,note=note)
pd.DataFrame(trows,columns=headers).to_csv(O/'table2_matched_strategy_sequences.csv',index=False)
# Decision-chain Table 3 arrives as a separate source-verified contract.
dc=P/'decision_evidence'/'table3_decision_chain_synthesis.csv'
if dc.exists():
 d=rd('decision_evidence/table3_decision_chain_synthesis.csv')
 # Presentation-only wording; source-derived decision records remain unchanged.
 d.iloc[:,0]=d.iloc[:,0].str.replace('Australia/Hellas','Australia and Hellas',regex=False).str.replace('investment/commissioning','investment and commissioning',regex=False)
 note_path='decision_evidence/table3_decision_chain_note.txt'; INPUTS.append(note_path)
 t3=dict(number=3,title='Selected decision chains and documented financial links',file='table3_decision_chain_synthesis.csv',headers=['Case and decision','Declared rationale','Documented financing link','Ownership or physical outcome and boundary'],rows=d.iloc[:,:4].values.tolist(),note=(P/note_path).read_text().split('\n\n',1)[-1].strip())
 contract['table_order'][2]=t3
 pd.DataFrame(t3['rows'],columns=t3['headers']).to_csv(O/t3['file'],index=False)
# Figure 2: all observed intervals; separate panels/scopes avoid misleading common MW scales.
fig,axes=plt.subplots(3,1,figsize=(6.27,7.3),gridspec_kw={'height_ratios':[2.7,2.7,1.6]})
colors={'unchanged':'#e7eeee','mixed':'#deebe8','unknown':'#f3eada','replace':'#d9e6f0'}
for ax,issuer in zip(axes,['Enel','Iberdrola','SSE']):
 g=q[q.issuer==issuer]
 ax.axis('off');ax.set_title(issuer+(' | coal only' if issuer=='Enel' else ' | reported fossil technology portfolio' if issuer=='Iberdrola' else ' | reported Thermal gas/oil'),loc='left',fontweight='bold',fontsize=10,pad=8)
 if issuer!='SSE':
  collabels=['2019→20','2020→21','2021→22','2022→23','2023→24']
  flabels=['~€7m\nsubstituted','Names/total\nunchanged','Names/total\nunchanged','€156.86m\nsubstituted','Names/total\nunchanged'] if issuer=='Enel' else ['Two names\n€800m']*5
  fsl=['−2,792\nClosure records','−1,993\nClosure records','−320\nClosure records','−1,963\nClosure records','0\nNo event identified'] if issuer=='Enel' else ['+148\nClosure + additions','−6\nUnresolved','+514\nCommissioning','0\nNo event identified','−8,506\nDisposal + other']
  cell=[flabels,fsl]
  tab=ax.table(cellText=cell,rowLabels=['Finance','Fossil MW'],colLabels=collabels,cellLoc='center',rowLoc='center',bbox=[.11,.17,.89,.78],colWidths=[.178]*5)
  tab.auto_set_font_size(False);tab.set_fontsize(7.0)
  for (ri,ci),c in tab.get_celld().items():
   c.set_edgecolor('white');c.set_linewidth(2)
   c.set_facecolor('#355770' if ri==0 else '#e8eef1' if ri==1 else '#e5eeea');c.get_text().set_color('white' if ri==0 else '#17272f')
   if ri==0:c.get_text().set_fontweight('bold')
  tail='Source-reported operating lines: 5/16 → 14/15 → 14/15 → 15/15 → 15/15 → 15/15.\nGross closure MW cannot be fully reconciled to net-efficient stock changes.' if issuer=='Enel' else 'Project money weights unavailable in every vintage; East Anglia ONE COD in 2020.\n2020 additions include pre-COD installation; 2024 includes −29 MW unresolved.'
  ax.text(.11,.02,tail,transform=ax.transAxes,fontsize=7.2,va='bottom')
 else:
  ax.text(.015,.82,'31 March 2023 → 31 March 2024',fontsize=9,fontweight='bold',transform=ax.transAxes)
  ax.text(.015,.54,'£543.9m and three project allocations unchanged\nFull-operation share: 6.84% → 69.48% (+62.64 pp)',fontsize=8.6,transform=ax.transAxes,va='center',bbox=dict(facecolor='#e8eef1',edgecolor='none',pad=6))
  ax.text(.015,.14,'Thermal gas/oil: 6,830 → 6,210 MW; Tarbert closure −620 MW\nKeadby 2 and Triton are before the opening cut.',fontsize=8.6,transform=ax.transAxes,va='center',bbox=dict(facecolor='#e5eeea',edgecolor='none',pad=6))
fig.subplots_adjust(left=.065,right=.99,top=.94,bottom=.03,hspace=.37)
fig.savefig(O/'figure2_matched_strategy_sequences.png',dpi=250);fig.savefig(O/'figure2_matched_strategy_sequences.svg',metadata={'Date':None});plt.close(fig)
# Figure 1: source-defined observation windows and SSE nesting, not arbitrary 2019–2024 finance panel.
timeline=rd('main_exhibits/figure1_timeline_source_rows.csv')
# Add previously omitted in-scope prior gas commissioning; its exact date is decisive.
r=sev[sev.asset=='Keadby2 CCGT'].iloc[0]
timeline=pd.concat([timeline,pd.DataFrame([dict(issuer='SSE',lane='Fossil events',date=r.event_date,date_precision='day',label='Keadby 2: commissioning before matched opening',source_url=r.source_url,source_locator=r.source_locator,plot_start=r.event_date,plot_end=r.event_date,plot_glyph='point')])],ignore_index=True)
mask=(timeline.issuer=='SSE') & timeline.label.str.contains('Tarbert.*physical retirement',regex=True)
timeline.loc[mask,'date']='2023; month unresolved (September/December)'
timeline.loc[mask,'date_precision']='conflicting month disclosures'
timeline.loc[mask,'plot_start']='2023-09-01'; timeline.loc[mask,'plot_end']='2023-12-31'
timeline.loc[mask,'source_url']=timeline.loc[mask,'source_url']+'; https://www.sse.com/media/ej5l4w14/sse-plc_prospectus-2024_final-version.pdf'
timeline.loc[mask,'source_locator']=timeline.loc[mask,'source_locator']+'; prospectus printed pp.105–106'
save(timeline,'timeline_with_analysis_window_source_rows.csv')
fig,axes=plt.subplots(2,1,figsize=(6.27,6.5),gridspec_kw={'height_ratios':[1.7,3.3]})
ax=axes[0]
for yi,issuer in enumerate(['Enel','Iberdrola']):
 for year in range(2019,2025):
  ax.scatter(year,1-yi,s=36,color='#355770',zorder=3)
  if year<2024:ax.plot([year,year+1],[1-yi,1-yi],color='#75949f',lw=2)
ax.set_yticks([1,0],['Enel reports','Iberdrola reports']);ax.set_xticks(range(2019,2025));ax.set_ylim(-.65,1.65);ax.set_xlim(2018.8,2024.2)
ax.set_title('Five adjacent report-vintage\ncomparisons per case',loc='left',fontweight='bold',fontsize=10)
ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0);ax.grid(axis='x',alpha=.12)
ax.text(0,-.32,'Fossil changes align to destination calendar years 2020–2024.\nReport labels do not establish exact allocation or publication dates.',transform=ax.transAxes,fontsize=8)
ax=axes[1]
select=[('Triton: acquisition','2022-09-01','2022-09-01','#b3634a'),('Keadby 2: commissioning','2023-03-15','2023-03-15','#b3634a'),('GB5 opening observation','2023-03-31','2023-03-31','#355770'),('Seagreen: full operation','2023-10-17','2023-10-17','#3b8a74'),('Tarbert: closure month unresolved','2023-09-01','2023-12-31','#b3634a'),('GB5 closing observation','2024-03-31','2024-03-31','#355770'),('Viking: full operation','2024-08-29','2024-08-29','#3b8a74')]
lo=datetime.date(2023,3,31);hi=datetime.date(2024,3,31)
ax.axvspan(lo,hi,facecolor='#e6efee',zorder=0);ax.axvline(lo,color='#355770',ls=':',lw=1);ax.axvline(hi,color='#355770',ls=':',lw=1)
for i,(label,a,b,c) in enumerate(select):
 y=len(select)-1-i;a=datetime.date.fromisoformat(a);b=datetime.date.fromisoformat(b);ax.axhline(y,color='#eeeeee',lw=.6,zorder=0)
 if a==b:ax.scatter(a,y,color=c,s=26,zorder=4)
 else:ax.plot([a,b],[y,y],color=c,lw=4,solid_capstyle='butt')
ax.set_yticks(list(reversed(range(len(select)))),[r[0] for r in select],fontsize=8)
ax.set_ylim(-.6,len(select)-.4);ax.set_xlim(datetime.date(2022,6,1),datetime.date(2024,12,1));ax.xaxis.set_major_locator(md.MonthLocator(bymonth=[1,7]));ax.xaxis.set_major_formatter(md.DateFormatter('%b\n%Y'));ax.tick_params(axis='y',length=0,pad=6);ax.spines['left'].set_visible(False)
ax.set_title('SSE: matched fiscal interval\nwith antecedent and later events',loc='left',fontweight='bold',fontsize=10,pad=10)
fig.subplots_adjust(left=.38,right=.98,top=.94,bottom=.07,hspace=.8)
fig.savefig(O/'figure1_selected_timelines.png',dpi=250);fig.savefig(O/'figure1_selected_timelines.svg',metadata={'Date':None});plt.close(fig)
contract['figures'][0]['caption']='Observation windows for the joint analysis. Enel and Iberdrola contribute all five adjacent 2019–2024 report-vintage comparisons; fossil changes use each destination calendar year. Points in the upper panel index report vintages, not exact allocation or publication dates. SSE has one matched interval, 31 March 2023–31 March 2024 (shading). Triton acquisition and Keadby 2 commissioning precede its opening; Viking full operation follows its close. The Tarbert range preserves conflicting September/December 2023 disclosures; both fall inside the same fiscal interval. Event sequencing and matched windows do not establish financing causation.'
contract['figures'][1]={'number':2,'file':'figure2_matched_strategy_sequences.png','caption':'Financing and fossil-asset sequences. All eleven observed adjacent intervals are shown. Finance cells summarize selected-instrument allocation stocks and report identities, not annual flows. Fossil MW cells show net changes in each source-defined portfolio, with identified event mixtures; scales and boundaries are not pooled. Enel’s coal branch lacks a harmonized gross-event bridge. Iberdrola’s 2020 net expansion includes coal closure and larger additions, and its 2024 decline includes ownership transfer and an unresolved reduction. SSE uses only the shaded fiscal window in Figure 1. Unchanged net stocks and missing project weights remain explicit; no company ranking or financing effect is estimated.'}
(O/'canonical_manuscript_exhibits.json').write_text(json.dumps(contract,indent=2,ensure_ascii=False)+'\n')
(O/'FIGURE_CAPTIONS.txt').write_text('\n\n'.join(f'Figure {r["number"]}. {r["caption"]}' for r in contract['figures'])+'\n')
# Retire superseded numbered main exhibits to clearly named supplements.
for name in ['table2_claim_evidence_synthesis.csv','table3_finance_delivery_comparison.csv']:
 (O/name).unlink(missing_ok=True)
for old,new in [('figure2_allocation_replacement.png','enel_allocation_replacement.png'),('figure2_allocation_replacement.svg','enel_allocation_replacement.svg'),('figure2_allocation_replacement_source_rows.csv','enel_allocation_replacement_source_rows.csv')]:
 if (O/old).exists():
  (J/new).write_bytes((O/old).read_bytes()); (O/old).unlink()
(O/'README.txt').write_text('CANONICAL MAIN EXHIBITS: STRATEGY REVISION\n\nThe exact four-table/three-figure contract is canonical_manuscript_exhibits.json. Table 1: selection; Table 2: matched finance/fossil sequences; Table 3: decision chains; Table 4: longer-period boundary-specific bridges. Figure 1: source-defined windows; Figure 2: complete adjacent-interval sequences; Figure 3: boundary bridges. Superseded claim/maturity tables and allocation-replacement figure are clearly named supplements in joint_strategy. Read joint_strategy/METHOD_AND_COVERAGE.txt for temporal and interpretation rules. Run python run_analysis.py at package root before packaging.\n')
# Bounded coverage protocol and machine-readable new-result receipt.
protocol='''MATCHED WITHIN-CASE FINANCING–FOSSIL STRATEGY ANALYSIS

Unit and scope: one adjacent pair of observed selected-instrument finance records joined to the destination issuer accounting period. There are five Enel report-vintage pairs, five Iberdrola report-vintage pairs and one SSE exact fiscal pair. All observed adjacent pairs are retained, including unchanged and unresolved periods. This is a retrospective, purposive archive, not a representative panel.

Temporal rule: Enel/Iberdrola report-vintage labels align to calendar-year accounting changes; exact within-year allocation timing is not established. They are not asserted to be exact-date synchronized observations. SSE uses (31 March 2023, 31 March 2024]; earlier gas additions and later Viking completion cannot be inserted into the matched window. SSE 2019–2024 capacity context is a longer, nested but distinct series.

Financial rule: recurring allocations are stocks, never summed as annual flows. Identity entries/exits use canonical report-line identifiers. Iberdrola project money is missing, not equal-weighted or zero-filled. Enel aggregate hydro identities and rounded allocations prevent exact underlying project continuity; operating status is not harmonized full COD. SSE weights use unchanged GBP543.9m denominator, and classify explicit zero output separately from missing output or construction with generation.

Fossil rule: every identified input-ledger event is retained and assigned to its source accounting year, preserving the actual implementation-date field. Enel's near-year-boundary effective closure dates are not forced into recognition years. Enel gross unit ratings are not converted into net-efficient stock contributions without evidence, so closure-component and residual cells remain blank. Iberdrola/SSE signed identified contributions retain unresolved residuals and reporting/ownership categories. A zero residual or no identified event is not an exhaustive gross-event census. Coal-only Enel, Iberdrola technology portfolio and SSE Thermal portfolio are never pooled, subtracted against green-project MW or ranked.

Analytical advance: the algorithm traces whether the same observed financial record accompanies changing annual mixes of physical closure, installation/commissioning, acquisition/rights, disposal, reporting changes and unresolved movements. It retains periods without financial substitution or net fossil movement. In the source-defined Iberdrola 2020 interval, actual coal closure coexists with net reported fossil expansion because identified additions exceed removals; in 2024 the dominant classified removal is a sale. SSE physical maturity/closure coexistence is established only within the correct fiscal window. Enel coal contraction appears in both substitution and non-substitution report intervals. These are bounded sequences, not causal mechanisms or enduring issuer types.

Link rule: co-occurrence, issuer-stated strategic rationale and an explicit financial/transaction link are separate. The decision-chain companion records source-supported links. No traced selected-bond-to-fossil-event funding chain is established by this join.

Rebuild: python run_analysis.py. New analysis: build_joint_strategy.py; full source data are extracted CSVs, with original documents linked in source registers and not redistributed. Manifest files are finalized after all outputs, workbook and notes.
'''
(J/'METHOD_AND_COVERAGE.txt').write_text(protocol)
results=dict(scope={'matched_intervals':len(q),'by_issuer':q.groupby('issuer').size().to_dict(),'source_package_sha256':'545c7ba597d3466126679c1f388a42780662a161a47714044ebe7d09430e9b33'},iberdrola_2020={'closure_mw':-874,'installation_pre_COD_mw':779,'acquisition_or_rights_mw':243,'net_change_mw':148},iberdrola_2024={'disposal_mw':-8494,'uprating_mw':17,'unresolved_mw':-29,'net_change_mw':-8506},iberdrola_unresolved_2021_mw=-6,unchanged_stock_intervals=['ENEL_2023_2024','IBERDROLA_2022_2023'],enel_annual_coal_changes_mw=list(q[q.issuer=='Enel'].net_change_mw),enel_substitution_report_years=[2020,2023],enel_no_observed_substitution_but_coal_decline_years=[2021,2022],sse=dict(interval='(2023-03-31,2024-03-31]',full_operation_share_open_pct=f(fin[(fin.issuer=='SSE')&(fin.observation_year==2023)].full_operation_share_pct.iloc[0]),full_operation_share_close_pct=f(fin[(fin.issuer=='SSE')&(fin.observation_year==2024)].full_operation_share_pct.iloc[0]),closure_mw=-620,preopening_excluded_gas_commissioning_mw=893,preopening_excluded_acquisition_mw=670),causal_effect_estimated=False,pooled_mw_or_issuer_ranking=False)
(J/'computed_joint_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
save(pd.DataFrame(CHECKS),'validation_checks.csv')
(J/'validation_summary.json').write_text(json.dumps({'checks':len(CHECKS),'passed':sum(r['pass'] for r in CHECKS),'all_pass':all(r['pass'] for r in CHECKS)},indent=2)+'\n')
# Inputs are hashed here after extraction is complete; outputs are hashed by final packager.
manifest=[]
for s in sorted(set(INPUTS)):
 p=P/s;manifest.append({'path':s,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'role':'source-derived input; original source URLs retained in rows'})
save(pd.DataFrame(manifest),'input_manifest.csv')
print(json.dumps(results,indent=2))
