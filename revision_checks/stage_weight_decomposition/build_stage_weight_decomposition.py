#!/usr/bin/env python3
"""Exact two-date stage-versus-weight accounting decomposition (stdlib only).

Run from any working directory: python path/to/build_stage_weight_decomposition.py
Input verification checks are mechanical; primary-source semantic reinspection is
recorded separately in inputs/source_verification.csv and is not automated here.
No baseline release files are edited. Outputs are deterministic.
"""
from __future__ import annotations
import calendar
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INP, OUT = ROOT / 'inputs', ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
CHECKS = []

def check(name, condition, detail=''):
    CHECKS.append(dict(check=name, passed=bool(condition), detail=detail))
    if not condition:
        raise ValueError(f'{name}: {detail}')

def rows(name):
    with (INP/name).open(newline='', encoding='utf-8-sig') as f:
        return [dict(r, source_csv_row=str(i)) for i, r in enumerate(csv.DictReader(f), 2)]

def frac(s):
    if str(s).strip() in ('', 'NA', 'unknown', 'null'):
        raise ValueError('Missing monetary amount must not be imputed.')
    return Fraction(str(s))

def number(x, places=15):
    with localcontext() as c:
        c.prec = 60
        s = f'{Decimal(x.numerator)/Decimal(x.denominator):.{places}f}'
    return s.rstrip('0').rstrip('.') if '.' in s else s

def write_csv(name, rs):
    if not rs:
        raise ValueError('Empty output')
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader();w.writerows(rs)

def month_bounds(month):
    # Month precision is retained, not silently converted to an exact event date.
    y,m=map(int,month.split('-'))
    return f'{y:04d}-{m:02d}-01', f'{y:04d}-{m:02d}-{calendar.monthrange(y,m)[1]:02d}'

def sse_stage(month, date_status, cutoff):
    lo,hi=month_bounds(month)
    if date_status in ('actual',):
        if hi <= cutoff: return 1
        if lo > cutoff: return 0
        raise ValueError('Actual event month overlaps cutoff; stage unresolved.')
    if date_status in ('expected', 'expected_at_report') and lo > cutoff:
        return 0  # Source reports full operation as still due after the cutoff.
    raise ValueError('Unknown or elapsed forecast is not an achieved-operation code.')

# Every frozen input is checked before any calculation.
provenance=json.loads((INP/'input_provenance.json').read_text())
for r in provenance:
    p=ROOT/r['analysis_path']
    check('frozen_input_hash:'+r['analysis_path'],hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'])

panel=[]
project_ids={'Viking':'SSE_VIKING','Gordonbush Extension':'SSE_GORDONBUSH_EXT','Seagreen1':'SSE_SEAGREEN1','Seagreen 1':'SSE_SEAGREEN1'}
for r in rows('sse_2023_gb5_project_rows.csv'):
    check('sse_2023_instrument:'+r['project'],r['bond_id']=='GB5' and r['isin']=='XS2510903862')
    date='2023-03-31'
    panel.append(dict(case='SSE',instrument='GB5 / XS2510903862',project_id=project_ids[r['project']],project_name=r['project'],cutoff=date,currency='GBP',amount_million=r['allocation_stock_gbp_m'],full_operation=sse_stage(r['fully_operational_month'],r['operational_date_status'],date),amount_input='inputs/sse_2023_gb5_project_rows.csv',input_csv_row=r['source_csv_row'],baseline_repo_path='nested_histories/original_three/sse/green_uop_2023_gb5_project_rows.csv',allocation_source_id='SSE2023',allocation_source_url=r['source_url'],allocation_source_locator='Table 6; printed page 9 / PDF page 10; GB5 allocation column',stage_source_id='SSE2023',stage_source_url=r['source_url'],stage_source_locator='Table 6; printed page 9 / PDF page 10; date fully operational column',stage_evidence=r['fully_operational_month']+'; '+r['operational_date_status'],stage_rule='Achieved actual full operation by cutoff; explicitly future due-date is not achieved',project_scope='GB5 only; exclude GB6; monetary allocation weight is not capacity or output share'))
for r in rows('sse_2024_bond_project_rows.csv'):
    if r['bond_group']!='5': continue
    date='2024-03-31'
    panel.append(dict(case='SSE',instrument='GB5 / XS2510903862',project_id=project_ids[r['project']],project_name=r['project'],cutoff=date,currency='GBP',amount_million=r['allocated_gbp_million'],full_operation=sse_stage(r['operational_month'],r['operational_date_status'],date),amount_input='inputs/sse_2024_bond_project_rows.csv',input_csv_row=r['source_csv_row'],baseline_repo_path='nested_histories/original_three/sse/bond_project_rows_2024.csv',allocation_source_id='SSE2024',allocation_source_url=r['source_url'],allocation_source_locator='Table 6; PDF page 10; GB5 allocation column',stage_source_id='SSE2024',stage_source_url=r['source_url'],stage_source_locator='Table 6; PDF page 10; date fully operational column',stage_evidence=r['operational_month']+'; '+r['operational_date_status'],stage_rule='Achieved actual full operation by cutoff; explicitly future due-date is not achieved',project_scope='GB5 only; exclude GB6; monetary allocation weight is not capacity or output share'))

# Corroborate report-derived stages against retained actual milestones. Do not
# use a scheduled completion date as if it were an actual operation date.
milestones={r['project_id']:r for r in rows('sse_actual_milestones.csv') if r['event_type']=='full_operation'}
for r in panel:
    m=milestones[r['project_id']]
    lo,hi=month_bounds(m['event_date']) if len(m['event_date'])==7 else (m['event_date'],m['event_date'])
    check('milestone_does_not_straddle:'+r['project_id']+':'+r['cutoff'],hi<=r['cutoff'] or lo>r['cutoff'])
    check('sse_report_vs_actual_milestone:'+r['project_id']+':'+r['cutoff'],r['full_operation']==int(hi<=r['cutoff']))

for r in rows('wec_project_stage_panel.csv'):
    check('wec_known_binary:'+r['project_id']+':'+r['allocation_cutoff'],r['fully_operating_indicator'] in ('0','1'))
    check('wec_instrument:'+r['source_csv_row'],r['instrument_id']=='WEPCO_20220922_4_75_due2032')
    if r['project_id']=='Badger_Hollow_II':
        # Verified PSC decision p70 states the actual in-service date.
        indicator=int('2023-12-22' <= r['allocation_cutoff'])
        stage_id='WECPSC'; evidence='Actual in-service date 2023-12-22'
        rule='Actual in-service date after first cutoff and before second cutoff'
    elif r['project_id']=='Paris_Solar_Battery':
        # The solar component itself became commercial only in December 2024.
        # Full mixed-entry operation cannot precede that component milestone.
        check('paris_known_pre_solar_cutoff:'+r['allocation_cutoff'],r['allocation_cutoff']<'2024-12-01')
        indicator=0;stage_id='WEC10K';evidence='Solar component commercial December 2024; battery future in 2025 as reported'
        rule='Allocated mixed entry not fully operating at either June cutoff; no solar/storage monetary split invented'
    else: raise ValueError('Unresolved WEC reporting entry')
    check('wec_stage_vs_primary_date:'+r['project_id']+':'+r['allocation_cutoff'],indicator==int(r['fully_operating_indicator']))
    panel.append(dict(case='WEC',instrument='WEPCO 4.75% due 2032 / issued 2022-09-22',project_id=r['project_id'],project_name=r['project_name'],cutoff=r['allocation_cutoff'],currency='USD',amount_million=r['allocated_usd_million'],full_operation=indicator,amount_input='inputs/wec_project_stage_panel.csv',input_csv_row=r['source_csv_row'],baseline_repo_path='nested_histories/expanded_cases/wec_project_stage_panel.csv',allocation_source_id='WEC'+r['allocation_cutoff'][:4],allocation_source_url=r['allocation_source_url'],allocation_source_locator='PDF page 1; Eligible Green Projects Disbursement Report; cumulative from 2020-10-01',stage_source_id=stage_id,stage_source_url=r['stage_source_url'],stage_source_locator=r['stage_source_locator'],stage_evidence=evidence,stage_rule=rule,project_scope='Legal-issuer cumulative disbursements; preserve Paris Solar/Battery as one reporting entry'))

# Stage values and project-set equality are gates, not conveniences.
def validate_panel(ps):
    if any(r['full_operation'] not in (0,1) for r in ps):
        raise ValueError('Unknown stage; decomposition is not admissible.')
    keys=[(r['case'],r['project_id'],r['cutoff']) for r in ps]
    if len(set(keys))!=len(keys): raise ValueError('Duplicate project-cutoff key.')
    for case in sorted({r['case'] for r in ps}):
        rr=[r for r in ps if r['case']==case];dates=sorted({r['cutoff'] for r in rr})
        if len(dates)!=2: raise ValueError('Exactly two cutoffs required.')
        if {r['project_id'] for r in rr if r['cutoff']==dates[0]}!={r['project_id'] for r in rr if r['cutoff']==dates[1]}:
            raise ValueError('Unmatched project membership; do not impute entrants or exits.')
        if len({r['currency'] for r in rr})!=1: raise ValueError('Mixed currency within case.')
        if len({r['instrument'] for r in rr})!=1: raise ValueError('Mixed instruments within case.')
        if any(frac(r['amount_million'])<0 for r in rr): raise ValueError('Negative allocation.')
        for date in dates:
            if sum(frac(r['amount_million']) for r in rr if r['cutoff']==date)<=0:
                raise ValueError('Non-positive denominator.')
validate_panel(panel)
source_register = {r['source_id']: r for r in rows('source_verification.csv')}
for r in panel:
    check('source_register_coverage:'+r['case']+':'+r['project_id']+':'+r['cutoff'], all(r[k] in source_register for k in ('allocation_source_id','stage_source_id')))
check('complete_unique_admissible_panel',len(panel)==10 and len({r['project_id'] for r in panel})==5)

for label,modify in [
 ('unknown_stage_rejected',lambda x:x.__setitem__('full_operation',None)),
 ('missing_amount_rejected',lambda x:x.__setitem__('amount_million','')),
 ('unmatched_membership_rejected',lambda x:x.__setitem__('project_id','invented_subproject'))]:
    trial=[r.copy() for r in panel];modify(trial[0]);raised=False
    try: validate_panel(trial)
    except ValueError: raised=True
    check(label,raised)

summary=[];contributions=[];cutoff_rows=[];exact={}
for case in ('SSE','WEC'):
    ps=[r for r in panel if r['case']==case];dates=sorted({r['cutoff'] for r in ps});t0,t1=dates
    bydate={d:{r['project_id']:r for r in ps if r['cutoff']==d} for d in dates}
    totals={d:sum(frac(r['amount_million']) for r in bydate[d].values()) for d in dates}
    shares={d:sum(frac(r['amount_million'])*r['full_operation'] for r in bydate[d].values())/totals[d] for d in dates}
    for d in dates:
        check('weights_sum_one:'+case+':'+d,sum(frac(r['amount_million'])/totals[d] for r in bydate[d].values())==1)
        cutoff_rows.append(dict(case=case,cutoff=d,currency=ps[0]['currency'],allocation_million=number(totals[d]),fully_operating_allocation_million=number(shares[d]*totals[d]),full_operation_share_pct=number(100*shares[d]),project_entries=len(bydate[d])))
        for r in bydate[d].values():
            r['total_allocation_million']=number(totals[d]);r['weight']=number(frac(r['amount_million'])/totals[d]);r['weight_exact']=str(frac(r['amount_million'])/totals[d])
    stage=Fraction(0);weight=Fraction(0)
    for project in sorted(bydate[t0]):
        a,b=bydate[t0][project],bydate[t1][project]
        w0,w1=frac(a['amount_million'])/totals[t0],frac(b['amount_million'])/totals[t1]
        o0,o1=a['full_operation'],b['full_operation']
        s=(w0+w1)/2*(o1-o0);w=Fraction(o0+o1,2)*(w1-w0)
        diff=w1*o1-w0*o0
        check('exact_project_identity:'+case+':'+project,s+w==diff)
        reverse_s=(w1+w0)/2*(o0-o1);reverse_w=Fraction(o1+o0,2)*(w0-w1)
        check('independent_project_time_reversal:'+case+':'+project,reverse_s==-s and reverse_w==-w)
        # Average the two exact path orders: stage-then-weight and weight-then-stage.
        check('path_order_symmetry:'+case+':'+project,s==(w0*(o1-o0)+w1*(o1-o0))/2 and w==(o1*(w1-w0)+o0*(w1-w0))/2)
        stage+=s;weight+=w
        contributions.append(dict(case=case,project_id=project,start_date=t0,end_date=t1,start_amount_million=a['amount_million'],end_amount_million=b['amount_million'],start_weight_pct=number(100*w0),end_weight_pct=number(100*w1),start_full_operation=o0,end_full_operation=o1,stage_component_pp=number(100*s),weight_component_pp=number(100*w),total_change_pp=number(100*diff),stage_component_exact=str(s),weight_component_exact=str(w),reconciliation_residual_exact=str(s+w-diff),source_ids=';'.join(sorted({a['allocation_source_id'],b['allocation_source_id'],a['stage_source_id'],b['stage_source_id']}))))
    delta=shares[t1]-shares[t0]
    check('exact_case_identity:'+case,stage+weight==delta)
    check('time_reversal_symmetry:'+case,-stage-weight==shares[t0]-shares[t1])
    summary.append(dict(case=case,instrument=ps[0]['instrument'],start_date=t0,end_date=t1,currency=ps[0]['currency'],start_allocation_million=number(totals[t0]),end_allocation_million=number(totals[t1]),start_share_pct=number(100*shares[t0]),end_share_pct=number(100*shares[t1]),stage_component_pp=number(100*stage),weight_component_pp=number(100*weight),total_change_pp=number(100*delta),reconciliation_residual_pp='0',source_ids=';'.join(sorted({r['allocation_source_id'] for r in ps}|{r['stage_source_id'] for r in ps}))))
    exact[case]=dict(start_share=str(shares[t0]),end_share=str(shares[t1]),stage_component=str(stage),weight_component=str(weight),total_change=str(delta),residual='0')
    if case=='SSE':
        check('sse_same_project_amounts_both_dates',all(frac(bydate[t0][p]['amount_million'])==frac(bydate[t1][p]['amount_million']) for p in bydate[t0]))
        check('sse_total_543_9_both_dates',all(x==frac('543.9') for x in totals.values()))
        check('sse_weight_component_exact_zero',weight==0)
    else:
        check('wec_totals_match_source',totals[t0]==frac('281.7') and totals[t1]==frac('440.5'))
        check('wec_weight_component_negative',weight<0)
        check('paris_no_artificial_subweights',set(bydate[t0])=={'Badger_Hollow_II','Paris_Solar_Battery'})
        for r in rows('wec_project_stage_panel.csv'):
            check('wec_stored_denominator:'+r['source_csv_row'],frac(r['total_allocated_usd_million'])==totals[r['allocation_cutoff']])

# Published figure shares must be reproduced without changing the original figure.
for r in rows('baseline_figure_3_plot_data.csv'):
    s=next(x for x in cutoff_rows if x['case']==r['issuer'] and x['cutoff']==r['cutoff'])
    check('baseline_figure3_share:'+r['issuer']+':'+r['cutoff'],abs(Decimal(s['full_operation_share_pct'])-Decimal(r['full_operation_share_pct']))<Decimal('0.000000000001'))
    check('baseline_figure3_denominator:'+r['issuer']+':'+r['cutoff'],frac(s['allocation_million'])==frac(r['allocated_million']))

panel=sorted(panel,key=lambda r:(r['case'],r['cutoff'],r['project_id']))
write_csv('project_cutoff_inputs.csv',panel)
write_csv('stage_weight_decomposition.csv',summary)
si_table=[]
for r in summary:
    source_location=('SSE 2023/2024 Green Bond Reports, Table 6, PDF p10 (GB5 only)' if r['case']=='SSE' else 'WEPCO 2023/2024 assertions, p1; PSC 5-UR-111, p70; 2024 Form 10-K, p7')
    si_table.append(dict(case=r['case'],cutoffs=r['start_date']+' to '+r['end_date'],start_share_pct=f"{Decimal(r['start_share_pct']):.6f}",end_share_pct=f"{Decimal(r['end_share_pct']):.6f}",stage_component_pp=f"{Decimal(r['stage_component_pp']):.6f}",weight_component_pp=f"{Decimal(r['weight_component_pp']):.6f}",total_change_pp=f"{Decimal(r['total_change_pp']):.6f}",source_locator=source_location))
write_csv('stage_weight_si_table.csv',si_table)
write_csv('project_contributions.csv',contributions)
write_csv('recomputed_cutoff_shares.csv',cutoff_rows)
write_csv('validation_checks.csv',CHECKS)
(OUT/'exact_fraction_results.json').write_text(json.dumps(exact,indent=2)+'\n')
manifest=dict(status='PASS',method='Symmetric exact accounting identity using Fraction; no rounding until presentation',primary_source_review='See inputs/source_verification.csv; executing this script does not independently reverify source meaning',unknown_handling='Missing stages, missing amounts and unmatched project membership stop execution; no zero imputation',inputs_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(INP.iterdir()) if p.is_file()},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checks_passed=len(CHECKS),case_exact_reconciliation={case:x['residual'] for case,x in exact.items()},outputs_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='validation_and_provenance.json'})
(OUT/'validation_and_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2));print(f'PASS: {len(CHECKS)} checks; exact reconciliation residual zero for both cases.')
