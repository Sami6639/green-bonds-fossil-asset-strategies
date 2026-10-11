#!/usr/bin/env python3
"""Rebuild three manuscript figures from the selected-result snapshot.

No MW, currencies, or groups are pooled. Direction counts are unweighted.
The SSE project-level extract is archived with this script; all other inputs
are read from the current integrated results and WEC source-derived panel.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, unicodedata, os
from datetime import datetime, timezone
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR','/tmp/bse-global-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/bse-global-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

HERE = Path(__file__).resolve().parent
PARSER = argparse.ArgumentParser()
PARSER.add_argument('--results', type=Path, default=HERE.parent/'analysis_panel/results')
PARSER.add_argument('--wec-panel', type=Path, default=HERE/'source_data/wec_project_stage_panel.csv')
PARSER.add_argument('--out', type=Path, default=HERE)
ARGS = PARSER.parse_args()
OUT = ARGS.out.resolve(); OUT.mkdir(parents=True, exist_ok=True)

BLUE='#176B85'; ORANGE='#B76B2C'; GRAY='#8B9299'; LIGHT='#E8ECF0'; INK='#25313B'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':INK,
 'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':'#8D969E',
 'axes.linewidth':0.6,'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})

SCOPE = {
 'aes_corporation':'Equity', 'ameren':'Owned nameplate',
 'american_electric_power':'Owned nameplate', 'cfe':'Owned effective',
 'clp':'Equity', 'colbun_s_a':'Gross consolidated',
 'constellation_energy':'Proportionate net', 'dte_energy':'DTE Electric owned',
 'duke_energy':'Regulated owned', 'edf':'Ownership share',
 'edp':'Controlling stakes', 'eletrobras':'Consolidated + SPE',
 'enbw':'Operational control', 'enel':'Financially consol.',
 'engie':'Gross', 'esb':'Coal + gas subset',
 'genesis_energy_limited':'Owned / operated', 'global_power_synergy_gpsc':'Equity',
 'iberdrola':'Consolidated coal + gas', 'j_power_electric_power_development':'Parent coal-capable',
 'jsw_energy':'Group installed', 'kansai_electric_power':'Own thermal aggregate',
 'naturgy':'Fossil-fuel subset', 'nextera_energy':'Owned net',
 'ontario_power_generation':'Proportionate in service', 'pampa_energ_a':'Gross operated',
 'ratch_group':'Operating equity', 'rwe':'IFRS-consolidated',
 'shikoku_electric_power':'Own company', 'sse':'Gas / oil incl. PPA',
 'statkraft':'Gas-only subset', 'taipower':'Owned',
 'tohoku_electric_power':'Thermal aggregate', 'vattenfall':'Non-pro-rata',
 'wec_energy_group':'Owned nameplate',
 'china_huaneng':'Group thermal proxy', 'chn_energy':'Group thermal proxy',
}
SHORT = {'american_electric_power':'American Electric Power',
 'j_power_electric_power_development':'J-POWER',
 'global_power_synergy_gpsc':'Global Power Synergy',
 'genesis_energy_limited':'Genesis Energy',
 'ontario_power_generation':'Ontario Power Generation'}
INPUTS={}
def manifest_key(path):
 return Path(os.path.relpath(Path(path).resolve(), OUT)).as_posix()
def read(path):
 path=Path(path); blob=path.read_bytes()
 INPUTS[manifest_key(path)]={'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob)}
 return pd.read_csv(path)
def bools(s): return s.astype(str).str.lower().eq('true')
def key(s): return unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
def save(fig, stem):
 fig.canvas.draw()
 renderer=fig.canvas.get_renderer(); w,h=fig.canvas.get_width_height()
 for artist in fig.findobj(match=Text):
  if artist.get_visible() and artist.get_text().strip():
   box=artist.get_window_extent(renderer)
   assert box.x0>=-1 and box.y0>=-1 and box.x1<=w+1 and box.y1<=h+1, \
      f'Text outside figure in {stem}: {artist.get_text()!r}, {box.bounds}, canvas {(w,h)}'
 for ext in ('png','pdf'):
  fig.savefig(OUT/(stem+'.'+ext),dpi=300,facecolor='white')
 sizes[stem]={'width_inches':fig.get_figwidth(),'height_inches':fig.get_figheight(),
              'png_dpi':300,'suggested_docx_width_inches':6.4}
 plt.close(fig)
def direction(opening,delta,band):
 if pd.isna(opening) or pd.isna(delta): return 'unresolved'
 if abs(delta)<=abs(opening)*band/100+1e-9: return 'within_declared_band'
 return 'increase' if delta>0 else 'decrease'

sizes={}; figures=[]; qa={}
results_manifest_path=ARGS.results/'results_build_manifest.json'
results_manifest=json.loads(results_manifest_path.read_text())
INPUTS[manifest_key(results_manifest_path)]={'sha256':hashlib.sha256(results_manifest_path.read_bytes()).hexdigest(),
                                  'bytes':results_manifest_path.stat().st_size}
g=read(ARGS.results/'group_capacity_results.csv')
tier_col=next((col for col in ['analysis_evidence_tier','evidence_tier'] if col in g),None)
assert tier_col, 'Final authoritative evidence-tier field is required; admitted alone is not a valid final-cohort filter.'
PRINCIPAL='principal_fuel_identified_scope'; PROXY='matched_thermal_proxy_extension'
g=g.loc[g[tier_col].isin([PRINCIPAL,PROXY])].copy()
g['principal_scope']=g[tier_col].eq(PRINCIPAL)
principal_n=int(g.principal_scope.sum()); proxy_n=int((~g.principal_scope).sum())
assert not g['group_id'].duplicated().any(), 'One selected window per group required.'
assert len(g)>0
assert (pd.to_datetime(g.end_date)>pd.to_datetime(g.start_date)).all()
assert ((pd.to_datetime(g.end_date)-pd.to_datetime(g.start_date)).dt.days==g.duration_days).all()
missing_scopes=set(g.group_id)-set(SCOPE)
assert not missing_scopes, f'New groups need source-reviewed display-scope labels: {missing_scopes}'
g['display_label']=[SHORT.get(r.group_id,r.issuer_label) for r in g.itertuples()]
g['display_scope']=g.group_id.map(SCOPE)
g=g.assign(_sort=g.display_label.map(key)).sort_values('_sort').drop(columns='_sort').reset_index(drop=True)
g['strict_storage_excluded']=g.renewable_boundary.eq('strict_storage_excluded')
g['fuel_identified']=bools(g.fuel_identified_sensitivity_eligible)
assert (g.fuel_identified==g.principal_scope).all(), 'Tier and fuel-identification fields disagree.'
assert g.loc[g.strict_storage_excluded,'strict_RE_start_mw'].notna().all()
g.to_csv(OUT/'figure_1_plot_data.csv',index=False)

# 1. Direction matrix: alphabetic ordering deliberately avoids ranking.
n=len(g); height=max(6.2, n*.168+1.48)
fig=plt.figure(figsize=(6.5,height)); ax=fig.add_axes([.025,.13,.95,.845])
ax.set_xlim(0,1);ax.set_ylim(n+.4,-1.8);ax.axis('off')
xs={'issuer':.0,'window':.354,'scope':.548,'fossil':.875,'re':.974}
for x,label,ha in [(xs['issuer'],'Utility group','left'),(xs['window'],'Window','left'),
                  (xs['scope'],'Scope / basis¹','left'),(xs['fossil'],'Fossil²','center'),
                  (xs['re'],'RE³','center')]:
 ax.text(x,-1.18,label,weight='bold',ha=ha,va='center',fontsize=9)
ax.axhline(-.56,color=INK,lw=.8)
for y,r in g.iterrows():
 if y%2==0: ax.axhspan(y-.47,y+.47,color='#F3F5F7',lw=0,zorder=0)
 ax.text(xs['issuer'],y,r.display_label,va='center',fontsize=8.55)
 start=pd.to_datetime(r.start_date);end=pd.to_datetime(r.end_date)
 ax.text(xs['window'],y,f'{start:%b %y}–{end:%b %y}',va='center',fontsize=8.2)
 ax.text(xs['scope'],y,r.display_scope,va='center',fontsize=7.65)
 for col,dx,filled in [('fossil',r.fossil_direction,r.fuel_identified),('re',r.renewable_direction,r.strict_storage_excluded)]:
  mark,colr={'increase':('^',BLUE),'decrease':('v',ORANGE),
      'unchanged_at_reported_precision':('o',GRAY),'unresolved':('x',GRAY)}.get(dx,('x',GRAY))
  ax.plot(xs[col],y,marker=mark,ms=6.9,markeredgewidth=1.15,
     markerfacecolor=colr if filled else 'white',markeredgecolor=colr,color=colr,ls='none')
ax.axhline(n-.48,color=INK,lw=.6)
handles=[Line2D([0],[0],marker='^',ls='',color=BLUE,label='Increase',ms=6),
 Line2D([0],[0],marker='v',ls='',color=ORANGE,label='Decrease',ms=6),
 Line2D([0],[0],marker='o',ls='',color=GRAY,label='Unchanged',ms=6),
 Line2D([0],[0],marker='x',ls='',color=GRAY,label='Unresolved',ms=6)]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.066),ncol=4,
           frameon=False,columnspacing=1.2,handletextpad=.35,fontsize=8.4)
fig.text(.028,.047,'Hollow fossil = unresolved fuel mix; hollow RE = broader / unverified boundary.',fontsize=8.05)
fig.text(.028,.025,'Solid RE = storage excluded. Filled fossil retains identified fuels / source categories.',fontsize=8.05)
fig.text(.028,.004,f'{principal_n} principal + {proxy_n} proxy-extension groups · Unequal periods and reporting scopes',fontsize=8.05)
save(fig,'Figure_1_Global_Capacity_Directions')
figures.append({'number':1,'stem':'Figure_1_Global_Capacity_Directions',
 'caption':f'Figure 1. Source-defined capacity directions across {n} utility-group windows: {principal_n} principal fuel-identified scopes and {proxy_n} financing-matched thermal-proxy extensions. Groups are ordered alphabetically. Triangles indicate increases or decreases; circles denote no change at reported precision, and crosses identify unresolved single-boundary comparisons. Dates are month-end cutoffs. ¹ Scope and basis labels are abbreviated; complete ownership, technology and operating-scope qualifications are retained in source-linked figure data and supplementary tables. ² Filled fossil symbols represent principal source-defined fossil series or identified component subsets; hollow symbols identify unresolved thermal-proxy mixtures, which are excluded from principal fossil counts. Filled symbols do not certify an exhaustive active-plant census. Iberdrola retains coal plus gas, excluding unspecified cogeneration; J-POWER and Statkraft show coal-capable and gas-only components, respectively. ³ Filled RE symbols identify storage-excluded renewables; hollow symbols retain broader, storage-inclusive or insufficiently verified reported categories. The storage-exclusion check does not establish a pure-fossil comparator. Period lengths, reporting boundaries and financing timing differ, so arrows are unweighted within-group descriptions, not comparable rates, pooled MW totals, causal effects or performance ranks.'})

# 2. Recalculate sign-band pair counts, and check supplied directions for two boundaries.
b=read(ARGS.results/'group_sign_band_sensitivity.csv')
b=b.loc[b.group_id.isin(g.group_id)].copy()
assert not b.duplicated(['group_id','boundary','band_pct_of_opening_capacity']).any()
ws=read(ARGS.results/'clean_wind_solar_sensitivity.csv')
ws=ws.loc[bools(ws.available)&ws.group_id.isin(g.loc[g.principal_scope,'group_id'])].merge(
 g[['group_id','fossil_start_mw','fossil_delta_mw']],on='group_id',validate='one_to_one')
rows=[]
for row in b.itertuples():
 rd=direction(row.RE_opening_mw,row.RE_delta_mw,row.band_pct_of_opening_capacity)
 fd=direction(row.fossil_opening_mw,row.fossil_delta_mw,row.band_pct_of_opening_capacity)
 assert rd==row.RE_direction_at_band and fd==row.fossil_direction_at_band
 rows.append({'group_id':row.group_id,'boundary':row.boundary,'band':row.band_pct_of_opening_capacity,'RE_direction':rd,'fossil_direction':fd})
for row in ws.itertuples():
 for band in (0,.5,1):
  rows.append({'group_id':row.group_id,'boundary':'clean_wind_solar_components','band':band,
   'RE_direction':direction(row.wind_solar_start_mw,row.wind_solar_delta_mw,band),
   'fossil_direction':direction(row.fossil_start_mw,row.fossil_delta_mw,band)})
detail=pd.DataFrame(rows)
detail=detail.loc[detail.boundary.ne('strict_storage_excluded_subset')|detail.group_id.isin(g.loc[g.principal_scope,'group_id'])]
fuel=detail[(detail.boundary=='reported_source_boundary')&detail.group_id.isin(g.loc[g.fuel_identified,'group_id'])].copy()
fuel['boundary']='fuel_identified_comparator_subset'
detail=pd.concat([detail,fuel],ignore_index=True)
detail['paired_available']=detail.RE_direction.ne('unresolved')&detail.fossil_direction.ne('unresolved')
def pair_class(r):
 if not r.paired_available:return 'not_available'
 if r.RE_direction=='increase':return {'decrease':'re_up_fossil_down','within_declared_band':'re_up_fossil_band','increase':'re_up_fossil_up'}[r.fossil_direction]
 return 'other_pair'
detail['pair_class']=detail.apply(pair_class,axis=1)
detail.to_csv(OUT/'figure_2_group_band_data.csv',index=False)
classes=['re_up_fossil_down','re_up_fossil_band','re_up_fossil_up','other_pair']
colors=[BLUE,'#78AABB',ORANGE,'#AAB1B7'];hatches=['','//','\\\\','..']
boundaries=[('fuel_identified_comparator_subset','A','Principal fuel-identified scopes'),
 ('reported_source_boundary','B','Broader series including thermal proxies'),
 ('strict_storage_excluded_subset','C','Principal scopes: storage-excluded RE'),
 ('clean_wind_solar_components','D','Principal scopes: wind + solar')]
counts=[];denoms={}
for boundary,_,_ in boundaries:
 for band in (0,.5,1):
  dd=detail[(detail.boundary==boundary)&(detail.band==band)&detail.paired_available]
  assert not dd.group_id.duplicated().any()
  denoms[(boundary,band)]=len(dd)
  for cl in classes:counts.append({'boundary':boundary,'band_pct_of_opening_capacity':band,
     'pair_class':cl,'groups':int(dd.pair_class.eq(cl).sum()),'paired_denominator':len(dd),
     'eligible_cohort_group_denominator':n if boundary=='reported_source_boundary' else principal_n,
     'broader_group_denominator':n,'group_ids':';'.join(dd.loc[dd.pair_class.eq(cl),'group_id'])})
count=pd.DataFrame(counts);count.to_csv(OUT/'figure_2_counts.csv',index=False)
for (boundary,band),dd in count.groupby(['boundary','band_pct_of_opening_capacity']):
 assert dd.groups.sum()==dd.paired_denominator.iloc[0]
fig,axes=plt.subplots(4,1,figsize=(6.5,7.1));fig.subplots_adjust(left=.11,right=.93,top=.95,bottom=.175,hspace=.67)
for ax,(boundary,letter,label) in zip(axes,boundaries):
 denom=denoms[(boundary,0)];assert all(denoms[(boundary,v)]==denom for v in (0,.5,1))
 ax.text(-.092,1.16,letter,transform=ax.transAxes,weight='bold',fontsize=10)
 cohort_n=n if boundary=='reported_source_boundary' else principal_n
 ax.text(0,1.16,f'{label}  (n = {denom}/{cohort_n})',transform=ax.transAxes,weight='bold',fontsize=9.2)
 for y,band in enumerate((0,.5,1)):
  left=0
  for cl,color,hatch in zip(classes,colors,hatches):
   val=int(count.loc[(count.boundary==boundary)&(count.band_pct_of_opening_capacity==band)&(count.pair_class==cl),'groups'].iloc[0])
   if val:
    ax.barh(y,val,left=left,height=.62,color=color,edgecolor='white',lw=.7,hatch=hatch)
    ax.text(left+val/2,y,str(val),ha='center',va='center',fontsize=9,
            color='white' if cl in ('re_up_fossil_down','re_up_fossil_up') else INK,weight='bold',
            bbox={'facecolor':color,'edgecolor':'none','pad':.25})
   left+=val
  ax.text(denom*1.014,y,f'{denom}',va='center',fontsize=8.6)
 ax.set_ylim(2.6,-.6);ax.set_xlim(0,max(denom,1)*1.06)
 ax.set_yticks([0,1,2],['0%','0.5%','1%']);ax.tick_params(axis='y',length=0,pad=6)
 ax.set_xticks([]);ax.set_xlabel('')
 for spine in ax.spines.values():spine.set_visible(False)
labels=['RE ↑ / fossil ↓','RE ↑ / fossil within band','RE ↑ / fossil ↑','Other resolved pairs']
fig.legend([Patch(facecolor=c,edgecolor='white',hatch=h) for c,h in zip(colors,hatches)],labels,
 loc='lower center',bbox_to_anchor=(.5,.066),ncol=2,frameon=False,fontsize=8.5,
 handlelength=1.6,columnspacing=1.4)
fig.text(.06,.042,'Bars are normalized to their paired denominators; integers are group counts.',fontsize=8.2)
fig.text(.06,.025,'Bands are retrospective descriptions, not significance or policy thresholds.',fontsize=8.2)
save(fig,'Figure_2_Materiality_Sensitivity')
denomtext=', '.join(f'{label.lower()} n = {denoms[(boundary,0)]}' for boundary,_,label in boundaries)
figures.append({'number':2,'stem':'Figure_2_Materiality_Sensitivity',
 'caption':f'Figure 2. Descriptive sensitivity of paired capacity directions to retrospective materiality bands. Bars count utility groups at 0%, 0.5% and 1% of each series’ opening capacity; an absolute endpoint change less than or equal to the stated band is within band. At 0%, this denotes no change at source precision. Denominators require resolved same-window observations for both series: {denomtext}. Panel A draws from {principal_n} principal fuel-identified scopes; panel B includes all {n} broader matched groups, including thermal proxies. Panels C and D intersect the principal cohort with storage-excluded renewables and separately observed wind-plus-solar components, respectively; panel D is not a total-renewable measure. A clean renewable boundary does not re-admit unresolved thermal proxies into panels C or D. The fossil comparator remains source-defined and scope-qualified throughout. Each group contributes at most once per bar. “Other resolved pairs” includes all pairs without a renewable-series increase at the stated band. Missing or incompatible comparisons are excluded rather than treated as zero. Bar lengths are normalized to each paired denominator and integers display unweighted counts, not pooled capacity, population prevalence estimates, statistical tests or causal effects.'})

# 3. Source-linked financial-stock-weighted achieved full-operation shares.
sse=read(HERE/'source_data/sse_gb5_maturity_project_weights.csv')
milestones=read(HERE/'source_data/sse_actual_milestones.csv')
wec=read(ARGS.wec_panel)
assert set(sse.report_year)=={2023,2024}
assert not sse.duplicated(['project_id','report_year']).any()
assert set(sse[sse.report_year==2023].project_id)==set(sse[sse.report_year==2024].project_id)
assert sse.groupby('project_id').allocation_stock_gbp_m.nunique().eq(1).all()
assert sse.groupby('report_year').allocation_stock_gbp_m.sum().round(6).eq(543.9).all()
assert not wec.duplicated(['project_id','allocation_cutoff']).any()
stages=[]
for year,rr in sse.groupby('report_year'):
 cutoff=pd.Timestamp(f'{year}-03-31')
 # Achieved milestones, not forecasts; a month-level completion must be earlier than cutoff.
 full={}
 for pid in rr.project_id:
  event=milestones.loc[(milestones.project_id==pid)&milestones.event_type.eq('full_operation')]
  assert len(event)==1
  eventdate=pd.to_datetime(event.event_date.iloc[0])
  full[pid]=bool(eventdate<=cutoff)
 assert all((r.maturity_class=='Full operation')==full[r.project_id] for r in rr.itertuples())
 total=rr.allocation_stock_gbp_m.sum();num=sum(r.allocation_stock_gbp_m for r in rr.itertuples() if full[r.project_id])
 stages.append({'issuer':'SSE','instrument':'GB5','cutoff':str(cutoff.date()),'currency':'GBP',
 'allocated_million':total,'fully_operating_allocated_million':num,'full_operation_share_pct':100*num/total,
 'reporting_entries':len(rr),'weighting':'Unchanged project allocations at both cutoffs',
 'source_urls':';'.join(sorted(set(rr.source_url)|set(rr.status_source_url)|set(milestones.loc[milestones.event_type.eq('full_operation'),'source_url'])))})
for cutoff,rr in wec.groupby('allocation_cutoff'):
 assert rr.total_allocated_usd_million.nunique()==1
 total=rr.allocated_usd_million.sum()
 assert np.isclose(total,rr.total_allocated_usd_million.iloc[0])
 assert np.isclose(rr.allocation_weight.sum(),1)
 assert rr.fully_operating_indicator.isin([0,1]).all()
 assert np.allclose(rr.allocation_weight,rr.allocated_usd_million/total)
 num=(rr.allocated_usd_million*rr.fully_operating_indicator).sum()
 stages.append({'issuer':'WEC','instrument':'WEPCO 4.75% due 2032','cutoff':cutoff,'currency':'USD',
 'allocated_million':total,'fully_operating_allocated_million':num,'full_operation_share_pct':100*num/total,
 'reporting_entries':len(rr),'weighting':'Cutoff-specific project allocations; weights change',
 'source_urls':';'.join(sorted(set(rr.allocation_source_url)|set(rr.stage_source_url)))})
stage=pd.DataFrame(stages)
assert stage.full_operation_share_pct.between(0,100).all()
stage.to_csv(OUT/'figure_3_plot_data.csv',index=False)
fig,axes=plt.subplots(2,1,figsize=(6.5,4.9));fig.subplots_adjust(left=.25,right=.965,top=.90,bottom=.26,hspace=1.00)
for ax,issuer,letter in zip(axes,['SSE','WEC'],['A','B']):
 rr=stage[stage.issuer.eq(issuer)].sort_values('cutoff')
 label='SSE · GB5 · 3 projects' if issuer=='SSE' else 'WEC · WEPCO bond · 2 reporting entries'
 ax.text(-.29,1.19,letter,transform=ax.transAxes,weight='bold',fontsize=10)
 ax.text(0,1.19,label,transform=ax.transAxes,weight='bold',fontsize=9.6)
 ylabels=[]
 for y,r in enumerate(rr.itertuples()):
  value=r.full_operation_share_pct
  ax.barh(y,100,height=.5,color=LIGHT,edgecolor='white')
  ax.barh(y,value,height=.5,color=BLUE,edgecolor='white')
  ax.plot(value,y,marker='|',color=BLUE,ms=22,mew=1.1)
  ax.text(value+1.8,y,f'{value:.2f}%',ha='left',va='center',fontsize=10,weight='bold',color=INK)
  sym='£' if r.currency=='GBP' else '$'
  ylabels.append(f'{pd.Timestamp(r.cutoff):%d %b %Y}\n{sym}{r.allocated_million:,.1f}m allocated')
 ax.set_xlim(0,100);ax.set_ylim(1.55,-.55)
 ax.set_yticks([0,1],ylabels);ax.tick_params(axis='y',length=0,pad=10,labelsize=8.8)
 ax.set_xticks([0,25,50,75,100],['0','25','50','75','100']);ax.tick_params(axis='x',length=3,labelsize=8.4)
 ax.grid(axis='x',color='#D3D9DE',lw=.6,zorder=0);ax.set_axisbelow(True)
 for spine in ['top','right','left']:ax.spines[spine].set_visible(False)
 ax.text(0,-.29,'Fixed allocation amounts and weights' if issuer=='SSE' else 'Cutoff-specific allocation amounts and weights',
         transform=ax.transAxes,fontsize=8.3,color='#5B6670')
fig.text(.58,.13,'Allocated financial stock associated with full operation (%)',ha='center',fontsize=9)
fig.legend([Patch(facecolor=BLUE),Patch(facecolor=LIGHT)],['Full operation achieved','Full operation not yet achieved'],
 loc='lower center',bbox_to_anchor=(.5,.055),ncol=2,frameon=False,fontsize=8.5)
fig.text(.04,.025,'A zero stage indicator does not mean zero production or no implementation progress.',fontsize=8.2)
save(fig,'Figure_3_Allocation_Associated_Operation')
figures.append({'number':3,'stem':'Figure_3_Allocation_Associated_Operation',
 'caption':'Figure 3. Allocated financial stock associated with achieved full operation at exact reporting cutoffs. Each percentage equals the sum of allocated financial amounts attached to reporting entries that had achieved full operation by the cutoff, divided by the instrument’s allocated financial stock at that cutoff. Panel A retains the same three SSE GB5 projects and £543.9 million allocation stock at 31 March 2023 and 31 March 2024: the full-operation share increases from 6.84% to 69.48% as Seagreen reaches full operation. Allocation amounts and weights remain fixed; the increase is not a new annual financing flow. Panel B uses the two persistent reporting entries of Wisconsin Electric Power Company’s September 2022 green bond, within WEC Energy Group. Allocated stock rises from $281.7 million at 30 June 2023 to $440.5 million at 30 June 2024, with cutoff-specific weights; the full-operation share increases from 0.00% to 33.46% after Badger Hollow II enters service. Paris is a bundled solar-and-battery reporting entry. The not-yet-full-operation category can include construction, partial operation and generation; a zero indicator does not assert zero production. These are instrument-specific stage associations, not measured generation shares, avoided emissions, comparable project-performance scores or identified financing effects.'})

figures[0]['main_caption']=(f'Figure 1. Capacity directions for {principal_n} principal fuel-identified scopes and {proxy_n} financing-matched thermal-proxy extensions, ordered alphabetically. Triangles indicate increases or decreases; circles indicate unchanged capacity at source precision; crosses identify unresolved comparisons. Dates are month-end cutoffs and scope labels are abbreviated. Filled fossil symbols denote principal fuel-identified series or component subsets; hollow fossil symbols denote thermal proxies. Filled RE symbols denote storage-excluded renewables; hollow RE symbols denote broader or unverified categories. Iberdrola retains coal plus gas, ESB named coal and gas components, J-POWER coal-capable capacity, and Statkraft gas capacity. Directions describe source-specific windows, rather than comparable rates.')
figures[1]['main_caption']=(f'Figure 2. Paired capacity directions under retrospective bands of 0%, 0.5% and 1% of each series’ opening capacity. Absolute changes within or equal to the band are classified as within band; 0% denotes no change at source precision. Panels show resolved pairs for principal scopes (A, n = {denoms[("fuel_identified_comparator_subset",0)]}/{principal_n}), the broader proxy-inclusive sample (B, n = {denoms[("reported_source_boundary",0)]}/{n}), storage-excluded RE within principal scopes (C, n = {denoms[("strict_storage_excluded_subset",0)]}/{principal_n}), and wind plus solar within principal scopes (D, n = {denoms[("clean_wind_solar_components",0)]}/{principal_n}). Bars are normalized to paired denominators; integers are group counts. Other pairs lack a renewable-series increase. Missing comparisons are excluded; bands are descriptive, not significance thresholds.')
figures[2]['main_caption']=('Figure 3. Allocated financial stock associated with full operation at exact reporting cutoffs. Percentages weight achieved full-operation indicators by project-level allocations. SSE retains three GB5 projects and fixed £543.9 million allocation stock: the share rises from 6.84% to 69.48% between March 2023 and March 2024. WEC’s WEPCO bond retains two reporting entries with changing allocations and weights: allocated stock rises from $281.7 million to $440.5 million, and the full-operation share from 0.00% to 33.46%, between June 2023 and June 2024. Paris combines solar and battery assets. A zero stage indicator does not imply zero generation; these shares do not measure financing effects.')

qa.update({'broader_matched_groups':n,'principal_fuel_identified_groups':principal_n,'matched_thermal_proxy_groups':proxy_n,
 'source_precision_directions':g.groupby(['renewable_direction','fossil_direction']).size().to_dict().__str__(),
 'storage_excluded_RE_groups':int(g.strict_storage_excluded.sum()),
 'paired_denominators':{k:denoms[(k,0)] for k,_,_ in boundaries},
 'one_row_per_selected_group':True,'sign_bands_recomputed_and_match':True,
 'counts_reconcile_to_denominators':True,'stage_shares_recomputed':True,
 'sse_milestones_match_classification':True,'no_pooled_mw':True,
 'no_image_titles':True,'all_visible_text_inside_image_bounds':True,'automatic_checks_passed':True,
 'visual_QA':'Pending human-readable rendered image inspection; see visual_qa.json when complete.'})
manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'generator':'build_manuscript_figures.py',
 'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'upstream_results_created_utc':results_manifest['created_utc'],
 'inputs':INPUTS,'figure_dimensions':sizes,'figures':figures,'qa':qa,
 'reproduce':'python build_manuscript_figures.py --results ../analysis_panel/results --wec-panel source_data/wec_project_stage_panel.csv',
 'redistribution':'Only author-generated figures and source-derived structured data. Corporate source PDFs are not redistributed.'}
(OUT/'figure_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
(OUT/'figure_captions.txt').write_text('\n\n'.join(f['caption'] for f in figures)+'\n')
(OUT/'figure_main_captions.txt').write_text('\n\n'.join(f['main_caption'] for f in figures)+'\n')
(OUT/'figure_provenance_manifest.json').write_text(json.dumps(INPUTS,indent=2))
(OUT/'figure_validation.json').write_text(json.dumps(qa,indent=2))
print(json.dumps({'figures':[f['stem'] for f in figures],'qa':qa},indent=2))
