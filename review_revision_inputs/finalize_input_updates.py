from pathlib import Path
p=Path('/workspace/shared/bse_utility_pilot_20261010/review_revision_inputs/build_review_inputs.py')
s=p.read_text()
s=s.replace('quantitative financing/refinancing split; full gross-event census','realized quantitative financing/refinancing split (a 25% pre-issue expectation is separately documented); full gross-event census')
s=s.replace("'Project weights, financing/refinancing shares and incremental financing effects.'","'Project weights, realized refinancing shares and incremental financing effects.'")
s=s.replace("'SSE: refinancing and stable allocation imply unchanged physical maturity.'","'SSE: financial continuity and project maturity are distinct.'")
s=s.replace("'Requires amounts, decisions and actual operation dates. GB5 retains GBP 543.9 million across two reports, while full operation occurs in 2021, 2023 and 2024.'","'GB5 retains GBP 543.9 million across the 2023–2024 reports; project operation dates differ. Gordonbush retains GBP 37.2 million and operational status at both snapshots.'")
s=s.replace("'Monetary continuity is supported for 2023–2024; uniform pre-issue operation is contradicted.'","'Monetary continuity is supported for two snapshots, including stable Gordonbush maturity; it does not establish uniform timing across projects.'")
s=s.replace("'Pre-2023 allocation history and financing-induced delivery; Viking’s 443/434 MW discrepancy.'","'Earlier allocations, within-year changes, complete ownership continuity and financing-induced delivery; Viking’s 443/434 MW discrepancy.'")
insert=r'''
# Final source corrections from the shared verified instrument ledger and retained reports.
C=Path('/workspace/shared/bse_utility_revision_20261010')
commit_copy=O/'verified_commitment_source_ledger.csv'
shutil.copyfile(C/'commitment_source_ledger.csv',commit_copy)
commit_rows=list(csv.DictReader(commit_copy.open(encoding='utf-8-sig',newline='')))
commit_keys={'Enel':{'EN-FW18'},'Iberdrola':{'IB-SPO19','IB-GR19'},'SSE':{'SS-FW21','SS-SPO22','SS-CR24'}}
for row in M:
 if row['dimension']=='Instrument commitment scope':
  selected=[x for x in commit_rows if x['source_key'] in commit_keys[row['issuer']]]
  row['source_files']=str(commit_copy)
  row['source_urls']=' | '.join(uniq(x['source_url'] for x in selected))
  row['source_locators']=' | '.join(x['source_key']+': '+x['locator'] for x in selected)
  row['verification_basis']='The shared verification ledger and companion commitment-boundaries memo were reviewed locally; document-level verification and access limitations are preserved in that ledger.'
  if row['issuer']=='Iberdrola':
   row['available_evidence']='The 4 February 2019 opinion identifies East Anglia ONE and Wikinger, an anticipated 25% refinancing share, full allocation expected within 12 months, and substitution following divestment. No named bond-linked fossil-exit condition was identified in the examined provisions.'
   row['inference_limit']='The 25% share is a pre-issuance expectation, not a verified realized split or additionality estimate. The archived standalone framework date remains unverified. Absence of a named exit condition is bounded to the inspected provisions; wider commitments are not denied.'
  if row['issuer']=='SSE':
   row['available_evidence']+=' The reporting-criteria record maps GB5 to the 2021 framework and states that proceeds were fully employed at settlement.'
 for key in ['available_evidence','inference_limit']:
  row[key]=row[key].replace('project money/refinancing shares and causal identification are absent','project money, realized refinancing shares and causal identification are absent')
# Persist page extracts in the authorized output directory, with exact original text.
annual=R/'enel/sources/annual_2023.txt'
pages=annual.read_text().split('\f')
extracts=[]
for page in [235,237,483]:
 path=O/f'enel_annual_2023_pdfpage_{page}_ownership.txt'
 path.write_text('Source: https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2023/annuali/en/integrated-annual-report_2023.pdf\nPDF/printed page: '+str(page)+'\n\n'+pages[page-1])
 extracts.append(str(path))
annual_url='https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2023/annuali/en/integrated-annual-report_2023.pdf'
kaf_url=next(x['source_url'] for x in commit_rows if x['source_key']=='EN-KAF19')
green_url=next(x['source_url'] for x in commit_rows if x['source_key']=='EN-GB23')
chain=[
 dict(event_id='EN_AU_2023_PARENT_SALE',event_date='2023-09-29',unit='Enel Green Power Australia (Pty) Ltd and Enel Green Power Australia Trust',event='Sale of 50% of both entities to INPEX; continuing joint control',project_link='The parent entities own the Group’s Australian renewables operations; Cohuna vehicle group ownership is separately verified below.',allocation_consequence='2023 green-bond report removes the Cohuna allocation following deconsolidation.',source_url=annual_url,source_locator='PDF/printed p. 235; agreement signed 13 July 2023; closing 29 September 2023.',source_files='enel/sources/annual_2023.txt | '+extracts[0],inference_limit='This is a parent-entity transaction, not evidence that a 50% stake in the Cohuna plant itself was directly sold. Joint control is at the subsidiary/JV level.'),
 dict(event_id='EN_COHUNA_2023_RETAINED_HOLDING',event_date='2023-12-31',unit='Cohuna Solar Farm (Pty) Ltd and Cohuna Solar Farm Trust',event='Equity consolidation; 50% Enel Group holding for each vehicle',project_link='Company-name schedule identifies the Cohuna project vehicles and their immediate holding entities.',allocation_consequence='Retained economic interest coexists with removal from the selected allocation pool.',source_url=annual_url,source_locator='PDF/printed p. 483; company-name rows and Group % holding column.',source_files='enel/sources/annual_2023.txt | '+extracts[2],inference_limit='Year-end group holding is observed. It does not establish a direct plant-stake transaction, unchanged physical operation or every within-year ownership state.'),
 dict(event_id='EN_HELLAS_2023_SUBSIDIARY_SALE',event_date='2023-12-29',unit='Enel Green Power Hellas',event='Sale of 50% to Macquarie Asset Management; continuing joint control',project_link='The official 15 October 2019 Kafireas release links that complex to Enel Green Power Hellas.',allocation_consequence='2023 green-bond report removes Kafireas allocation following deconsolidation.',source_url=annual_url+' | '+kaf_url,source_locator='Annual Report 2023 PDF/printed p. 237; Kafireas release opening paragraph.',source_files='enel/sources/annual_2023.txt | '+extracts[1]+' | '+str(commit_copy),inference_limit='The 50% transaction is at the Hellas subsidiary level. This evidence does not verify a direct sale of 50% of Kafireas or its exact plant-level ownership chain.'),
 dict(event_id='EN_2019_ISSUE_2023_REALLOCATION',event_date='2023 report vintage; exact allocation dates not identified',unit='Enel January 2019 green use-of-proceeds issue',event='EUR 30.93 million Cohuna plus EUR 125.93 million Kafireas replaced by EUR 55.38 million Alta Farms II plus EUR 101.48 million Seven Cowboy',project_link='Named source and destination projects are directly stated in the green-bond report.',allocation_consequence='EUR 156.86 million of selected-issue recorded allocation is reassigned after deconsolidation.',source_url=green_url,source_locator='2023 Green Bond Report PDF/printed p. 4 and footnotes 1–2.',source_files='enel/green_2019_issue_reassignment_disclosures.csv | '+str(commit_copy),inference_limit='The broader EUR 229.60 million combines 2018 and 2019 issues. Removal is not physical retirement or complete ownership exit; recipients were already operating in 2022.')
]
dump('enel_ownership_allocation_event_chain.csv',chain)
for row in M:
 if row['issuer']=='Enel' and row['dimension']=='Ownership':
  row['exact_claim']='The Cohuna/Kafireas allocation exits follow deconsolidation after subsidiary-level stake sales while Enel retains joint control and economic interests.'
  row['needed_evidence']='Transaction dates and entity-level stakes, project-to-subsidiary links, retained-control evidence, and an explicit connection between deconsolidation and allocation replacement.'
  row['available_evidence']='Australia: 50% of two parent entities sold to INPEX on 29 September 2023; joint control retained. Cohuna vehicles show 50% Group holding at year-end. Hellas: 50% sold on 29 December 2023 with joint control retained; an official release links Kafireas to Hellas. The green report explicitly connects deconsolidation to EUR 156.86 million of 2019-issue reassignment.'
  row['source_files']=str(O/'enel_ownership_allocation_event_chain.csv')+' | '+str(commit_copy)+' | '+' | '.join(extracts)
  row['source_urls']=green_url+' | '+annual_url+' | '+kaf_url
  row['source_locators']='2023 Green Bond Report p. 4; Annual Report 2023 pp. 235, 237 and 483; Kafireas issuer release 15 October 2019, opening paragraph.'
  row['inference_limit']='The 50% sales concern Australian parent entities and Hellas, not verified direct 50% plant sales. Continued joint control is at subsidiary/JV level. Allocation-pool removal does not establish physical retirement or complete economic exit; Kafireas’s exact plant-level stake is not inferred.'
  row['verification_basis']='Annual Report 2023 retained text pages 235, 237 and 483 were reviewed directly; project-subsidiary linkage and instrument provisions are supported by the shared verified commitment ledger.'
for row in screen:
 if row['issuer']=='Enel':
  row['specific_basis']+=' The 2023 parent/subsidiary transactions retain joint control; allocation exit is not complete economic exit.'
  row['inspected_sources']+=' | '+str(O/'enel_ownership_allocation_event_chain.csv')
  row['source_locators']+=' Annual Report 2023 PDF/printed pp. 235, 237 and 483.'
  row['source_urls']+=' | '+annual_url+' | '+kaf_url
 if row['issuer']=='Iberdrola':
  row['incomplete_extraction']=row['incomplete_extraction'].replace('quantitative financing/refinancing split','realized quantitative financing/refinancing split')
dump('final_nine_candidate_screen.csv',screen)
add('SSE','Bounded stable comparison','Gordonbush Extension retains both its reported GB5 allocation and full-operational status at the 2023 and 2024 snapshots.','The same-project financial amount and maturity status at each specified reporting cutoff.','Gordonbush shows GBP 37.2 million GB5 allocation in both reports and operational status at both 31 March snapshots; full operation is recorded as August 2021.','supported',SP+SN+SM,spages,'This is positive consistency within the selected records, not independent or out-of-sample validation. It supports endpoint amount and maturity continuity only; complete ownership continuity and within-year stability remain unidentified.','Gordonbush Extension only; GB5 report-to-31-March-2023 and report-to-31-March-2024 snapshots.')
'''
s=s.replace('# Order each case coherently.',insert+'\n# Order each case coherently.')
s=s.replace('30 claim-level assessments','31 claim-level assessments')
s=s.replace('including all seven common dimensions and three separately writer-verified instrument-commitment rows.','including all seven common dimensions, three instrument-commitment rows and a bounded stable Gordonbush comparison.')
s=s.replace('The main tables summarize the full screen and matrix;','The enel_ownership_allocation_event_chain.csv supplement preserves subsidiary-level transactions, retained joint control, and the allocation replacement separately; verified_commitment_source_ledger.csv preserves the originating source review.\n\nThe main tables summarize the full screen and matrix;')
# Escaped literal replacement needed inside the final Python string.
s=s.replace('originating source review.\n\nThe main tables','originating source review.\\n\\nThe main tables')
p.write_text(s)
