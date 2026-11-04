#!/usr/bin/env python3
"""VK plots from vk_plot_data.xlsx (all + filtered) or two_figures_plot_data.xlsx (filtered only)."""
from pathlib import Path
import argparse,re,json
import numpy as np
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
p=argparse.ArgumentParser();p.add_argument('--data',type=Path);p.add_argument('--font',type=Path);p.add_argument('--latin-font',type=Path);p.add_argument('--preview',action='store_true');p.add_argument('--out',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parent
data=a.data or next((x for x in [root/'vk_plot_data.xlsx',root/'two_figures_plot_data.xlsx'] if x.exists()),root/'vk_plot_data.xlsx')
out=a.out or root/('preview_vk' if a.preview else 'figures_vk');out.mkdir(parents=True,exist_ok=True)
cnfile=a.font or root/'fonts/simsun.ttc';enfile=a.latin_font or root/'fonts/times.ttf'
if cnfile.exists() and enfile.exists():
 for f in [cnfile,enfile]:font_manager.fontManager.addfont(str(f))
 cn=font_manager.FontProperties(fname=str(cnfile)).get_name();en=font_manager.FontProperties(fname=str(enfile)).get_name()
 if cn.lower() not in ['simsun','宋体'] or en.lower()!='times new roman':p.error('Please supply SimSun and Times New Roman font files.')
 exact=True
elif a.preview:
 names={f.name for f in font_manager.fontManager.ttflist};cn=next((n for n in ['Noto Serif CJK JP','Noto Sans CJK JP'] if n in names),'DejaVu Serif');en='Liberation Serif';exact=False
else:p.error('Missing fonts. Place simsun.ttc and times.ttf in fonts/ or supply --font and --latin-font.')
plt.rcParams.update({'font.family':[en,cn],'font.size':12,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'path'})
w=openpyxl.load_workbook(data,read_only=True,data_only=True)
def rows(name):
 vals=iter(w[name].values);head=next(vals);return [dict(zip(head,r)) for r in vals if any(v is not None for v in r)]
def add_ratios(r):
 if r.get('O/C') is not None and r.get('H/C') is not None:return r
 f=r.get('formula',r.get('Formula'));atoms={e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',f)}
 return {**r,'O/C':atoms.get('O',0)/atoms['C'],'H/C':atoms.get('H',0)/atoms['C']}
if 'all_molecules' in w.sheetnames:
 allrows=rows('all_molecules');network=rows('network_molecules');candidate_rows=rows('markers')
 markers={g:{r['formula'] for r in candidate_rows if r['group']=='Lake' and r['candidate_source']==g} for g in ['Groundwater','Sediment']}
else:
 allrows=None;network=[add_ratios(r) for r in rows('04_all_molecule_degrees')];hr=rows('05_heatmap_raw')
 markers={g:{r['formula'] for r in hr if r['source']==g} for g in ['Groundwater','Sediment']}
 print('Only filtered network molecules are available; full-range VK will not be drawn.')
w.close()
colors={'Lake':'#177D99','Sediment':'#BC643E','Groundwater':'#546CB0'};groups=list(colors)
report=[]
def draw(rs,name,filtered=False):
 fig,axs=plt.subplots(1,3,figsize=(14,4.8),sharex=True,sharey=True)
 for ax,g in zip(axs,groups):
  selected=[add_ratios(r) for r in rs if r['group']==g]
  xs=[float(r['O/C']) for r in selected];ys=[float(r['H/C']) for r in selected]
  ax.scatter(xs,ys,s=10,c=colors[g],alpha=.4,linewidths=0,rasterized=True)
  ax.set_title(g);ax.set_xlabel('O/C');ax.grid(alpha=.12)
  ax.set_xlim(-.04, max(1.22,max(float(add_ratios(r)['O/C']) for r in rs)*1.03))
  ax.set_ylim(-.04,1.55 if filtered else max(2.5,max(float(add_ratios(r)['H/C']) for r in rs)*1.03))
  if not filtered:ax.axhline(1.5,color='#AAA',ls='--',lw=.8)
  report.append({'figure':name,'group':g,'formulas':len(selected),'point_count':len(xs),'one_point':'one formula, unweighted'})
 axs[0].set_ylabel('H/C');fig.tight_layout()
 for ext in ['png','pdf','svg']:fig.savefig(out/(name+'.'+ext),dpi=300,bbox_inches='tight')
 plt.close(fig)
if allrows:draw(allrows,'01_VK_all_molecules')
draw(network,'02_VK_network_filtered',True)
# Locate the 25 candidates in Lake, retaining the original source-specific identity.
rs=[add_ratios(r) for r in (allrows or network) if r['group']=='Lake']
lookup={r['formula']:r for r in rs}
fig,ax=plt.subplots(figsize=(7,5.8));ax.scatter([float(r['O/C']) for r in rs],[float(r['H/C']) for r in rs],s=10,c='#CED3D9',alpha=.5,linewidths=0,rasterized=True)
for g,shape in [('Groundwater','o'),('Sediment','^')]:
 rr=[lookup[f] for f in sorted(markers[g])];ax.scatter([float(r['O/C']) for r in rr],[float(r['H/C']) for r in rr],s=55,marker=shape,c=colors[g],edgecolors='white',linewidths=.5,label=g,zorder=3)
ax.set_xlabel('O/C');ax.set_ylabel('H/C');ax.legend(frameon=False);ax.grid(alpha=.12)
ax.set_xlim(-.04,max(1.22,max(float(r['O/C']) for r in rs)*1.03));ax.set_ylim(-.04,max(2.5,max(float(r['H/C']) for r in rs)*1.03) if allrows else 1.55)
fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(out/('03_VK_Lake_candidates.'+ext),dpi=300,bbox_inches='tight')
plt.close(fig)
(out/'plot_metadata.json').write_text(json.dumps({'exact_requested_fonts':exact,'Chinese_font':cn,'Latin_font':en,'all_molecules_available':bool(allrows),'data':str(data),'counts':report,'Lake_groundwater_candidates':len(markers['Groundwater']),'Lake_sediment_candidates':len(markers['Sediment']),'note':'Ratio-position overlap means multiple formulas can share coordinates; no compound class inferred from VK regions.'},ensure_ascii=False,indent=2))
print('Done:',out.resolve());print('Fonts:',cn,en,'exact=',exact)
