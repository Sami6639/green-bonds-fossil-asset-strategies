"""Offline semantic regression tests for the XS1890845875 date-source correction."""
from pathlib import Path
import csv,json,hashlib
P=Path(__file__).parent
H=P/'iberdrola/history_2019_2024'
def read(p):
 with (P/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
checks=[]
def check(name,condition):
 checks.append({'check':name,'pass':bool(condition)})
 if not condition:raise AssertionError(name)
pr=read('iberdrola/history_2019_2024/instrument_date_provenance.csv');check('one_instrument_date_record',len(pr)==1);d=pr[0]
check('verified_contractual_issue_date',d['issue_date']=='2019-02-12')
check('reported_inventory_date_preserved',d['allocation_report_inventory_date']=='2019-02-05' and d['allocation_report_inventory_date_as_reported']=='05-Feb-19')
check('date_types_separate',d['issue_date_meaning']=='contractual_issue_date_defined_in_offering_circular' and 'retained as reported' in d['allocation_report_inventory_date_meaning'])
check('no_pricing_inference','no pricing-date inference' in d['date_resolution'])
check('matching_instrument',d['instrument_isin']=='XS1890845875')
check('primary_source_urls_distinct',d['issue_date_source_url']!=d['allocation_report_inventory_date_source_url'] and all('www.iberdrola.com' in d[k] for k in ['issue_date_source_url','allocation_report_inventory_date_source_url']))
check('legal_and_inventory_locators_separate','47' in d['issue_date_source_locator'] and '64' in d['issue_date_source_locator'] and 'PDF p. 3' in d['allocation_report_inventory_date_source_locator'])
bond=read('iberdrola/history_2019_2024/matched_green_hybrid_2019_2024.csv');check('24_original_finance_observations',len(bond)==24)
for r in bond:
 check('date_fields_consistent_'+r['report_year']+'_'+r['field'],all(r[k]==d[k] for k in d if k not in ['verified_utc_date']))
 check('no_pricing_date_field_'+r['report_year']+'_'+r['field'],not any(k=='pricing_date' and r[k] for k in r))
for y in range(2019,2025):
 rr={r['field']:float(r['value']) for r in bond if r['report_year']==str(y)}
 check(f'{y}_allocation_unchanged',rr['investment_allocated_stock']==800)
 check(f'{y}_attributable_capacity_unchanged',rr['capacity_attributable']==231)
 check(f'{y}_generation_unchanged',rr['actual_generation_attributable']==dict(zip(range(2019,2025),[232,761,874,821,948,771]))[y])
 check(f'{y}_reported_avoided_co2_unchanged',rr['avoided_co2_reported']==dict(zip(range(2019,2025),[93265,209234,202192,191783,221965,184477]))[y])
for f in ['main_exhibits/figure1_timeline_source_rows.csv','joint_strategy/timeline_with_analysis_window_source_rows.csv']:
 rr=[r for r in read(f) if r['issuer']=='Iberdrola' and r['lane']=='Finance'];check(f+'_single_finance_event',len(rr)==1);r=rr[0]
 check(f+'_legal_event_date',r['date']==r['plot_start']==r['plot_end']=='2019-02-12')
 check(f+'_legal_source',r['source_url']==d['issue_date_source_url'])
 check(f+'_inventory_retained',r['allocation_report_inventory_date']=='2019-02-05' and 'no pricing-date inference' in r['date_resolution'])
for f in ['review_revision_inputs/three_core_evidence_matrix.csv','main_exhibits/three_core_evidence_matrix.csv']:
 r=next(r for r in read(f) if r['claim_id']=='IBE06')
 check(f+'_both_dates_distinguished','contractual Issue Date is 12 February 2019' in r['available_evidence'] and 'inventory separately reports 5 February 2019' in r['available_evidence'])
 check(f+'_primary_sources',all(d[k] in r['source_urls'] for k in ['issue_date_source_url','allocation_report_inventory_date_source_url']))
 check(f+'_prior_decision_unchanged','10 November 2017' in r['available_evidence'] and r['status']=='supported')
m=read('iberdrola/history_2019_2024/source_manifest.csv');v=json.loads((H/'issue_date_source_verification.json').read_text())
for source in v['sources']:
 check(source['source_id']+'_source_hash',next(r['sha256'] for r in m if r['source_id']==source['source_id'])==source['sha256'])
reg=read('methods_revision_inputs/empirical_source_register.csv');r=next(r for r in reg if r['source_key']=='IB-OC19')
check('circular_document_date_distinct',r['verified_publication_date']=='2019-02-06' and r['verified_publication_date']!=d['issue_date'])
check('evidence_registry_contractual_date','12 February 2019' in r['source_note'] and r['source_url']==d['issue_date_source_url'])
check('eleven_intervals_unchanged',len(read('joint_strategy/matched_interval_panel.csv'))==11)
# The final vintage-only timeline and all unrelated figure designs must be preserved.
figure_hashes={'main_exhibits/figure1_selected_timelines.png': '994eaaf99d1a8183902905782226c73eb0cdef3e38311a79e6337a959e94c291', 'main_exhibits/figure1_selected_timelines.svg': 'f3c91c65e467ab6a9b5294fb4575f88d8384d408b3a2bd1d55ba2c0d5946ff6a', 'main_exhibits/figure2_matched_strategy_sequences.png': '815196fad488462749ed0b29ee245d93e4244dbfd3805ee764685b3987cc6d11', 'main_exhibits/figure2_matched_strategy_sequences.svg': '2e67e7942977cae6787d095bbff2f8bf0bfed9f77ef3e73b1b9f3cbdf8f304e1', 'main_exhibits/figure3_capacity_bridges.png': '34e8d4e2e6daf0f08dfe002f082fa755295bd962cc937295108ed2c3621c46d8', 'main_exhibits/figure3_capacity_bridges.svg': '67fb95940f549da789b374fd2b2153a1630b00d7adf8c04ba9c3601d6747dcac'}
for f,expected in figure_hashes.items():
 check('original_main_figure_bytes:'+f,hashlib.sha256((P/f).read_bytes()).hexdigest()==expected)
out={'scope':'Semantic date-provenance regression checks plus unchanged selected-instrument quantities; not an independent human coding exercise.','checks':len(checks),'all_pass':all(r['pass'] for r in checks),'details':checks}
(H/'issue_date_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='details'}))
