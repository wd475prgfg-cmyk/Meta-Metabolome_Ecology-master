#!/usr/bin/env python3
"""Render the two supplied figures from CSV directory or original data workbook.
Example: python render_two_figures.py --data two_figures_plot_data.xlsx
No access to the original /workspace analysis paths is required.
"""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--data',type=Path,default=Path(__file__).resolve().parent,help='CSV directory or two_figures_plot_data.xlsx')
p.add_argument('--out',type=Path,default=None,help='Output directory (default: figures beside data)')
p.add_argument('--font',type=Path,help='Optional Chinese TTF/OTF/TTC file')
a=p.parse_args();data=a.data.expanduser().resolve()
out=a.out if a.out else (data if data.is_dir() else data.parent)/'figures';out.mkdir(parents=True,exist_ok=True)
if a.font:
 font_manager.fontManager.addfont(str(a.font));font=font_manager.FontProperties(fname=str(a.font)).get_name();cn=True
else:
 names={f.name for f in font_manager.fontManager.ttflist}
 font=next((n for n in ['Noto Sans CJK SC','Noto Sans CJK JP','Microsoft YaHei','SimHei','PingFang SC','WenQuanYi Zen Hei'] if n in names),'DejaVu Sans');cn=font!='DejaVu Sans'
plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'font.size':11,'pdf.fonttype':42,'svg.fonttype':'none'})
if not cn:print('No Chinese font found: using English labels. Use --font path/to/font.ttf for Chinese.')
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
ax.set_xticks(range(len(percent)),[str(r['degree_category']) for r in percent]);ax.set_xlabel(text('每个分子连接的不同分子数 k','Number of distinct molecular neighbors, k'));ax.set_ylabel(text('占该组网络分子的比例（%）','Percentage of network molecules (%)'));ax.legend(frameon=False);ax.grid(axis='y',alpha=.15)
x=np.arange(3);ri=[int(pools[g]['RI_pool_k_le_1']) for g in groups];zero=[int(pools[g]['marker_pool_k_eq_0']) for g in groups]
bx.bar(x-.16,ri,.30,color='#9FB2C1',label=text('RI 池 k ≤ 1','RI pool k <= 1'));bx.bar(x+.16,zero,.30,color='#DF9C2E',label=text('marker 池 k = 0','Marker pool k = 0'))
for pos,l,r in zip(x,ri,zero):bx.text(pos-.16,l+4,str(l),ha='center');bx.text(pos+.16,r+4,str(r),ha='center')
bx.set_xticks(x,groups);bx.set_ylim(0,max(ri)*1.25);bx.set_ylabel(text('分子式数','Number of molecular formulas'));bx.legend(frameon=False);bx.grid(axis='y',alpha=.15)
fig.subplots_adjust(bottom=.22,wspace=.27)
fig.text(.08,.025,text('来源筛后中位质量网络；marker池为RI池的子集。','Source-group networks built after filtering, using median measured masses. Marker pool is a subset of RI pool.'),fontsize=9,color='#566779')
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
fig=plt.figure(figsize=(12,11));ax=fig.add_axes([.29,.12,.49,.74]);cax=fig.add_axes([.82,.38,.022,.30])
cmap=plt.colormaps['YlGnBu'].copy();cmap.set_bad('#EAECEF')
im=ax.imshow(np.ma.masked_invalid(values),aspect='auto',cmap=cmap,vmin=np.nanmin(values),vmax=np.nanmax(values))
ax.set_yticks(range(25),[r['formula'] for r in raw],fontsize=10);ax.set_xticks(range(3),['Lake K1','Lake K2','Lake K3']);ax.xaxis.tick_top()
for tick,r in zip(ax.get_yticklabels(),raw):tick.set_color(colors[r['source']])
for i,r in enumerate(labels):
 for j,c in enumerate(cols):
  label='—' if missing(r[c]) else f'{float(r[c]):.2f}'
  ax.text(j,i,label,ha='center',va='center',fontsize=9,color='white' if np.isfinite(values[i,j]) and values[i,j]>(np.nanmin(values)+np.nanmax(values))/2 else '#203247')
ax.axhline(18.5,color='white',lw=4);ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,25,1),minor=True);ax.grid(which='minor',color='white',lw=.8);ax.tick_params(which='minor',bottom=False,left=False)
fig.colorbar(im,cax=cax).set_label(text('log10（原始峰强）','log10(raw intensity)'))
fig.text(.04,.96,text('Lake中检出的来源独有marker候选','Source-specific marker candidates detected in Lake'),fontsize=19,fontweight='bold')
fig.text(.82,.84,text('地下水独有：19','Groundwater: 19'),color=colors['Groundwater'],fontsize=12,fontweight='bold');fig.text(.82,.80,text('沉积物独有：6','Sediment: 6'),color=colors['Sediment'],fontsize=12,fontweight='bold')
fig.text(.82,.22,text('格内数字 =\n原始峰强 / 10^6\n灰色 / — = 未检出\n不作行归一化','Cell values =\nraw intensity / 10^6\nGray / — = not detected\nNo row normalization'),fontsize=10,linespacing=1.7)
fig.text(.04,.035,text('本图复现19+6名单；Lake检出不等于稳定性验证，原始峰强不代表氮来源贡献。','Reproduces the 19+6 candidate list. Lake detection is not stability validation; raw intensity is not nitrogen source contribution.'),fontsize=9,color='#566779')
save(fig,'02_lake_marker_heatmap')
if wb is not None:wb.close()
print('Done. Six files (2 figures x PNG/PDF/SVG):',out.resolve())
