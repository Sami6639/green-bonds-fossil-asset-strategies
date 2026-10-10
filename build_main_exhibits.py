"""Rebuild bounded descriptive exhibits from extracted, source-linked CSVs. No network."""
from pathlib import Path
import os,csv,json,hashlib,calendar,datetime
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-utility')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/utility-cache')
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).parent; O=P/'main_exhibits'; O.mkdir(exist_ok=True)
def read(s): return pd.read_csv(P/s,keep_default_na=False)
def save(df,n):df.to_csv(O/n,index=False)
plt.rcParams.update({'svg.hashsalt':'utility-review-20261010','font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':200})
# Within-case endpoint bridges; positive and negative contributions retain mechanism.
ib=read('iberdrola/history_2019_2024/annual_capacity_bridges_2020_2024.csv');ib=ib[ib.technology=='Gas+Cogeneration+Coal']
ss=read('sse/capacity_2019_2024_event_contributions.csv');cl=read('clp/history_2019_2024/endpoint_coal_bridge_2019_2024.csv').iloc[0]
rows=[]
def b(issuer,scope,opening,closing,parts,path,warning):
 residual=closing-opening-sum(v for k,v in parts)
 for category,value in [('Opening stock',opening)]+parts+[('Residual',residual),('Closing stock',closing)]:rows.append(dict(issuer=issuer,scope=scope,period='2019 year-end to 2024 year-end' if issuer!='SSE' else 'FY2019 to FY2024 (31 March)',component=category,value_mw=value,source_table=path,warning=warning))
b('Iberdrola','Reported gas + cogeneration + coal',16864,9014,[('Physical closures',ib.physical_retirement.sum()),('Installed / commissioned',ib.physical_installation_completion.sum()+ib.commissioning.sum()),('Existing-asset acquisition / rights',ib.acquisition_existing_asset.sum()+ib.acquisition_or_operating_rights_existing_asset.sum()),('Ownership disposal',ib.divestment_ownership_transfer.sum()),('Uprating',ib.modernisation_uprating.sum())],'iberdrola/history_2019_2024/annual_capacity_bridges_2020_2024.csv','Consolidated plus proportional investees; installed pre-COD and lease-ambiguous assets included; cogeneration fuel unresolved; unidentified gross events not excluded.')
sums=ss.groupby('event_type').signed_reported_portfolio_mw.sum()
b('SSE','Reported Thermal portfolio',6765,6210,[('Physical closures',sums.get('physical_retirement',0)+sums.get('physical_closure',0)),('Commissioning',sums.get('physical_commissioning',0)),('Acquisition',sums.get('ownership_acquisition',0)),('Ownership disposal',sums.get('ownership_disposal',0)),('Reporting / segment changes',sums.get('reporting_scope_change',0)+sums.get('internal_segment_transfer',0))],'sse/capacity_2019_2024_event_contributions.csv','Includes multifuel in opening stock and disposal; segment boundary changes retained; no exhaustive gross event census.')
b('CLP','Equity coal; reserve-inclusive',cl.opening_mw,cl.closing_mw,[('Physical closures',cl.physical_closure_mw),('Ownership / contract exits',cl.ownership_or_contract_exit_mw),('Uprating',cl.uprating_mw)],'clp/history_2019_2024/endpoint_coal_bridge_2019_2024.csv','2024 closures include 245 equity MW in reserve from 2022; uprating date versus stock recognition mismatch retained; residual includes rounding.')
br=pd.DataFrame(rows);save(br,'appendix_capacity_bridge_components.csv')
fig,axes=plt.subplots(3,1,figsize=(12,11));colors={'Opening stock':'#385770','Closing stock':'#385770','Residual':'#9d659c'}
for ax,(issuer,g) in zip(axes,br.groupby('issuer',sort=False)):
 running=0
 for j,r in enumerate(g.itertuples()):
  endpoint=r.component in ('Opening stock','Closing stock');base=0 if endpoint else min(running,running+r.value_mw)
  h=r.value_mw if endpoint else abs(r.value_mw)
  ax.bar(j,h,bottom=base,color=colors.get(r.component,'#af6549' if r.value_mw<0 else '#47857a'),width=.7)
  if not endpoint and h==0: ax.plot([j-.3,j+.3],[running,running],color='#9d659c',lw=2)
  ax.text(j,base+h+max(g.value_mw)*.025,f'{r.value_mw:+,.0f}' if not endpoint else f'{r.value_mw:,.0f}',ha='center',fontsize=9)
  running=r.value_mw if endpoint else running+r.value_mw
 ax.set_xticks(range(len(g)),[x.replace(' / ',' /\n').replace('Existing-asset ','Existing-asset\n').replace('Reporting /','Reporting /\n') for x in g.component],fontsize=8)
 ax.set_ylabel('MW');ax.set_ylim(0,max(g.value_mw)*1.26);ax.set_title(issuer+' | '+g.scope.iloc[0],loc='left',fontweight='bold');ax.grid(axis='y',alpha=.15)
fig.suptitle('Capacity changes',x=.06,ha='left',fontsize=14)
# Scope note is provided separately for manuscript caption.
fig.tight_layout(rect=[0,.01,1,.96]);fig.savefig(O/'figure3_capacity_bridges.png');fig.savefig(O/'figure3_capacity_bridges.svg',metadata={'Date':None});plt.close(fig)
# Timeline rows carry date precision. Year/month intervals are drawn as ranges, never fabricated dates.
t=[]
def event(issuer,lane,date,label,url,loc,precision=None):t.append(dict(issuer=issuer,lane=lane,date=date,date_precision=precision or ('half_year' if '-H' in date else 'year_with_upper_bound' if ';' in date else 'day' if len(date)==10 else 'month' if len(date)==7 else 'year'),label=label,source_url=url,source_locator=loc))
a=read('iberdrola/history_2019_2024/prior_strategy_evidence.csv')
for r in a.itertuples():event('Iberdrola','Prior decisions',r.decision_date,r.decision_type.replace('_',' '),r.source_url,'PDF '+str(r.pdf_page_1_based))
a=read('iberdrola/history_2019_2024/matched_green_hybrid_2019_2024.csv');r=a.iloc[0];event('Iberdrola','Finance',r.issue_date,'€800m hybrid issued',r.issue_date_source_url,r.issue_date_source_locator)
# Retain the conflicting allocation inventory date without relabelling it as pricing.
for _field in ['issue_date_meaning','allocation_report_inventory_date','allocation_report_inventory_date_as_reported','allocation_report_inventory_date_meaning','allocation_report_inventory_date_source_url','allocation_report_inventory_date_source_locator','date_resolution']:
 t[-1][_field]=r[_field]
r=read('iberdrola/history_2019_2024/matched_project_delivery_evidence.csv').iloc[0];event('Iberdrola','Renewable delivery','2020','East Anglia ONE: actual COD year',r.source_url,'PDF 91')
a=read('iberdrola/history_2019_2024/fossil_capacity_event_ledger.csv')
for r in a.itertuples():
 if r.event_class in ('physical_retirement','divestment_ownership_transfer'):event('Iberdrola','Fossil events',r.event_date_reported,r.asset_or_project+': '+r.event_class.replace('_',' '),r.source_url,'PDF '+str(r.pdf_page_1_based))
a=read('sse/capacity_prior_decisions_and_dates.csv')
for r in a.itertuples():
 if r.event_type in ('proposed_closure','licence_required_closure_prior_disclosure'):event('SSE','Prior decisions',r.disclosure_or_event_date,r.asset+': prior closure disclosure',r.source_url,r.locator)
a=read('sse/fixed_cohort_actual_milestones.csv')
for r in a.itertuples():
 if r.event_type=='investment_decision':event('SSE','Prior decisions',r.event_date,r.project_id.replace('SSE_','').replace('_',' ')+': investment decision',r.source_url,'Decision date; source may be retrospective',r.date_precision)
r=read('sse/capacity_2019_2024_event_contributions.csv');r=r[r.asset=='Keadby2 CCGT'].iloc[0];event('SSE','Prior decisions','2018-08','Keadby 2: construction commenced',r.source_url,r.source_locator)
a=read('sse/fixed_cohort_bond_project_links.csv');r=a[a.bond_group=='GB5'].iloc[0];event('SSE','Finance',r.settlement_date,'GB5 issued (refinancing)',r.date_source,'Table 1')
a=read('sse/fixed_cohort_actual_milestones.csv')
for r in a.itertuples():
 if r.event_type=='full_operation':event('SSE','Renewable delivery',r.event_date,r.project_id.replace('SSE_','').replace('_',' ')+': actual full operation',r.source_url,'Dated issuer / partner announcement')
a=read('sse/capacity_2019_2024_event_contributions.csv')
for r in a.itertuples():
 if r.event_type in ('physical_retirement','ownership_acquisition'):event('SSE','Fossil events',r.event_date,r.asset+': '+r.event_type.replace('_',' '),r.source_url,r.source_locator)
tl=pd.DataFrame(t);save(tl,'figure1_timeline_source_rows.csv')
def date_range(s):
 if '; completed by' in s:return datetime.date(int(s[:4]),1,1),datetime.date.fromisoformat(s.split('by')[1])
 if s.endswith('-H1'):return datetime.date(int(s[:4]),1,1),datetime.date(int(s[:4]),6,30)
 if s.endswith('-H2'):return datetime.date(int(s[:4]),7,1),datetime.date(int(s[:4]),12,31)
 parts=list(map(int,s.split('-')));y=parts[0];m=parts[1] if len(parts)>1 else 1;d=parts[2] if len(parts)>2 else 1
 lo=datetime.date(y,m,d);hi=lo if len(parts)==3 else datetime.date(y,m,calendar.monthrange(y,m)[1]) if len(parts)==2 else datetime.date(y,12,31)
 return lo,hi
tl['plot_start']=[date_range(s)[0].isoformat() for s in tl.date]
tl['plot_end']=[date_range(s)[1].isoformat() for s in tl.date]
tl['plot_glyph']=['point' if a==b else 'interval_line' for a,b in zip(tl.plot_start,tl.plot_end)]
save(tl,'figure1_timeline_source_rows.csv')
# Print-width design: one event per row at 6.27 inches, rather than crowded swimlanes.
import matplotlib.dates as md
from matplotlib.lines import Line2D
import textwrap
fig,axes=plt.subplots(2,1,figsize=(6.27,8.1),gridspec_kw={'height_ratios':[8,13]})
lanes=['Prior decisions','Finance','Renewable delivery','Fossil events'];pal=['#7c668f','#356685','#3b8a74','#b3634a']
short={'VIKING: investment decision':'Viking: investment decision','GORDONBUSH EXT: investment decision':'Gordonbush Extension: investment decision','SEAGREEN1: investment decision':'Seagreen: investment decision','request for closure authorisation':'Coal closure authorisation requested','divestment MoU':'Mexico divestment MoU','sale purchase agreement':'Mexico sale agreement','East Anglia ONE: actual COD year':'East Anglia ONE: actual COD','Velilla 1 and 2: physical retirement':'Velilla 1 and 2: closure','Lada: physical retirement':'Lada: closure','Mexico CCGT portfolio: divestment ownership transfer':'Mexico gas portfolio: sale','Fiddlers Ferry: prior closure disclosure':'Fiddlers Ferry: closure proposed','Tarbert old oil station: prior closure disclosure':'Tarbert: prior closure disclosure','VIKING: actual full operation':'Viking: full operation','GORDONBUSH EXT: actual full operation':'Gordonbush Extension: full operation','SEAGREEN1: actual full operation':'Seagreen: full operation','Fiddlers Ferry remaining units: physical retirement':'Fiddlers Ferry: closure','Triton Saltend and Indian Queens: ownership acquisition':'Triton: ownership acquisition','Tarbert old oil station: physical retirement':'Tarbert: closure'}
for ax,issuer in zip(axes,['Iberdrola','SSE']):
 g=tl[tl.issuer==issuer].copy()
 # Keep category ordering; event records and reported date precision remain unchanged.
 labels=[]
 for i,r in enumerate(g.itertuples()):
  y=len(g)-1-i;lo,hi=date_range(r.date);c=pal[lanes.index(r.lane)]
  ax.axhline(y,color='#eeeeee',lw=.7,zorder=0)
  if lo!=hi:ax.plot([lo,hi],[y,y],color=c,lw=4,solid_capstyle='butt')
  else:ax.scatter([lo],[y],color=c,s=24,zorder=3)
  labels.append(textwrap.fill(short.get(r.label,r.label),29))
 ax.set_title(issuer,loc='left',fontweight='bold',fontsize=11,pad=10)
 ax.set_yticks(list(reversed(range(len(g)))),labels,fontsize=8)
 ax.tick_params(axis='y',length=0,pad=7)
 ax.set_ylim(-.6,len(g)-.4)
 ax.set_xlim(datetime.date(2017,1,1),datetime.date(2025,3,1))
 ax.xaxis.set_major_locator(md.YearLocator(2));ax.xaxis.set_major_formatter(md.DateFormatter('%Y'));ax.tick_params(axis='x',labelsize=9)
 ax.spines['left'].set_visible(False);ax.grid(axis='x',alpha=.15)
handles=[Line2D([0],[0],marker='o',lw=0,color=c,label=label,markersize=5) for c,label in zip(pal,lanes)]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.035),ncol=2,frameon=False,fontsize=9,columnspacing=1.8)
fig.subplots_adjust(left=.47,right=.98,top=.93,bottom=.12,hspace=.30)
fig.savefig(O/'figure1_selected_timelines.png');fig.savefig(O/'figure1_selected_timelines.svg',metadata={'Date':None});plt.close(fig)
# Allocation replacement by instrument vintage; identical currency stock movement.
r=read('enel/green_reallocations_2023.csv');save(r,'figure2_allocation_replacement_source_rows.csv');fig,ax=plt.subplots(figsize=(10,5))
for j,year in enumerate([2019,2018]):
 for k,kind in enumerate(['deconsolidated_removed','replacement_allocation']):
  sub=r[(r.issue_year==year)&(r.event==kind)];bottom=0;x=j*3+k
  for z,v in enumerate(sub.itertuples()):
   h=abs(v.allocation_change_EUR_m);ax.bar(x,h,bottom=bottom,color=['#48768c','#81a5ae','#a8c6c8'][z]);ax.text(x,bottom+h/2,(f'{v.project} {h:.2f}' if h<15 else f'{v.project}\n{h:.2f}'),ha='center',va='center',fontsize=7 if h<15 else 9);bottom+=h
  ax.text(x,bottom+3,f'€{bottom:.2f}m',ha='center')
ax.set_xticks([0,1,3,4],['2019 focal issue\nRemoved','2019 focal issue\nReassigned','2018 companion\nRemoved','2018 companion\nReassigned']);ax.set_ylabel('EUR million, allocation stock');ax.set_ylim(0,195);ax.grid(axis='y',alpha=.15)
fig.tight_layout();fig.savefig(O/'figure2_allocation_replacement.png');fig.savefig(O/'figure2_allocation_replacement.svg',metadata={'Date':None});plt.close(fig)
checks=[]
for issuer,g in br.groupby('issuer'):
 n=g.value_mw.iloc[0]+g.value_mw.iloc[1:-1].sum()-g.value_mw.iloc[-1];checks.append(dict(check=issuer+'_bridge_identity',difference=float(n),status='PASS' if abs(n)<1e-8 else 'FAIL'))
for year,g in r.groupby('issue_year'):checks.append(dict(check=f'Enel_{year}_allocation_balance',difference=float(g.allocation_change_EUR_m.sum()),status='PASS' if abs(g.allocation_change_EUR_m.sum())<.011 else 'FAIL'))
save(pd.DataFrame(checks),'validation_checks.csv')
print(pd.DataFrame(checks).to_string(index=False))
