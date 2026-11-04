#!/usr/bin/env python3
"""Render the two supplied figures from CSV directory or original data workbook.
Example: python render_two_figures.py --data two_figures_plot_data.xlsx
No access to the original /workspace analysis paths is required.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--data',type=Path,default=Path(__file__).resolve().parent,help='CSV directory or two_figures_plot_data.xlsx')
p.add_argument('--out',type=Path,default=None,help='Output directory (default: figures beside data)')
p.add_argument('--font', '--cn-font', dest='font',type=Path,help='SimSun file, e.g. fonts/simsun.ttc')
p.add_argument('--latin-font',type=Path,help='Times New Roman file, e.g. fonts/times.ttf')
p.add_argument('--preview',action='store_true',help='Explicitly allow substitute fonts for a layout preview only')
a=p.parse_args();data=a.data.expanduser().resolve()
out=a.out if a.out else (data if data.is_dir() else data.parent)/'figures';out.mkdir(parents=True,exist_ok=True)
# Search user-provided files before installed fonts. Exact required fonts are mandatory
# unless --preview is explicitly selected; substitutes are never reported as SimSun/TNR.
font_dirs=[Path(__file__).resolve().parent/'fonts',(data if data.is_dir() else data.parent)/'fonts',Path('C:/Windows/Fonts')]
def resolve_font(path, names, filenames):
 if path:
  if not path.exists():p.error('Font file does not exist: '+str(path))
  font_manager.fontManager.addfont(str(path))
  family=font_manager.FontProperties(fname=str(path)).get_name()
  if family.lower() not in {n.lower() for n in names}:p.error('Wrong font family '+family+'; expected '+str(names))
  return family,str(path)
 for directory in font_dirs:
  for filename in filenames:
   candidate=directory/filename
   if candidate.exists():return resolve_font(candidate,names,filenames)
 for f in font_manager.fontManager.ttflist:
  if f.name.lower() in {n.lower() for n in names}:return f.name,f.fname
 return None,None
cn_font,cn_path=resolve_font(a.font,['SimSun','宋体'],['simsun.ttc','simsun.ttf','SimSun.ttf'])
latin_font,latin_path=resolve_font(a.latin_font,['Times New Roman'],['times.ttf','Times New Roman.ttf','TimesNewRoman.ttf'])
exact_fonts=bool(cn_font and latin_font)
if not exact_fonts:
 if not a.preview:
  p.error('Required font missing: '+', '.join(n for n,v in [('SimSun / 宋体',cn_font),('Times New Roman',latin_font)] if not v)+'. Put simsun.ttc and times.ttf in fonts/, or use --font and --latin-font. --preview is only a substitute-font layout preview.')
 names={f.name for f in font_manager.fontManager.ttflist}
 cn_font=cn_font or next((n for n in ['Noto Serif CJK SC','Noto Serif CJK JP','Noto Sans CJK JP'] if n in names),None)
 latin_font=latin_font or next((n for n in ['Liberation Serif','Nimbus Roman','DejaVu Serif'] if n in names),'DejaVu Serif')
 if a.out is None:out=(data if data.is_dir() else data.parent)/'preview_figures';out.mkdir(parents=True,exist_ok=True)
 print('LAYOUT PREVIEW ONLY: substitute fonts:',cn_font,latin_font)
cn=bool(cn_font)
# Matplotlib >=3.6 performs per-glyph fallback: Latin/digits in Times New Roman,
# Chinese glyphs in SimSun. Do not use mathtext, which would introduce a third font.
plt.rcParams.update({'font.family':[latin_font]+([cn_font] if cn_font else []),'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'font.size':13,'pdf.fonttype':42,'svg.fonttype':'path'})
def text(zh,en):return zh if cn else en
wb=None
if data.is_file():
 import openpyxl
 wb=openpyxl.load_workbook(data,read_only=True,data_only=True)
elif data.is_dir() and not (data/'01_degree_percent.csv').exists() and (data/'two_figures_plot_data.xlsx').exists():
 import openpyxl
 wb=openpyxl.load_workbook(data/'two_figures_plot_data.xlsx',read_only=True,data_only=True)
def rows(name):
 if wb is not None:
  values=iter(wb[name].values);header=next(values)
  return [dict(zip(header,row)) for row in values if any(v is not None for v in row)]
 with (data/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(fig,name):
 for ext in ['png','pdf','svg']:fig.savefig(out/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)
groups=['Lake','Sediment','Groundwater'];colors={'Lake':'#177D99','Sediment':'#BC643E','Groundwater':'#546CB0'}
percent=rows('01_degree_percent');pools={r['group']:r for r in rows('03_RI_marker_pools')}
fig,(ax,bx)=plt.subplots(1,2,figsize=(14,5.8),gridspec_kw={'width_ratios':[1.5,1]})
for i,g in enumerate(groups):
 values=[float(r[g]) for r in percent];assert abs(sum(values)-100)<1e-7
 ax.bar(np.arange(len(percent))+(i-1)*.25,values,.23,color=colors[g],label=g)
ax.set_xticks(range(len(percent)),[str(r['degree_category']) for r in percent]);ax.set_xlabel(text('连接数 k','Number of neighbors, k'));ax.set_ylabel(text('分子比例（%）','Molecules (%)'));ax.legend(frameon=False);ax.grid(axis='y',alpha=.15)
x=np.arange(3);ri=[int(pools[g]['RI_pool_k_le_1']) for g in groups];zero=[int(pools[g]['marker_pool_k_eq_0']) for g in groups]
bx.bar(x-.16,ri,.30,color='#9FB2C1',label=text('RI 池 k ≤ 1','RI pool k <= 1'));bx.bar(x+.16,zero,.30,color='#DF9C2E',label=text('marker 池 k = 0','Marker pool k = 0'))
for pos,l,r in zip(x,ri,zero):bx.text(pos-.16,l+4,str(l),ha='center');bx.text(pos+.16,r+4,str(r),ha='center')
bx.set_xticks(x,groups);bx.set_ylim(0,max(ri)*1.25);bx.set_ylabel(text('分子式数','Number of molecular formulas'));bx.legend(frameon=False);bx.grid(axis='y',alpha=.15)
fig.subplots_adjust(bottom=.15,top=.95,wspace=.28)
save(fig,'01_degree_distribution_and_pools')
raw=sorted(rows('05_heatmap_raw'),key=lambda r:int(r['row_order']));logs=sorted(rows('06_heatmap_log10'),key=lambda r:int(r['row_order']));labels=sorted(rows('07_heatmap_labels'),key=lambda r:int(r['row_order']))
assert len(raw)==len(logs)==len(labels)==25
for r,l,t in zip(raw,logs,labels):assert r['formula']==l['formula']==t['formula']
def missing(v):return v is None or v==''
cols=['Lake_K1','Lake_K2','Lake_K3']
values=np.array([[np.nan if missing(r[c]) else float(r[c]) for c in cols] for r in logs])
for i,r in enumerate(raw):
 for j,c in enumerate(cols):
  if not missing(r[c]):assert abs(values[i,j]-np.log10(float(r[c])))<1e-10
fig=plt.figure(figsize=(9,10));ax=fig.add_axes([.30,.05,.48,.88]);cax=fig.add_axes([.84,.36,.025,.31])
cmap=plt.colormaps['YlGnBu'].copy();cmap.set_bad('#EAECEF')
im=ax.imshow(np.ma.masked_invalid(values),aspect='auto',cmap=cmap,vmin=np.nanmin(values),vmax=np.nanmax(values))
ax.set_yticks(range(25),[r['formula'] for r in raw],fontsize=12);ax.set_xticks(range(3),['Lake K1','Lake K2','Lake K3']);ax.xaxis.tick_top()
for tick,r in zip(ax.get_yticklabels(),raw):tick.set_color(colors[r['source']])
for i,r in enumerate(labels):
 for j,c in enumerate(cols):
  label='—' if missing(r[c]) else f'{float(r[c]):.2f}'
  ax.text(j,i,label,ha='center',va='center',fontsize=11,color='white' if np.isfinite(values[i,j]) and values[i,j]>(np.nanmin(values)+np.nanmax(values))/2 else '#203247')
ax.axhline(18.5,color='white',lw=4);ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,25,1),minor=True);ax.grid(which='minor',color='white',lw=.8);ax.tick_params(which='minor',bottom=False,left=False)
fig.colorbar(im,cax=cax).set_label(text('log10（峰强）','log10(intensity)'))
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=colors['Groundwater'],label='Groundwater'),Patch(color=colors['Sediment'],label='Sediment')],loc='upper right',bbox_to_anchor=(.995,.99),frameon=False,fontsize=10)
save(fig,'02_lake_marker_heatmap')
if wb is not None:wb.close()
(out/'font_status.json').write_text(json.dumps({'exact_requested_fonts':exact_fonts,'Chinese_font':cn_font,'Chinese_font_file':cn_path,'Latin_font':latin_font,'Latin_font_file':latin_path,'layout':'clean: no titles, footnotes, explanatory paragraphs or count banners','heatmap_cell_numbers':'raw intensity / 10^6, 2 decimals','heatmap_missing':'gray and em dash'},ensure_ascii=False,indent=2))
print('Done. Six files (2 figures x PNG/PDF/SVG):',out.resolve())
