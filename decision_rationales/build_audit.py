from pathlib import Path
import pandas as pd,json,hashlib
P=Path(__file__).resolve().parent
x=pd.read_csv(P/'frozen_inputs/principal33_selected_window_event_evidence.csv').fillna('')
rows=[]
for _,r in x.iterrows():
 j=json.loads(r.event_raw_json)
 rows.append(dict(event_record_id=r.event_record_id,group_id=r.group_id,issuer=r.issuer_label,asset=r.asset,event_date=r.event_date_raw,event_type=r.event_type_canonical,source_url=r.source_url,source_locator=r.source_locator,archived_decision_date=j.get('decision_date_reported',''),archived_decision_source_url=j.get('decision_source_url',''),archived_decision_source_locator=j.get('decision_source_locator',''),archived_finance_connection=j.get('finance_connection',''),archived_context=' | '.join(f'{k}: {v}' for k,v in j.items() if k in ['notes','interpretive_caution','ownership_perimeter_effect','perimeter_effect']),dedicated_rationale_field_present=any('rationale' in k for k in j),interpretation='Archive supports event coding; missing dedicated rationale is not evidence that the company disclosed no rationale.',raw_record=r.event_raw_json))
y=pd.DataFrame(rows); y.to_csv(P/'all97_archive_field_audit.csv',index=False)
g=pd.read_csv(P/'frozen_inputs/principal33_direction_event_presence_long.csv').drop_duplicates('group_id')[['group_id','issuer','fossil_direction']]
g=g.merge(x.groupby('group_id').size().rename('archived_event_records'),how='left',on='group_id').fillna({'archived_event_records':0})
g['archived_event_records']=g.archived_event_records.astype(int)
g['coverage_interpretation']=g.archived_event_records.map(lambda n:'Bounded event archive; not an exhaustive decision census' if n else 'No selected-window event record in frozen archive; decisions and rationales unknown')
g.to_csv(P/'all33_group_coverage.csv',index=False)
s={'event_records':len(x),'groups_with_event_records':x.group_id.nunique(),'principal_groups':len(g),'groups_without_event_records':g[g.archived_event_records==0].issuer.tolist(),'rows_with_nonempty_decision_date_field':int((y.archived_decision_date!='').sum()),'rows_with_decision_source_url':int((y.archived_decision_source_url!='').sum()),'rows_with_dedicated_rationale_field':int(y.dedicated_rationale_field_present.sum()),'rows_with_finance_connection_field':int((y.archived_finance_connection!='').sum()),'finance_connection_values':y[y.archived_finance_connection!=''].archived_finance_connection.tolist(),'input_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'frozen_inputs').glob('*')}}
(P/'audit_summary.json').write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(s,indent=2))
