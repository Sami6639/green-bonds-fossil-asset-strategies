import csv,json,hashlib,re
from pathlib import Path
P=Path(__file__).parent;S=P/'sources';urls={r['source_id']:r['url'] for r in csv.DictReader((P/'source_manifest.csv').open())};urls.update(json.loads((P/'followup_source_urls.json').read_text()))
def write(name,rows):
 with (P/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def pages(n):return (S/(n+'.txt')).read_text().split('\f')
def page(n,term):return next(i+1 for i,s in enumerate(pages(n)) if term in s)
# Same issuer bulletins pair opening and closing values; exact regional arithmetic, no forced plant conversion.
d={2019:([15828,6340,5052,813,3623],[11695,6206,4825,664,0]),2020:([11695,6206,4825,664,0],[8903,5594,2764,545,0]),2021:([8903,5594,2764,545,0],[6910,4720,1644,546,0]),2022:([6910,4720,1644,546,0],[6590,4720,1644,226,0]),2023:([6590,4720,1644,226,0],[4627,4160,241,226,0])}
rs=[]
for y,(a,b) in d.items():
 n=f'operations_{y}';ps=pages(n)
 for region,opening,closing in zip(['Group','Italy','Iberia','Latin America','Europe_Russia'],a,b):
  term={'Group':'Installed capacity','Italy':'Italy','Iberia':'Iberia','Latin America':'Latin America','Europe_Russia':'Europe'}[region]
  candidates=[i+1 for i,s in enumerate(ps) if term in s and 'Coal' in s and 'Installed capacity' in s]
  if y==2019:candidates=[i+1 for i,s in enumerate(ps) if 'Coal' in s and '11,695' in s and '15,828' in s]
  rs.append(dict(issuer='Enel',flow_year=y,opening_date=f'{y-1}-12-31',closing_date=f'{y}-12-31',region=region,opening_coal_MW=opening,closing_coal_MW=closing,change_MW=closing-opening,basis='Consolidated installed capacity; matches annual net-efficient group series',source_id=n,source_pdf_page=';'.join(map(str,candidates)),source_url=urls[n],status='reported_cells' if region!='Europe_Russia' or y<=2020 else 'zero_coal_scope_after_2019_disposal; no coal row in later Europe tables',boundary='2019 flows require end2018 opening; do not add to end2019-end2024 change. Regional change is not automatically retirement MW.'))
rs.append(dict(issuer='Enel',flow_year=2024,opening_date='2023-12-31',closing_date='2024-12-31',region='Group',opening_coal_MW=4627,closing_coal_MW=4627,change_MW=0,basis='Net efficient installed capacity',source_id='annual_2024',source_pdf_page=178,source_url='https://www.enel.com/content/dam/enel-com/documenti/investitori/informazioni-finanziarie/2024/annuali/en/integrated-annual-report_2024.pdf',status='reported_cells',boundary='No aggregate coal capacity movement; generation decline is not capacity retirement'))
write('coal_capacity_regional_bridge_2019_2024.csv',rs)
# Distinguish independently stated event capacity from the portfolio movement that event may explain.
E=[]
def event(id,asset,etype,decision,implemented,eventmw,mwbasis,observed,obsbasis,decision_src,decision_pg,impl_src,impl_pg,post,note):
 E.append(dict(event_id=id,asset=asset,event_type=etype,decision_date=decision,implementation_date=implemented,event_capacity_MW=eventmw,event_MW_basis=mwbasis,associated_observed_change_MW=observed,observed_change_basis=obsbasis,decision_source=decision_src,decision_pdf_page=decision_pg,decision_url=urls.get(decision_src,''),implementation_source=impl_src,implementation_pdf_page=impl_pg,implementation_url=urls.get(impl_src,''),post_event_status=post,boundary_note=note))
event('ENEL_COAL_2019_REFT','Reftinskaya GRES','disposal','2019-06-20','2019-10-01',3800,'gross/installed physical plant; six300MW plus four500MW',-3623,'directly stated Enel net-efficient disposal contribution','half_year_2019',62,'annual_2019',118,'Buyer independently operating after2020-06-30; Enel Russia annual2020p38','2019 ownership exit, not closure. Buyer JSC Kuzbassenergo. Pre-outcome agreement in half-year report; completion annual2019p149. Operational lease continuedOct2019-Jun2020. Parent held56.43% ofEnelRussia; line-by-line group series must not be multiplied bythis share. Outside end2019-end2024 stock bridge.')
event('ENEL_COAL_2020_SPAIN','Compostilla II / Teruel','closure','2018-12-19','2020-06-30',None,'gross individual capacity not used in net reconciliation',-2061,'observed Iberia coal-stock change4825→2764; Endesa mainland net4584→2523 corroborates','endesa_annual_2020',page('endesa_annual_2020','19 December 2018'),'endesa_annual_2020',page('endesa_annual_2020','on 30 June 2020'),'closed; dismantling startedQ42020','The two named closures align with mainland net change; no plant-specific split asserted. Decision dates are closure applications disclosed retrospectively in2020 report. Chronological pre-outcome public document still needed if strict original-disclosure vintage required.')
event('ENEL_COAL_2020_BRINDISI','Brindisi Federico II unit2','closure','2020-01; authorization2020-05-28','2021-01-01',None,'unit netMW unverified',-612,'observed Italy2020 coal-stock change6206→5594','annual_2020',193,'annual_2020',193,'closed; permits for site conversion togas noted','2020 sustainability describes2020 shutdown whereas annual report specifies effectiveJan1,2021. Preserve accounting year and legal date separately. Do not assign every612MW to unit without unit-level net proof.')
event('ENEL_COAL_2020_BOC_I','Bocamina I','closure','2020-05-28','2020-12-31/2021-01',128,'reported unit capacity; gross/net not harmonized',-119,'observed LatinAmerica2020 coal change664→545; bulletin also reports1MW added capacity','annual_2020',194,'annual_2020',194,'closed','Annual report January2021 versus other disclosuresDec31,2020. No128→119 conversion asserted; original plan2019 was2023.')
event('ENEL_COAL_2021_LITORAL','Litoral','closure','2019-12-27','2021-12',1120,'reported installed eventMW, same as Iberia change',-1120,'Iberia coal-stock2764→1644','endesa_annual_2020',page('endesa_annual_2020','19 December 2018'),'annual_2021',8,'closed; sustainability2022p197 confirmsDecember2021','2020 report anticipatedmid2021 authorization; final closure period differs.2019 application retrospectively disclosed.')
event('ENEL_COAL_2021_ITALY','La Spezia / Fusina units1-2','closure','LaSpezia authorization2021-12-02','2021',863,'548MW LaSpezia +315MW Fusina1-2 directly reported',-874,'observed Italy2021 coal-stock5594→4720','annual_2021',227,'annual_2021',8,'closed','11MW Italian difference not assigned. Group named1983MW vs net1993MW gives10MW difference because LatinAmerica increased1MW. Do not force residual tozero or assume basis equivalence.')
event('ENEL_COAL_2022_BOC_II','Bocamina II','closure','2020-05-28','2022-09-30',350,'reported installed/gross unit capacity',-320,'observed LatinAmerica2022 coal-stock546→226; Italy/Iberia unchanged','annual_2020',194,'sustainability_2022',202,'permanently disconnected; Chile no remaining coal plants','Initial plannedMay31,2022 delayed toSeptember30;2022 reportp151 documents authorizationdelay.320MW is regional netchange, not a numerical conversion of350MW gross.')
event('ENEL_COAL_2023_FUSINA','Fusina remaining coal units','closure','authorization process; precise application date unverified','2023',500,'rounded0.5GW in sustainability2023p109',-560,'observed Italy2023 coal-stock4720→4160','annual_2023',164,'annual_2023',164,'coal units decommissioned; CCGT conversion planned','Rounded500MW must not overwrite exact regional560MW.2024 report discusses gasconversion; closure of coal does not prove a non-fossil site.')
event('ENEL_COAL_2023_PONTES','As Pontes','closure','2019-12-27','2023',1400,'rounded1.4GW in sustainability2023p109',-1403,'observed Iberia2023 coal-stock1644→241','endesa_annual_2020',page('endesa_annual_2020','19 December 2018'),'annual_2023',164,'closed; Alcudia241MW remains inIberia','2022 sustainabilityp151 states closure requested2019 for2021 was not authorized;2023 implementation is distinct from the original schedule.')
write('coal_decision_event_dossier.csv',E)
# Summary arithmetical bridges: coverage can be complete geographically while asset mechanism remains incomplete.
R=[]
for y,(a,b) in d.items():
 delta=b[0]-a[0];regional=sum(b[i]-a[i] for i in range(1,5))
 R.append(dict(flow_year=y,opening_group_coal_MW=a[0],closing_group_coal_MW=b[0],reported_group_change_MW=delta,sum_regional_changes_MW=regional,regional_reconciliation_residual_MW=delta-regional,plant_mechanism_status={2019:'Reftinskaya3623MW net disposal directly attributed; other510MW not fully asset-resolved',2020:'Named closures corroborated; regions612Italy/2061Iberia/119LatAm; individual netMW/timing require boundary discipline',2021:'Named installed closures1983MW; group netdecrease1993MW;10MW unresolved difference',2022:'BocaminaII closure corroborated; LatinAmerica netchange320MW; no gross-net conversion asserted',2023:'Fusina andAsPontes closures corroborated; Italy560MW/Iberia1403MW regional changes; source plant capacities rounded'}[y]))
R.append(dict(flow_year=2024,opening_group_coal_MW=4627,closing_group_coal_MW=4627,reported_group_change_MW=0,sum_regional_changes_MW='',regional_reconciliation_residual_MW='',plant_mechanism_status='No change atgroup level; regional cells not extracted for2024; generation decline not retirement'))
write('coal_bridge_validation.csv',R)
# Save exact page evidence and all used report source references.
for n,pgn in {'annual_2019':[118,149],'annual_2020':[145,146,193,194],'annual_2021':[8,227],'annual_2022':[200],'annual_2023':[164],'enel_russia_2020':[38,47],'half_year_2019':[62,152],'endesa_annual_2020':[page('endesa_annual_2020','19 December 2018'),page('endesa_annual_2020','on 30 June 2020'),249]}.items():
 ps=pages(n)
 for pg in pgn:(P/'source_cells'/f'{n}_pdfpage_{pg}.txt').write_text(ps[pg-1])
for y in d:
 n=f'operations_{y}'
 for pg,s in enumerate(pages(n),1):
  if 'Coal' in s:(P/'source_cells'/f'{n}_pdfpage_{pg}.txt').write_text(s)
manifest=list(csv.DictReader((P/'source_manifest.csv').open()));known={r['source_id'] for r in manifest}
for n,u in urls.items():
 f=S/(n+'.pdf')
 if f.exists() and n not in known:manifest.append(dict(source_id=n,url=u,local_file=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),retrieved_utc_date='2026-10-10',document_type='official issuer annual/interim/operating-data report'))
write('source_manifest.csv',manifest)
print('Created',len(E),'decision-event dossiers;',len(rs),'regional cells;',len(manifest),'sources')
