"""Build a non-pooled, provenance-preserving pilot catalog. No regressions or causal estimates."""
from pathlib import Path
import csv,json,hashlib,collections
P=Path(__file__).parent
O=P/'integrated';O.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(name,rows,fields=None):
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def val(r,*keys):
 return next((r.get(k,'') for k in keys if r.get(k,'')!=''),'')
normalized=[]
for r in read(P/'clp/issuer_year_facts.csv'):
 normalized.append(dict(issuer='CLP',year=r['fiscal_year'],period_start=r['period_start'],period_end=r['period_end'],metric=r['metric'],category=r['asset_type'],value=r['value'],unit=r['unit'],scope=r['ownership_basis'],measurement_basis=r['measurement_basis'],aggregation_role='total' if r['asset_type']=='total' else 'component',status=r['value_status'],source_url=r['source_url'],source_locator=r['source_locator'],origin_table='clp/issuer_year_facts.csv',notes=r['notes']))
for r in read(P/'sse/issuer_year_cells.csv'):
 normalized.append(dict(issuer='SSE',year=r['fiscal_year_end'],period_start=r['period_start'],period_end=r['period_end'],metric=r['metric'],category='see_metric',value=r['value'],unit=r['unit'],scope=r['scope_flags'],measurement_basis='reported_company_KPI',aggregation_role='see_metric_no_cross_row_sum',status=r['value_status'],source_url=r['source_url'],source_locator='; '.join([r['source_locator'],r['source_row'],r['source_column']]),origin_table='sse/issuer_year_cells.csv',notes='Do not pool with equity-only issuer values. See issuer README and boundary supplements.'))
for r in read(P/'iberdrola/issuer_year_technology_facts.csv'):
 normalized.append(dict(issuer='Iberdrola',year=r['observation_year'],period_start=r['observation_year']+'-01-01',period_end=r['observation_year']+'-12-31',metric=r['metric'],category=r['reported_technology'],value=r['value'],unit=r['unit'],scope=r['ownership_scope'],measurement_basis=r['timing'],aggregation_role=r['aggregation_role'],status='reported',source_url=r['source_url'],source_locator='printed p'+r['printed_page']+'; PDF p'+r['pdf_page_1_based']+'; '+r['source_table']+'; row '+r['source_row']+'; column '+r['source_field'],origin_table='iberdrola/issuer_year_technology_facts.csv',notes=r['notes']))

orf=P/'orsted/issuer_year_observations.csv'
if orf.exists():
 sm={r['source_id']:r['official_url'] for r in read(P/'orsted/source_manifest.csv')}
 for r in read(orf):
  normalized.append(dict(issuer='Ørsted',year=r['year'],period_start=r['period_start'],period_end=r['period_end'],metric=r['metric'],category='see_metric',value=r['value'],unit=r['unit'],scope=r['scope'],measurement_basis='issuer_reported_see_scope',aggregation_role='see_metric_no_cross_row_sum',status=r['observation_status'],source_url=sm.get(r['source_id'],''),source_locator='printed p'+r['printed_page']+'; PDF p'+r['pdf_page_1based']+'; '+r['source_row']+'; column '+r['source_column'],origin_table='orsted/issuer_year_observations.csv',notes=r['notes']+'; preferred_observation='+r['is_preferred_observation']))

sup=P/'sse/boundary_additional_source_cells.csv'
if sup.exists():
 for r in read(sup):
  matched=[z for z in normalized if z['issuer']=='SSE' and z['year']==r['fiscal_year_end'] and z['metric']==r['metric']]
  if matched:
   z=matched[0];z.update(value=r['value'],status=r['value_status'],source_url=r['source_url'],source_locator=r['source_locator']+'; '+r['source_column'],notes=z['notes']+' Supplement verifies formerly missing value; original source extraction retained unchanged.')
  else:
   y=r['fiscal_year_end']
   normalized.append(dict(issuer='SSE',year=y,period_start=str(int(y)-1)+'-04-01',period_end=y+'-03-31',metric=r['metric'],category='see_metric',value=r['value'],unit=r['unit'],scope='supplemental mixed-energy or alternative-definition scope; not whole-company fossil output',measurement_basis='reported_company_KPI',aggregation_role='alternative_or_mixed_category_do_not_sum',status=r['value_status'],source_url=r['source_url'],source_locator=r['source_locator']+'; '+r['source_column'],origin_table='sse/boundary_additional_source_cells.csv',notes='Supplementary scope clarification only.'))
write('issuer_year_observations.csv',normalized)
# Freeze an inventory; preserve source tables rather than manufacturing lossy common joins.
catalog=[]; sources=collections.defaultdict(set); dictionary=[]
meaning={
'value':'Source observation or explicit derived quantity; read status, unit, scope and source before use.',
'unit':'Measurement unit as reported; MW is capacity, GWh is energy; currency units and million multipliers remain explicit.',
'source_url':'Official public source URL; access and download limitations are recorded separately.',
'source_locator':'Exact table/page/row/column or HTML section supporting the row.',
'ownership_scope':'Accounting perimeter as reported; distinct scopes are alternatives and must not be summed.',
'scope':'Issuer-specific reporting boundary; not harmonized across issuers.',
'project_allocation_money':'Project-specific money only; blank where reported only for a bond or aggregate. Never spread pro rata without separate assumption.',
'project_actual_generation_gwh':'Observed project generation only; blank when absent or only instrument-attributed output exists.',
'capacity_attributable_mw':'Financing-attributed capacity; may represent future projects and is not automatically operating MW.',
'allocated_total_million':'Cumulative allocated amount in allocation_currency unless allocation_basis explicitly states flow.',
'allocated_finance_million':'Issuer-labelled finance allocation; this does not on its own establish new physical construction.',
'allocated_refinance_million':'Issuer-labelled refinancing allocation; construction projects may be refinanced.',
'actual_generation_gwh':'Reported actual energy output; do not equate to bond-attributed or equity-adjusted output without basis.',
'commissioning_status':'actual vs expected_at_report vs not_applicable; never use later actual status as earlier information.',
'event_type':'Physical retirement, ownership exit, acquisition, commissioning, reserve or reporting-boundary change are separate.',
'capacity_change_equity_mw':'Signed change in issuer equity capacity from the identified event, not system capacity change.',
'unexplained_residual_mw':'Observed closing minus opening less identified signed event changes; blank is unresolved, not zero.',
'physical_retirement_established':'Whether physical retirement is directly evidenced; false never converts disposal into closure.',
'missingness_reason':'Why no numerical value is present. Blank or source dash is not assumed zero.',
'startup_status':'As-reported startup status. Historical year alone need not prove final commercial operation.',
'report_year':'Year of disclosure/reporting snapshot; distinct from project startup or bond issue year.',
'record_id':'Stable row identifier within the named source table.',
'project_id':'Stable coded project identifier; harmonization with external asset IDs remains to be verified.',
'instrument_id':'Reported ISIN or issuer common code; not all identifiers are ISINs.',
'notes':'Material definition, interpretation or quality qualifications; required for safe use.'}
for folder in ['clp','sse','iberdrola','orsted']:
 for f in sorted((P/folder).glob('*.csv')):
  rows=read(f); cols=list(rows[0]) if rows else []
  catalog.append(dict(table=str(f.relative_to(P)),rows=len(rows),columns=len(cols),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),purpose='Issuer-specific source facts/QA; see issuer note',pooled_panel='no'))
  for c in cols:
   dictionary.append(dict(table=str(f.relative_to(P)),field=c,definition=meaning.get(c,'Literal source-specific field; exact label and interpretation in issuer README or source locator. Preserve without cross-issuer recoding.'),missing_rule='Blank remains missing/not applicable; consult status/reason. Never fill with zero.'))
  for r in rows:
   for k,v in r.items():
    if 'url' in k and v.startswith('http'):sources[v].add(str(f.relative_to(P)))
write('table_catalog.csv',catalog)
write('data_dictionary.csv',dictionary)
write('source_manifest.csv',[dict(source_url=u,used_in='; '.join(sorted(fs)),retrieved_date='2026-10-10',source_class='official_company_or_public_regulator',redistribution='Derived facts only; no open report redistribution licence established') for u,fs in sorted(sources.items())])
checks=[]
key=lambda r:(r['issuer'],r['year'],r['metric'],r['category'],r['scope'],r['source_locator'])
keys=[key(r) for r in normalized]
checks.append(dict(check='normalized observation key uniqueness',status='PASS' if len(keys)==len(set(keys)) else 'FAIL',n=len(keys)-len(set(keys)),interpretation='Alternative ownership scopes and component/subtotal rows are not cross-summed.'))
checks.append(dict(check='nonblank numeric observations have source URL and locator',status='PASS' if all(r['source_url'] and r['source_locator'] for r in normalized if r['value']!='') else 'FAIL',n=sum(r['value']!='' and (not r['source_url'] or not r['source_locator']) for r in normalized),interpretation='Provenance completeness does not establish cross-issuer comparability.'))
checks.append(dict(check='explicit missing values retained',status='DESCRIPTIVE',n=sum(r['value']=='' for r in normalized),interpretation='Never zero-filled. Additional absent constructs are recorded in the coverage matrix.'))
write('integration_checks.csv',checks)
summary={'normalized_issuer_cells':len(normalized),'source_tables':len(catalog),'unique_source_urls':len(sources),'regressions_run':False,'pooled_panel_constructed':False,'checks':checks}
(O/'integration_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
# Syntactic completeness is disclosed separately from analytical eligibility.
fieldcov=[]
for c in catalog:
 rr=read(P/c['table'])
 for field in (rr[0].keys() if rr else []):
  n=sum(str(r.get(field,'')).strip()!='' for r in rr)
  fieldcov.append(dict(table=c['table'],field=field,nonblank=n,rows=len(rr),nonblank_pct=round(100*n/len(rr),2),interpretation='Syntactic coverage only; expected values and not-applicable fields require semantic filtering.'))
write('field_completeness.csv',fieldcov)
coverage=[
 dict(issuer='Iberdrola',portfolio_years='2022–2024',primary_capacity_scope='Consolidated-at-EBITDA reported gas-fired bucket (includes OCGT)',dated_event_bridge='2024 reported gas-fired bucket reconciles: sale8494MW + upgrade17MW',whole_company_fossil_generation='not_identified_as_pure_fuel; Reported gas bucket observed, cogeneration fuel unresolved; nuclear excluded',allocation_cohort='All8 ISINs of6 new2024 holding transactions; separate one2022 bond continuity case',project_money='Not disaggregated by project in bounded cohort',physical_output='Instrument-attributed actual output; project-specific actual output missing',ownership_alignment='Group includes Avangrid/Neoenergia; bond cohort excludes their own issued instruments',eligible_use='Comparative reported gas-fired asset reconfiguration; bounded instrument delivery; no whole-group green-finance proxy',expansion='2019–2024 capacity/event evidence in integrated_history; accounting-stock limitations retained'),
 dict(issuer='SSE',portfolio_years='FY2022–FY2024 ending31March',primary_capacity_scope='SSE Thermal transmission-entry MW; owned+JVshare',dated_event_bridge='FY2024 net capacity reconciles to620MWTarbertclosure; gross offsets not exhaustively verified',whole_company_fossil_generation='Unresolved; reported Thermal gas/oil only; Enterprise and PPA/accounting changes separate',allocation_cohort='2024 report Tables2/3/6 direct generation plus HVDC; transmission-only Tables4/5 excluded',project_money='Reported by bond/project; analytical expansion of shared physical rows requires project deduplication',physical_output='Actual qualifying project GWh available, some shared across bonds; futurecommissioning flagged',ownership_alignment='Renewables equity; Thermal output includes100%MarchwoodPPA; no pooledGWh',eligible_use='Comparative reported-Thermal capacity bridge; bounded project delivery',expansion='FY2019–FY2024 capacity/event audit in progress'),
 dict(issuer='CLP',portfolio_years='2022–2024 calendar',primary_capacity_scope='Equity-share coal asset capacity',dated_event_bridge='2024 coal reconciles:735MW reserve-inclusive physical closure +529MW ownership exit',whole_company_fossil_generation='Coal/gas plant-type sent-out observed; coal cofire not apportioned, others not recoded',allocation_cohort='All5/6/7 CAFF bonds outstanding in2022/2023/2024; loans excluded',project_money='Complete bond-project mapping; cumulative finance/refinance stocks',physical_output='WENT43/46/42GWh full-project actual; not bond/equity-attributed; gas GWh not reported',ownership_alignment='Fullproject bond output versus group equity; no implicit scaling or join',eligible_use='Asian mixed-finance boundary case; landfill gas separate from wind/solar; exclude gas/LNG/smartmeters from core',expansion='2019–2024 capacity/event evidence in integrated_history; reserve-inclusive coal boundary'),
 dict(issuer='Ørsted',portfolio_years='2022–2024 calendar',primary_capacity_scope='Thermal capacity observed; fuel-capability MW overlap and fossil unique capacity notidentified',dated_event_bridge='2024 Esbjerg373MWclosure; Kyndby260MW outofoperation/standby separatelycoded; remainingchanges unresolved',whole_company_fossil_generation='Not identified: thermal includes biomass and shares combine heat+power',allocation_cohort='All22 projects and23 bonds in2024report; annual2024 links and cumulative2017–2023matrix',project_money='Detailed annual2024 links observed;90mDKKsummary/detail conflict unresolved',physical_output='Fullproject actual GWh; ownership-adjusted allocations, attributedGWh missing',ownership_alignment='Fullproject physical figures must not be summed as issuer equity output',eligible_use='Finance/project disclosure plus asset-classification case; exclude naive coal-capable decline as total retirement',expansion='Needs unit-level fuel/standby/ownership reconciliation before capacity-series comparison')]
write('analytical_coverage.csv',coverage)
screen=[dict(issuer=r['issuer'],screen_status='included_in_pilot_with_scope_limits',reason=r['eligible_use']) for r in coverage]+[
 dict(issuer='ReNew',screen_status='not_entered_primary_incumbent_sample',reason='Renewable developer; verified project finance-to-production disclosures do not establish a fossil incumbent counterfactual.'),
 dict(issuer='ACEN',screen_status='not_entered_primary_sample_at_this_stage',reason='Mixed instrument disclosure and portfolio transformation need separate eligibility and historical ownership audit; not automatically a control.')]
write('issuer_screen_legacy_six_candidate_pilot.csv',screen)
# Current nine-candidate screen is a frozen source-audited input, not this superseded pilot.
if (P/'review_revision_inputs/final_nine_candidate_screen.csv').exists():
 write('issuer_screen.csv',read(P/'review_revision_inputs/final_nine_candidate_screen.csv'))
# Allocation-value coverage is within each explicit currency/cohort, not pooled across money units.
clprows=read(P/'clp/bond_allocations_2022_2024.csv')
av=[]
for y in ['2022','2023','2024']:
 rr=[r for r in clprows if r['report_year']==y];den=sum(float(r['allocated_total_million']) for r in rr)
 av.append(dict(issuer='CLP',year=y,cohort='CAFF outstanding bonds',currency='HKD',unit='million',allocated_total=den,project_mapped_allocation=den,project_allocation_coverage_pct=100,renewable_generation_eligible_allocation=170,notes='Only170m WENT landfillgas; remainder gas/LNG or smartmeters. Fullprojectoutput not automatically financing-attributed.'))
if (P/'orsted/allocation_2024.csv').exists():
 rr=read(P/'orsted/allocation_2024.csv');den=sum(float(r['allocation_dkkm']) for r in rr)
 av.append(dict(issuer='Ørsted',year='2024',cohort='Detailedp8 annual2024allocations',currency='DKK',unit='million',allocated_total=den,project_mapped_allocation=den,project_allocation_coverage_pct=100,renewable_generation_eligible_allocation=den,notes='Detailed-table denominator is used. Summary bond rows differ by90mDKK; ownership/output alignment remains unresolved.'))
write('allocation_value_coverage.csv',av)
if not (O/'README.txt').exists(): (O/'README.txt').write_text('UTILITY TRANSITION PILOT\nVersion:10October2026. Four screened incumbent issuer groups;2–3year project coverage varies. This package is a data-quality and comparative accounting pilot, not a globally representative panel or completed full study.\n\nRead analytical_coverage.csv first. Source tables preserve separate units, currencies, fiscal periods, ownership boundaries, sub/supertotals, stocks/flows, actual/expected delivery, and blank versuszero. issuer_year_observations.csv normalizes column names only; it is not analytically harmonized. Never sum scopes, subtotalrows, repeated project outputs, annual report allocationstocks, or fuel-capable units.\n\nThree capacity bridges support narrower comparisons: IberdrolaCCGT sale versus upgrade, SSEreportedThermal closure, andCLPequitycoal closure versus ownershipexit. A zero net residual does not prove zero unreported offsetting gross movements. No bond-induced closure, avoided-emissions-as-measured-reduction or constant-perimeter output effect is claimed. Ørstedfuel-capability and standby distinctions remainunresolved.\n\nAll source files and manifests are issuer-specific. Source PDF content is not redistributed in the data-only package because open redistribution licences were notverified. TablecatalogSHA256 hashes freeze extractedCSVversions. Derivedcells retain formulas or inputtable references. Python scripts reproduce tables andchecks from audited manual transcriptions. Some sources were only officialwebtext-readable; visualverification limits remainin issuer notes.\n\nfield_completeness.csv is syntactic completeness only, not eligibility. Allocation-value coverage is calculated within each explicitcohort/currency; no global coverage percentage is manufactured. Entire-firm greenfinance and physicalasset coverage are not established.\n\nNEXT: public2019–2024 sampleframe screening and historicalcapacity/event audit, followed by strategy evidence and comparativeanalysis only where residuals/boundariespermit. No inferentialregressions in thispilot.\n')
