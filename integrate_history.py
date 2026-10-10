"""Preserve issuer-specific historical capacity boundaries; no pooled regression panel."""
from pathlib import Path
import csv,json,hashlib
P=Path(__file__).parent;O=P/'integrated_history';O.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(n,rr):
 with (O/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rr[0]);w.writeheader();w.writerows(rr)
capacity=[]
ib=P/'iberdrola/history_2019_2024'
for r in read(ib/'capacity_by_fossil_technology_2019_2024.csv'):
 if r['primary_scope'].lower()!='true':continue
 capacity.append(dict(issuer='Iberdrola',year=r['year'],period_end=r['year']+'-12-31',category=r['reported_technology'],capacity_mw=r['capacity_mw'],scope=r['ownership_scope'],primary_status='issuer_specific_technology_not_pure_fuel',source_url=r['source_url'],source_locator=f"PDFp{r['pdf_page_1_based']}; printedp{r['printed_page']}; {r['source_row']}; {r['source_field']}",notes=r['notes']))
for r in read(P/'sse/capacity_2019_2024_source_cells.csv'):
 capacity.append(dict(issuer='SSE',year=r['fiscal_year_end'],period_end=r['as_of'],category=r['metric'],capacity_mw=r['value'],scope=r['boundary'],primary_status=r['status'],source_url=r['source_url'],source_locator=r['source_locator']+'; '+r['source_column'],notes=r['scope_flags']))
for r in read(P/'clp/history_2019_2024/issuer_year_facts_2019_2024.csv'):
 if r['metric']!='capacity':continue
 capacity.append(dict(issuer='CLP',year=r['fiscal_year'],period_end=r['period_end'],category=r['asset_type'],capacity_mw=r['value'],scope=r['ownership_basis'],primary_status=r['value_status'],source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']))
for r in read(P/'enel/issuer_fuel_year_2019_2024.csv'):
 if r['unit']!='MW':continue
 capacity.append(dict(issuer='Enel',year=r['year'],period_end=r['year']+'-12-31',category=r['fuel']+' | '+r['metric'],capacity_mw=r['value'],scope=r['scope'],primary_status=r['value_type'],source_url=r['source_url'],source_locator='PDFp'+r['source_pdf_page']+'; '+r['source_cell'],notes=r['boundary_note']))
write('historical_capacity_cells.csv',capacity)
for name in ['coal_capacity_regional_bridge_2019_2024.csv','coal_decision_event_dossier.csv','coal_bridge_validation.csv']:
 write('enel_'+name,read(P/'enel'/name))
# Event rows preserve the exact numerical reporting boundary rather than pretending all are net equity.
events=[]
for r in read(ib/'fossil_capacity_event_ledger.csv'):
 events.append(dict(issuer='Iberdrola',event_id=r['event_id'],year=r['year'],event_date=r['event_date_reported'],asset=r['asset_or_project'],event_type=r['event_class'],capacity_change_mw=r['capacity_delta_mw'],scope='reported group capacity: consolidated plus proportional investees',source_url=r['source_url'],source_locator=f"printedp{r['printed_page']}; PDFp{r['pdf_page_1_based']}; {r['source_row']}",notes=r['notes']+'; include_in_capacity_bridge='+r['include_in_capacity_bridge']))
for i,r in enumerate(read(P/'sse/capacity_2019_2024_event_contributions.csv')):
 events.append(dict(issuer='SSE',event_id='SSE_HIST_'+str(i+1),year=r['bridge_fiscal_year'],event_date=r['event_date'],asset=r['asset'],event_type=r['event_type'],capacity_change_mw=r['signed_reported_portfolio_mw'],scope='reported Thermal owned plus JV share; fuel categories and scope changes retained',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']))
for r in read(P/'clp/history_2019_2024/additional_asset_events.csv'):
 events.append(dict(issuer='CLP',event_id=r['event_id'],year=r['date'][:4],event_date=r['date'],asset=r['asset'],event_type=r['event_type'],capacity_change_mw=r['equity_change_mw'],scope='equity-share coal',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']+'; '+r['capacity_source']+'; stock-series recognition: '+r['stock_series_recognition']))
for r in read(P/'clp/asset_event_ledger.csv'):
 events.append(dict(issuer='CLP',event_id=r['event_id'],year=r['event_date'][:4],event_date=r['event_date'],asset=r['asset_id'],event_type=r['event_type'],capacity_change_mw=r['capacity_change_equity_mw'],scope='equity-share coal',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']+'; '+r['capacity_source_url']+'; '+r['capacity_source_locator']))
write('historical_capacity_events.csv',events)
# Stable finance cohorts are illustrative matched instruments, not complete issuer financing universes.
finance=[]
for r in read(ib/'matched_green_hybrid_2019_2024.csv'):
 finance.append(dict(issuer='Iberdrola',year=r['report_year'],instrument_id=r['instrument_isin'],project_or_basket='East Anglia ONE and Wikinger',metric=r['field'],value=r['value'],unit=r['unit'],measurement_basis={'investment_allocated_stock':'Cumulative monetary allocation stock', 'capacity_attributable':'Financing-attributed capacity snapshot', 'actual_generation_attributable':'Annual financing-attributed actual generation', 'avoided_co2_reported':'Annual modeled avoided-emissions estimate'}.get(r['field'],'Reported indicator; consult unit and source definition'),source_url=r['source_url'],source_locator=f"printedp{r['printed_page']}; PDFp{r['pdf_page_1_based']}; {r['source_field']}",notes=r['notes']))
for r in read(P/'clp/history_2019_2024/went_finance_delivery_2019_2024.csv'):
 for field,unit in [('allocation_cumulative_hkdm','HKD million'),('actual_output_gwh','GWh'),('expected_output_gwh','GWh'),('full_project_capacity_mw','MW')]:
  finance.append(dict(issuer='CLP',year=r['year'],instrument_id=r['instrument_id'],project_or_basket='WENT landfill gas',metric=field,value=r[field],unit=unit,measurement_basis='Full-project output/capacity; cumulative allocation; expected output separate',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['notes']+'; '+r['period_notes']+'; status='+r['output_status']))
for r in read(P/'sse/fixed_cohort_bond_project_links.csv'):
 finance.append(dict(issuer='SSE',year=r['report_year'],instrument_id=r['isin'],project_or_basket=r['project_id'],metric='allocation_stock_gbp_m',value=r['allocation_stock_gbp_m'],unit='GBP million',measurement_basis='Cumulative bond-project allocation stock; financial refinancing',source_url=r['source_url'],source_locator=r['source_locator'],notes=r['warning']))
write('selected_matched_finance_cohort_cells.csv',finance)
for name in ['fixed_cohort_project_master.csv','fixed_cohort_annual_disclosure_snapshots.csv','fixed_cohort_actual_milestones.csv']:
 write('sse_'+name,read(P/'sse'/name))
checks=[]
for name,rr,keys in [('capacity',capacity,['issuer','year','category','scope']),('events',events,['issuer','event_id']),('finance',finance,['issuer','year','instrument_id','project_or_basket','metric'])]:
 kk=[tuple(r[k] for k in keys) for r in rr]; dup=len(kk)-len(set(kk))
 checks.append(dict(check=name+'_unique_keys',value=dup,status='PASS' if dup==0 else 'FAIL'))
 checks.append(dict(check=name+'_has_provenance',value=sum(not r['source_url'] or not r['source_locator'] for r in rr),status='PASS' if all(r['source_url'] and r['source_locator'] for r in rr) else 'FAIL'))
write('validation_checks.csv',checks)
(O/'README.txt').write_text('HISTORICAL CAPACITY AND FINANCE EVIDENCE\n\nThis extension preserves four distinct issuer reporting boundaries. It is not a balanced, harmonized whole-company fossil panel. Use historical_capacity_cells.csv and historical_capacity_events.csv with the issuer-level bridges and notes.\n\nIberdrola uses its reported group capacity: consolidated at EBITDA level plus proportional managed investees. Its gas bucket includes OCGT, and cogeneration is a broad technology proxy whose fuel mix is not fully established. The original label is retained. Topolobampo was physically installed before commercial operation; Australian assets include unresolved ownership or lease status. This is a reported accounting/technology stock, not a core operating fossil stock.\n\nSSE uses its reported Thermal portfolio, with owned and joint-venture capacity. Multifuel, transfers, scope changes and acquisition effects are separate. Fiscal years end 31 March.\n\nCLP uses equity-share capacity. The coal event analysis is separate from its gas and other capacity. A late-2020 Mount Piper uprating and 2021 stock recognition mismatch is retained; annual bridges are not forced. The 2024 closure total includes 245 equity MW already in reserve from 2022; it is reserve-inclusive. Identified zero event contributions do not verify the absence of gross offsetting events.\n\nThe selected matched financial cohorts are illustrative longitudinal instruments, not full issuer finance universes. Iberdrola output is financing-attributed to a two-asset basket; CLP WENT output is full-project. They must not be pooled or relabelled as comparable additional generation. SSE links and dated project snapshots are retained separately; disclosure year does not imply a common observation date.\n\nExpected versus actual output, allocation stocks versus annualflows, and sale/handback versus physical retirement remain distinct. No bond-caused transition estimate or whole-company comparable fossil GWh is constructed. Enel regional coal bridges and event dossiers remain separate: gross plant ratings, observed regional net changes and known disposal contributions are not interchangeable. Reftinskaya exited during 2019 and is outside the end-2019 to end-2024 bridge.\n')
manifest=[]
for folder in ['clp','iberdrola','sse','orsted','enel']:
 for f in sorted((P/folder).rglob('*.csv')):
  if 'sources' in f.parts:continue
  manifest.append(dict(path=str(f.relative_to(P)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),rows=len(read(f))))
write('extracted_file_manifest.csv',manifest)
print({'capacity_cells':len(capacity),'event_rows':len(events),'finance_cells':len(finance),'checks':checks})
