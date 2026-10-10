"""Finalize workbook and outputs, then manifests, then deterministic data/code ZIP."""
from pathlib import Path
import csv,json,hashlib,zipfile,io,datetime,re,sys,platform,importlib.metadata
import pandas as pd
from openpyxl.styles import Font,PatternFill,Alignment
P=Path(__file__).parent;O=P/'main_exhibits';J=P/'joint_strategy'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def record(f,key='path'):return {key:str(f.relative_to(P)),'sha256':sha(f),'bytes':f.stat().st_size}
folders=['iberdrola','sse','clp','orsted','enel','integrated','integrated_history','review_revision_inputs','joint_strategy','decision_evidence','methods_revision_inputs']
folders=[n for n in folders if (P/n).exists()]
# Refresh the snapshot-review provenance after the narrowly corrected input records.
review_manifest=P/'review_revision_inputs/review_input_provenance_manifest.csv'
review_rows=list(csv.DictReader(review_manifest.open(encoding='utf-8-sig',newline='')))
for r in review_rows:
 if r.get('packaging_status')=='included_derived_input':
  f=P/r['input_file'];r['sha256']=sha(f);r['bytes']=f.stat().st_size
pd.DataFrame(review_rows).to_csv(review_manifest,index=False,lineterminator='\n')
# No original PDF redistribution. Source registers retain exact URLs/locators/fingerprints.
inputs=[]
for folder in folders:
 for f in sorted((P/folder).rglob('*.csv')):
  if not any(x in f.parts for x in ['sources','source_cells','excluded_sources','local_sources']):inputs.append(record(f))
pd.DataFrame(inputs).to_csv(O/'source_derived_input_manifest.csv',index=False,lineterminator='\n')
versions={n:importlib.metadata.version(n) for n in ['pandas','numpy','matplotlib','openpyxl']}
(P/'requirements.txt').write_text('\n'.join(f'{n}=={v}' for n,v in versions.items())+'\n')
(P/'BUILD_ENVIRONMENT.json').write_text(json.dumps({'python':platform.python_version(),'packages':versions,'scope':'Versions used for the verified offline rebuild; no source downloads or external writes'},indent=2)+'\n')
contract=json.loads((O/'canonical_manuscript_exhibits.json').read_text())
sheets=[(f'Table {t["number"]} '+['Case coverage','Matched strategy','Decision chains','Capacity bridges'][t['number']-1],O/t['file']) for t in contract['table_order']]
sheets.extend([(n,P/p) for n,p in [
 ('Matched interval panel','joint_strategy/matched_interval_panel.csv'),('Interval pattern audit','joint_strategy/interval_pattern_audit.csv'),('Finance observation states','joint_strategy/finance_observation_states.csv'),('Fossil event inventory','joint_strategy/bounded_fossil_event_inventory.csv'),('Decision chains','decision_evidence/decision_chain_matrix.csv'),('Decision claims','decision_evidence/decision_source_claims.csv'),('Decision source register','decision_evidence/decision_source_register.csv'),('Detailed claim matrix','main_exhibits/three_core_evidence_matrix.csv'),('Prior claim synthesis','joint_strategy/appendix_claim_evidence_synthesis.csv'),('Finance maturity detail','joint_strategy/appendix_finance_delivery_comparison.csv'),('SSE maturity weights','main_exhibits/sse_gb5_maturity_project_weights.csv'),('SSE maturity analysis','main_exhibits/sse_gb5_maturity_stock_analysis.csv'),('SSE boundary sensitivity','main_exhibits/sse_capacity_boundary_sensitivity.csv'),('Enel companion issues','main_exhibits/enel_reallocation_by_issue_companion.csv'),('Appendix continuity','main_exhibits/appendix_pool_continuity.csv'),('Bridge components','main_exhibits/appendix_capacity_bridge_components.csv'),('Joint analysis checks','joint_strategy/validation_checks.csv'),('Missing zero tests','main_exhibits/maturity_missing_zero_regression_tests.csv'),('Timeline sources','joint_strategy/timeline_with_analysis_window_source_rows.csv'),('Empirical source register','methods_revision_inputs/empirical_source_register.csv'),('Final claim ledger','methods_revision_inputs/methods_results_claim_ledger.csv'),('Instrument date provenance','iberdrola/history_2019_2024/instrument_date_provenance.csv'),('Scholarly reference verification','methods_revision_inputs/scholarly_reference_verification.csv')
 ] if (P/p).exists()])
with pd.ExcelWriter(O/'utility_transition_evidence.xlsx',engine='openpyxl') as w:
 for sheet,filename in sheets:pd.read_csv(filename,keep_default_na=False).to_excel(w,sheet_name=sheet[:31],index=False)
 w.book.properties.created=datetime.datetime(2026,10,10);w.book.properties.modified=datetime.datetime(2026,10,10)
 for ws in w.book.worksheets:
  ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
  for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='355770');c.alignment=Alignment(wrap_text=True)
  for col in ws.columns:
   ws.column_dimensions[col[0].column_letter].width=min(60,max(16,max(len(str(c.value or '')) for c in col[:30])+2))
   for c in col[1:]:c.alignment=Alignment(wrap_text=True,vertical='top')
  ws.row_dimensions[1].height=32
# Normalize inner XLSX ZIP timestamps and modified metadata.
f=O/'utility_transition_evidence.xlsx';raw=f.read_bytes();out=io.BytesIO()
with zipfile.ZipFile(io.BytesIO(raw)) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as w:
 for name in sorted(z.namelist()):
  content=z.read(name)
  if name=='docProps/core.xml':content=re.sub(rb'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',rb'\g<1>2026-10-10T00:00:00Z\2',content)
  info=zipfile.ZipInfo(name,(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o600<<16;w.writestr(info,content)
f.write_bytes(out.getvalue())
(P/'PACKAGE_README.txt').write_text('''GREEN BOND FINANCING AND FOSSIL ASSET STRATEGIES IN ELECTRIC UTILITIES
FINAL REVISION: DERIVED EVIDENCE AND REPRODUCIBLE CODE

Offline rebuild: python run_analysis.py
Full ZIP integrity: python validate_package.py
The tested dependency versions are requirements.txt / BUILD_ENVIRONMENT.json. The supported offline entry point is run_analysis.py; historical extraction scripts retain source-generation provenance and may require original reports that are not redistributed. The rebuild uses included source-derived CSVs; it performs no source downloads, regression, causal estimation, or external-service writes. Original reports are linked and fingerprinted where available, not redistributed. No GitHub upload or public repository release is claimed.

Date provenance: XS1890845875 has contractual Issue Date 12 February 2019 (Offering Circular, IB-OC19, PDF/printed pp. 6, 47 and 64). The 2019 allocation inventory separately reports 05-Feb-19 (PDF p. 3 / printed p. 2). Both source dates and their distinct meanings are preserved in instrument_date_provenance.csv and the matched data; no pricing-date interpretation is inferred. Annual-vintage findings and the final figure designs are unchanged. validate_issue_date_provenance.py checks the distinction and downstream evidence/timeline records.

Core new analysis: build_joint_strategy.py constructs every admissible adjacent selected-finance comparison (five Enel report-vintage pairs, five Iberdrola pairs and one exact SSE fiscal pair), classifies the identified annual fossil-event mixtures and retains unchanged and unresolved periods. Read joint_strategy/METHOD_AND_COVERAGE.txt. Enel/Iberdrola vintage alignment does not imply exact same-day allocation. SSE only uses 31 March 2023–31 March 2024; Keadby 2 and Triton are prior context. The new source audit preserves conflicting September/December 2023 Tarbert closure descriptions without changing its fiscal interval.

Scholarly references: methods_revision_inputs/scholarly_reference_verification.csv contains the final 30 academic references plus ICMA guidance, verified metadata and DOI/source links, supported claims and manuscript locations. Quartile observations retain the specific dated CiteScore 2024 scheme, category and source; they do not claim a current JCR classification. Access-depth and other verification limits are explicit. No third-party full-text articles are redistributed.

Main exhibits: main_exhibits/canonical_manuscript_exhibits.json lists exactly four tables and three figures. Table 1 selection; Table 2 joint sequences; Table 3 decision chains; Table 4 longer-window capacity boundaries. Superseded claim/maturity tables and allocation-replacement figure have moved to explicitly named joint_strategy supplements. The workbook starts with exact canonical tables and then detailed evidence. The original source package is preserved separately and not overwritten. prior_release_clean_workspace_reproduction.json and prior_strategy_release_clean_workspace_reproduction.json are historical evidence ONLY; clean_workspace_reproduction.json, when present, records this release's separately performed clean rebuild.

Measurement: allocations are stocks, not annual flows. Project money is not equal-weighted when missing. Operating status, first production and full COD are distinct. SSE explicit-zero production is separate from missing production; regression fixtures test this. Enel gross/installed unit ratings are not converted into net-efficient portfolio contributions without evidence. Iberdrola technology and SSE Thermal boundaries differ and are not pooled. A balanced bridge or unchanged stock does not establish complete gross-event coverage. No company ranking, global prevalence, financing additionality or causal bond effect is estimated. Decision-chain rationales are issuer statements and do not trace sale receipts or bond proceeds unless the evidence explicitly does so.

Integrity: package/code/source/derived manifests are built only after all outputs, workbook, notes and dependency records. PACKAGE_MANIFEST.csv covers EVERY archive member except itself. Code manifest covers included Python scripts; source manifests cover exact source-derived inputs and independent original-source URLs/fingerprints. The self-manifest exception prevents circular hashing. Deterministic ZIP timestamps and workbook metadata permit byte-for-byte offline rebuild checks.
''')
# Dictionary includes units plus uncertainty/coverage semantics.
dictionary=[['matched_interval_panel','interval_id','identifier','Issuer-specific adjacent pair, never a pooled-year panel'],['matched_interval_panel','allocation_stock_change_m','currency million','Difference of reported stocks, not annual flow; Enel EUR986m is rounded table precision, original summary EUR985.6m is distinct'],['matched_interval_panel','identified_physical_closure_mw','issuer-specific MW','Signed source-basis contribution; blank for unresolved Enel full gross bridge'],['matched_interval_panel','unresolved_net_residual_mw','issuer-specific MW','Known stock change not attributed to classified event; zero is not exhaustive coverage'],['matched_interval_panel','disclosed_reassignment_m','currency million','Published reassignment in selected issue; missing means no amount established, not zero'],['finance_observation_states','operating_status_share_of_line_sum_pct','percent','Enel rounded line allocation-weighted source operating status; not harmonized full COD'],['finance_observation_states','full_operation_share_pct','percent','SSE financial stock at full operation over unchanged GBP543.9m; not capacity or generation'],['bounded_fossil_event_inventory','standalone_event_mw','source-specific MW','Enel event ratings retain heterogeneous gross/installed/rounded bases; not added to group net-efficient bridge'],['bounded_fossil_event_inventory','common_window_inclusion','classification','In matched interval or antecedent context only'],['maturity_missing_zero_regression_tests','expected','classification','Blank production is unresolved; explicit zero permits no-generation classification']]
dictionary.extend([['matched_green_hybrid_2019_2024','issue_date','ISO date','Contractual Issue Date defined by offering circular; separate from its document date and allocation-inventory date'],['matched_green_hybrid_2019_2024','allocation_report_inventory_date','ISO date','Date recorded under Issue date in the 2019 allocation inventory; preserved as reported, without pricing-date inference'],['instrument_date_provenance','date_resolution','source interpretation','Contractual circular governs issue_date; source discrepancy remains visible in separately named fields']])
pd.DataFrame(dictionary,columns=['table','field','unit','meaning']).to_csv(O/'data_dictionary.csv',index=False,lineterminator='\n')
# Derived manifest after all main outputs are finalized.
main=[f for f in sorted(O.iterdir()) if f.is_file() and f.name!='derived_manifest.csv']
pd.DataFrame([{'file':f.name,'sha256':sha(f),'bytes':f.stat().st_size} for f in main]).to_csv(O/'derived_manifest.csv',index=False,lineterminator='\n')
files=[]
for folder in folders+['main_exhibits']:
 for f in (P/folder).rglob('*'):
  if not f.is_file() or any(x in f.parts for x in ['sources','source_cells','excluded_sources','visual_qa','__pycache__','local_sources']):continue
  if f.suffix.lower() in ['.csv','.py','.json','.txt'] or (folder in ['main_exhibits','joint_strategy'] and f.suffix.lower() in ['.png','.svg','.xlsx']):files.append(f)
for f in P.iterdir():
 if f.is_file() and (f.suffix.lower() in ['.py','.txt','.json'] or f.name=='README.md') and f.name not in ['PACKAGE_MANIFEST.csv','CODE_MANIFEST.csv']:files.append(f)
files=sorted(set(files))
code=[f for f in files if f.suffix=='.py'];pd.DataFrame([record(f) for f in code]).to_csv(P/'CODE_MANIFEST.csv',index=False,lineterminator='\n');files.append(P/'CODE_MANIFEST.csv')
files=sorted(set(files));pd.DataFrame([record(f) for f in files]).to_csv(P/'PACKAGE_MANIFEST.csv',index=False,lineterminator='\n');files.append(P/'PACKAGE_MANIFEST.csv')
archive=P/'utility_transition_strategy_evidence.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):
  info=zipfile.ZipInfo(str(f.relative_to(P)),(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,f.read_bytes())
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 assert not any(n.endswith('.pdf') or '/sources/' in n or '/source_cells/' in n or '/local_sources/' in n for n in z.namelist())
print(json.dumps({'archive':archive.name,'files':len(files),'bytes':archive.stat().st_size,'sha256':sha(archive),'manifest_generated_after_outputs':True}))
