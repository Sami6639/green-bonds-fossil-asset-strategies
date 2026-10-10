"""Validate every final ZIP member and all current derived/input manifest hashes."""
from pathlib import Path
import argparse,csv,hashlib,io,json,zipfile,sys,re
P=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--archive',default=str(P/'utility_transition_strategy_evidence.zip'));ap.add_argument('--docx');ap.add_argument('--output');a=ap.parse_args()
errors=[];checks=[]
def check(name,condition,detail=None):
 checks.append({'check':name,'pass':bool(condition),'detail':detail})
 if not condition:errors.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(a.archive) as z:
 names=set(z.namelist())
 def rows(n):return list(csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig'))))
 top=rows('PACKAGE_MANIFEST.csv');topnames={r['path'] for r in top}
 check('root_manifest_complete_membership',topnames==names-{'PACKAGE_MANIFEST.csv'},{'listed':len(top),'members':len(names)})
 for r in top:
  n=r['path'];check('archive_hash:'+n,n in names and sha(z.read(n))==r['sha256'] and len(z.read(n))==int(r['bytes']))
 derived=rows('main_exhibits/derived_manifest.csv')
 check('derived_manifest_complete_membership',{'main_exhibits/'+r['file'] for r in derived}=={n for n in names if n.startswith('main_exhibits/') and n!='main_exhibits/derived_manifest.csv'})
 for r in derived:check('derived_hash:'+r['file'],sha(z.read('main_exhibits/'+r['file']))==r['sha256'])
 inputs=rows('main_exhibits/source_derived_input_manifest.csv')
 for r in inputs:check('input_hash:'+r['path'],r['path'] in names and sha(z.read(r['path']))==r['sha256'])
 # Historical input manifest is rebuilt upstream; all its entries refer to included extracts.
 for r in rows('integrated_history/extracted_file_manifest.csv'):check('history_input_hash:'+r['path'],r['path'] in names and sha(z.read(r['path']))==r['sha256'])
 for r in rows('review_revision_inputs/review_input_provenance_manifest.csv'):
  if r.get('packaging_status')=='included_derived_input':check('review_input_hash:'+r['input_file'],r['input_file'] in names and sha(z.read(r['input_file']))==r['sha256'])
 # Current source-registry audit hashes are current; superseded prose-fragment checks are labelled historical.
 methods_audit=json.loads(z.read('methods_revision_inputs/methods_delivery_audit.json'))
 for filename,expected in methods_audit['file_sha256'].items():
  check('methods_source_hash:'+filename,sha(z.read('methods_revision_inputs/'+filename))==expected)
 check('methods_source_audit_pass',methods_audit['status']=='pass' and all(methods_audit['checks'].values()))
 # New source/code manifests and complete interval contract.
 for r in rows('CODE_MANIFEST.csv'):check('code_hash:'+r['path'],r['path'] in names and sha(z.read(r['path']))==r['sha256'])
 for r in rows('joint_strategy/input_manifest.csv'):check('joint_input_hash:'+r['path'],r['path'] in names and sha(z.read(r['path']))==r['sha256'])
 refs=rows('methods_revision_inputs/scholarly_reference_verification.csv')
 refjson=json.loads(z.read('methods_revision_inputs/scholarly_reference_verification.json'))
 check('scholarly_csv_json_agree',[{k:str(v) for k,v in r.items()} for r in refjson]==refs)
 check('scholarly_register_31_unique_keys',len(refs)==len({r['reference_key'] for r in refs})==31)
 academic=[r for r in refs if r['reference_type']=='academic']
 check('scholarly_register_30_academic',len(academic)==30)
 check('scholarly_register_nonempty_claim_and_locations',all(r['supported_manuscript_claim'] and r['manuscript_locations'] for r in refs))
 check('scholarly_register_unique_nonempty_dois',len([r['doi'] for r in academic])==len({r['doi'] for r in academic})==30 and all(r['doi'] for r in academic))
 check('scholarly_quartile_scheme_explicit',all(r['quartile_scheme'] and r['quartile_year'] and r['quartile_source'] and r['quartile_access_caution'] for r in academic))
 # Date-source semantics must survive packaging, not merely arithmetic checks.
 date_rows=rows('iberdrola/history_2019_2024/instrument_date_provenance.csv');d=date_rows[0]
 check('date_provenance_single_matching_isin',len(date_rows)==1 and d['instrument_isin']=='XS1890845875')
 check('contractual_issue_date_12_february',d['issue_date']=='2019-02-12')
 check('inventory_5_february_preserved',d['allocation_report_inventory_date']=='2019-02-05' and d['allocation_report_inventory_date_as_reported']=='05-Feb-19')
 check('no_pricing_date_inference','no pricing-date inference' in d['date_resolution'])
 b=rows('iberdrola/history_2019_2024/matched_green_hybrid_2019_2024.csv')
 check('date_semantics_all_24_records',len(b)==24 and all(r['issue_date']=='2019-02-12' and r['allocation_report_inventory_date']=='2019-02-05' for r in b))
 for fname in ['main_exhibits/figure1_timeline_source_rows.csv','joint_strategy/timeline_with_analysis_window_source_rows.csv']:
  rr=[r for r in rows(fname) if r['issuer']=='Iberdrola' and r['lane']=='Finance']
  check('contractual_timeline:'+fname,len(rr)==1 and rr[0]['date']==rr[0]['plot_start']==rr[0]['plot_end']=='2019-02-12' and rr[0]['source_url']==d['issue_date_source_url'] and rr[0]['allocation_report_inventory_date']=='2019-02-05')
 for fname in ['review_revision_inputs/three_core_evidence_matrix.csv','main_exhibits/three_core_evidence_matrix.csv']:
  r=next(r for r in rows(fname) if r['claim_id']=='IBE06')
  check('IBE06_date_resolution:'+fname,'contractual Issue Date is 12 February 2019' in r['available_evidence'] and 'inventory separately reports 5 February 2019' in r['available_evidence'] and d['issue_date_source_url'] in r['source_urls'])
 check('semantic_date_tests_pass',json.loads(z.read('iberdrola/history_2019_2024/issue_date_validation.json'))['all_pass'])
 jp=rows('joint_strategy/matched_interval_panel.csv')
 check('joint_eleven_intervals',len(jp)==11)
 check('joint_counts_5_5_1', {k:sum(r['issuer']==k for r in jp) for k in ['Enel','Iberdrola','SSE']}=={'Enel':5,'Iberdrola':5,'SSE':1})
 check('joint_allocation_stocks_not_flows',all(abs(float(r['allocation_stock_change_m']))<1e-8 for r in jp))
 check('old_numbered_main_exhibits_retired',not any(n in names for n in ['main_exhibits/table2_claim_evidence_synthesis.csv','main_exhibits/table3_finance_delivery_comparison.csv','main_exhibits/figure2_allocation_replacement.png','main_exhibits/figure2_allocation_replacement.svg']))
 check('maturity_missing_zero_fixtures',all(r['status']=='PASS' for r in rows('main_exhibits/maturity_missing_zero_regression_tests.csv')))
 screen=rows('integrated/issuer_screen.csv');check('nine_candidate_screen',len(screen)==9 and {r['issuer'] for r in screen}=={'Iberdrola','SSE','Enel','CLP','Ørsted','EDF','ENGIE','EDP','RWE'})
 contract=json.loads(z.read('main_exhibits/canonical_manuscript_exhibits.json'))
 check('four_main_tables',len(contract['table_order'])==4);check('three_figures',len(contract['figures'])==3)
 from openpyxl import load_workbook
 wb=load_workbook(io.BytesIO(z.read('main_exhibits/utility_transition_evidence.xlsx')),read_only=True,data_only=False)
 for i,t in enumerate(contract['table_order']):
  cells=list(csv.reader(io.StringIO(z.read('main_exhibits/'+t['file']).decode('utf-8-sig'))))
  expected=[t['headers']]+t['rows'];check('canonical_csv_table_'+str(t['number']),cells==expected)
  actual=[[str(x) if x is not None else '' for x in r] for r in wb.worksheets[i].values]
  check('canonical_workbook_table_'+str(t['number']),actual==expected)
 if a.docx:
  # DOCX parsing uses XML, so no extra docx dependency is required.
  import xml.etree.ElementTree as ET
  ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
  with zipfile.ZipFile(a.docx) as d:root=ET.fromstring(d.read('word/document.xml'))
  tables=[]
  for tb in root.findall('.//w:tbl',ns):
   tables.append([[''.join(t.text or '' for t in tc.findall('.//w:t',ns)) for tc in tr.findall('w:tc',ns)] for tr in tb.findall('w:tr',ns)])
  for t in contract['table_order']:
   expected=[t['headers']]+t['rows'];check('exact_word_table_'+str(t['number']),expected in tables)
  paras=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in root.findall('.//w:body/w:p',ns)]
  check('word_en_g21_visible',any('EN-G21' in p for p in paras))
  figcaps=[p for p in paras if re.match(r'^Figure ([123])(?:\.|\s)',p)]
  check('word_figure_caption_order',[int(re.match(r'^Figure ([123])',p).group(1)) for p in figcaps]==[1,2,3])
  children=list(root.find('w:body',ns));placement=[]
  for j,node in enumerate(children):
   txt=''.join(t.text or '' for t in node.findall('.//w:t',ns))
   if re.match(r'^Figure ([123])(?:\.|\s)',txt):
    previous=[n for n in children[:j] if n.tag.endswith('}p') and (n.findall('.//w:drawing',ns) or ''.join(t.text or '' for t in n.findall('.//w:t',ns)).strip())]
    placement.append(bool(previous and previous[-1].findall('.//w:drawing',ns)))
  check('word_captions_below_images',len(placement)==3 and all(placement))
summary={'archive':Path(a.archive).name,'archive_sha256':sha(Path(a.archive).read_bytes()),'checks':len(checks),'pass':not errors,'failed':errors,'details':checks}
if a.output:Path(a.output).write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='details'},indent=2));sys.exit(bool(errors))
