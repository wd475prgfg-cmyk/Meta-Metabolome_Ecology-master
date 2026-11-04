#!/usr/bin/env python3
"""Colored VK panels. Empirical regions, not structural identifications."""
from pathlib import Path
from fractions import Fraction as F
import csv,argparse,json,math,re
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle,Patch
p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path);p.add_argument('--font',type=Path);p.add_argument('--latin-font',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args()
root=a.data_dir;out=a.out or root/('preview_classified_vk' if a.preview else 'figures_vk_classified');out.mkdir(parents=True,exist_ok=True)
cnpath=a.font or root/'fonts/simsun.ttc';enpath=a.latin_font or root/'fonts/times.ttf'
if cnpath.exists() and enpath.exists():
 for f in [cnpath,enpath]:font_manager.fontManager.addfont(str(f))
 cn=font_manager.FontProperties(fname=str(cnpath)).get_name();en=font_manager.FontProperties(fname=str(enpath)).get_name();exact=cn.lower() in ['simsun','宋体'] and en.lower()=='times new roman'
 if not exact:p.error('Expected SimSun and Times New Roman.')
elif a.preview:
 cn='Noto Serif CJK JP';en='Liberation Serif';exact=False
else:p.error('Missing fonts: put simsun.ttc and times.ttf in fonts/ or use --font and --latin-font.')
plt.rcParams.update({'font.family':[en,cn],'font.size':11,'axes.unicode_minus':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'path'})
# Mutually exclusive empirical intervals. Integer atom counts -> exact rational tests.
CLASSES=[('Lipids-like','#69BE98'),('Aliphatic/Peptides-like','#FDA17D'),('Lignin-like','#4D87BA'),('Carbohydrates-like','#EFC1CA'),('Unsaturated hydrocarbons-like','#A07AC4'),('Condensed aromatics-like','#9C6F64'),('Tannins-like','#F2DA8C'),('Unclassified','#969696')]
REGIONS=[('Lipids-like',0,.3,1.5,2),('Aliphatic/Peptides-like',.3,.67,1.5,2.2),('Lignin-like',.1,.67,.7,1.5),('Carbohydrates-like',.67,1.2,1.5,2.4),('Unsaturated hydrocarbons-like',0,.1,.7,1.5),('Condensed aromatics-like',0,.67,.2,.7),('Tannins-like',.67,1.2,.5,1.5)]
def classify(r):
 c,h,o=int(r['C']),int(r['H']),int(r['O']);assert c>0
 x,y=F(o,c),F(h,c)
 if 0<=x<F(3,10) and F(3,2)<=y<=2:return 'Lipids-like'
 if F(3,10)<=x<F(67,100) and F(3,2)<=y<=F(11,5):return 'Aliphatic/Peptides-like'
 if F(1,10)<=x<F(67,100) and F(7,10)<=y<F(3,2):return 'Lignin-like'
 if F(67,100)<=x<=F(6,5) and F(3,2)<=y<=F(12,5):return 'Carbohydrates-like'
 if 0<=x<F(1,10) and F(7,10)<=y<F(3,2):return 'Unsaturated hydrocarbons-like'
 if 0<=x<F(67,100) and F(1,5)<=y<F(7,10):return 'Condensed aromatics-like'
 if F(67,100)<=x<=F(6,5) and F(1,2)<=y<F(3,2):return 'Tannins-like'
 return 'Unclassified'
def read(name):
 with (root/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(name,rs,fields=None):
 with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rs[0]));w.writeheader();w.writerows(rs)
groups=read('group_molecules.csv')
for r in groups:
 r['O/C']=float(F(int(r['O']),int(r['C'])));r['H/C']=float(F(int(r['H']),int(r['C'])));r['VK_region']=classify(r)
xmax=max(1.25,max(r['O/C'] for r in groups)*1.02);ymax=max(2.5,math.ceil(max(r['H/C'] for r in groups)*10)/10)
COLORS=dict(CLASSES);STATS=[]
def panels(rows,keys,keyfield,labels,name,ncols):
 nrows=math.ceil(len(keys)/ncols);fig,axs=plt.subplots(nrows,ncols,figsize=(3.4*ncols,3.05*nrows+1.0),sharex=True,sharey=True,squeeze=False)
 for i,(key,ax) in enumerate(zip(keys,axs.flat)):
  rs=[r for r in rows if r[keyfield]==key];counts=Counter(r['VK_region'] for r in rs)
  for cls,_ in CLASSES:
   rr=[r for r in rs if r['VK_region']==cls]
   ax.scatter([r['O/C'] for r in rr],[r['H/C'] for r in rr],s=2.2 if len(keys)>3 else 3.8,c=COLORS[cls],alpha=.68,linewidths=0,rasterized=True,zorder=2)
  for cls,x0,x1,y0,y1 in REGIONS:ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='none',edgecolor='#737373',linestyle=(0,(2,2)),linewidth=.65,zorder=3))
  ax.set_xlim(-.025,xmax);ax.set_ylim(-.025,ymax+.03);ax.set_xticks([0,.25,.5,.75,1,1.25]);ax.set_yticks([0,.5,1,1.5,2,2.5]+([3] if ymax>=3 else []));ax.tick_params(direction='out',length=2.5,width=.6,labelsize=9,labelbottom=True,labelleft=True)
  ax.set_xlabel('O/C',labelpad=2);ax.set_ylabel('H/C',labelpad=2);ax.set_title(labels[key],fontsize=11,pad=5)
  ax.text(-.10,1.02,chr(97+i),transform=ax.transAxes,fontsize=15,ha='left',va='bottom')
  for cls,_ in CLASSES:STATS.append({'figure':name,'panel':chr(97+i),'group_or_sample':key,'VK_region':cls,'formula_count':counts[cls],'total_formulas':len(rs),'percent':100*counts[cls]/len(rs)})
  assert sum(counts.values())==len(rs)
 for ax in list(axs.flat)[len(keys):]:ax.set_visible(False)
 handles=[Patch(facecolor=c,edgecolor='none',label=n) for n,c in CLASSES]
 fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.012),ncol=4,frameon=False,fontsize=9,columnspacing=1.4,handlelength=1.3)
 fig.subplots_adjust(left=.065,right=.985,top=.91 if nrows==1 else .96,bottom=.26 if nrows==1 else .13,wspace=.22,hspace=.36)
 for ext in ['png','pdf','svg']:fig.savefig(out/(name+'.'+ext),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)
order=['Groundwater','Lake','Sediment'];labels={g:g for g in order}
panels(groups,order,'group',labels,'01_VK_classified_three_groups',3)
filtered=[r for r in groups if int(r['network_filter_pass'])]
panels(filtered,order,'group',labels,'03_VK_classified_network_filtered',3)
write('VK_region_statistics.csv',STATS)
write('group_molecules_classified.csv',groups)
write('region_boxes.csv',[{'region':cls,'O_C_min':x0,'O_C_max':x1,'H_C_min':y0,'H_C_max':y1} for cls,x0,x1,y0,y1 in REGIONS])
(out/'plot_metadata.json').write_text(json.dumps({'exact_requested_fonts':exact,'Chinese_font':cn,'Latin_font':en,'scope':'measured m/z 200-900 and positive intensity; group/sample formula deduplication','group_formula_rows':len(groups),'network_formula_rows':len(filtered),'x_range':[-.025,xmax],'y_range':[-.025,ymax+.03],'interpretation':'Empirical VK region labels only, not confirmed compound structures. Regional membership uses exact rational atomic ratios; intervals documented in README. Reference image supplied no numeric boundary table; chosen boundaries are explicit operational rules, not claimed to reproduce the original publication exactly.'},ensure_ascii=False,indent=2))
print('Done:',out.resolve());print('Fonts:',cn,en,'exact=',exact)
