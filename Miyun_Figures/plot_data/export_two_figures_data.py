from pathlib import Path
import csv,math,hashlib,zipfile
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font,PatternFill
R=Path(__file__).resolve().parents[1];F=R/'figures';B=R/'completed_output';O=R/'two_figures_plot_data';O.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(name,rs):
 with (O/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
groups=['Lake','Sediment','Groundwater'];bins=['0','1','2–5','6–10','11–20','>20']
dist=read(F/'03_连接次数分布.csv');index={(r['degree_category'],r['group']):r for r in dist}
percent=[{'degree_category':c,**{g:float(index[c,g]['percent']) for g in groups}} for c in bins]
counts=[{'degree_category':c,**{g:int(index[c,g]['molecules']) for g in groups}} for c in bins]
allm=[];pools=[]
for g in groups:
 ms=read(B/g/'molecule_transformation_counts.csv');ds=[int(r['transformation_count']) for r in ms]
 assert sum(int(index[c,g]['molecules']) for c in bins)==len(ms)
 assert abs(sum(float(index[c,g]['percent']) for c in bins)-100)<1e-9
 pools.append({'group':g,'network_molecule_total':len(ms),'RI_pool_k_le_1':sum(d<=1 for d in ds),'marker_pool_k_eq_0':sum(d==0 for d in ds)})
 for r in ms:
  allm.append({'group':g,'formula':r['formula'],'representative_measured_mz':r['representative_measured_mz'],'H/C':r['H/C'],'transformation_count':int(r['transformation_count']),'RI_pool':int(r['RI_pool']),'marker_pool':int(r['marker_main_pool'])})
heat=read(F/'05_Lake候选热图原始数据.csv');raw=[];log=[];annot=[]
for i,r in enumerate(heat,1):
 base={'row_order':i,'source':r['source'],'formula':r['formula'],'source_degree':int(r['source_degree']),'lake_detection_count':int(r['lake_detection_count'])}
 rv={f'Lake_K{j}':int(Decimal(r[f'K{j}-shui_result'])) if r[f'K{j}-shui_result'] else '' for j in [1,2,3]}
 assert sum(v!='' for v in rv.values())==base['lake_detection_count']
 raw.append({**base,**rv})
 log.append({**base,**{k:math.log10(v) if v!='' else '' for k,v in rv.items()}})
 annot.append({**base,**{k:format(v/1e6,'.2f') if v!='' else '' for k,v in rv.items()}})
assert len(raw)==25
assert sum(r['source']=='Groundwater' for r in raw)==19
sets={g:{r['formula'] for r in raw if r['source']==g} for g in ['Groundwater','Sediment']}
lake_formula=set().union(*sets.values())
records=[]
for g in ['Groundwater','Sediment','Lake']:
 rr=read(B/g/'filtered_records_mz200_900_positive.csv')
 for r in rr:
  if r['canonical_formula'] in (lake_formula if g=='Lake' else sets[g]):
   records.append({k:r[k] for k in ['group','sample','canonical_formula','meas.m/z','intens','source_file','sheet','excel_row','formula']})
# Verify every heatmap raw value against the retained actual sample record.
lookup={(r['sample'],r['canonical_formula']):int(Decimal(r['intens'])) for r in records if r['group']=='Lake'}
for r in raw:
 for j in [1,2,3]:
  assert r[f'Lake_K{j}']==lookup.get((f'K{j}-shui_result',r['formula']),'')
meta=[{'item':'figure_version','value':'严格复现截图：地下水19、沉积物6；未改用后续双规则交集10个名单'},
{'item':'degree_meaning','value':'组内中位质量、N>0且H/C<1.5筛后网络的不同分子邻居数，不是逐样本转化次数'},
{'item':'distribution_percent','value':'百分数为0–100；每组分母是该组全部网络分子，未按峰强加权'},
{'item':'pool_overlap','value':'marker池k=0是RI池k≤1的子集，不能把两柱相加'},
{'item':'heatmap_colors','value':'颜色用log10(原始峰强)，全图共同色阶，不进行行归一化'},
{'item':'heatmap_annotations','value':'格内文字=原始峰强/1000000，保留两位小数'},
{'item':'heatmap_missing','value':'空白表示未检出，画灰色；不得当作实测0或对其取log10'},
{'item':'sample_names','value':'Lake_K1/K2/K3分别对应K1-shui_result/K2-shui_result/K3-shui_result'},
{'item':'row_order','value':'热图必须按row_order从1到25排序，前19地下水、后6沉积物'},
{'item':'interpretation','value':'Lake检出不等于稳定性验证；原始峰强不代表来源氮贡献比例'}]
tables=[('01_degree_percent',percent),('02_degree_counts',counts),('03_RI_marker_pools',pools),('04_all_molecule_degrees',allm),('05_heatmap_raw',raw),('06_heatmap_log10',log),('07_heatmap_labels',annot),('08_original_peak_records',records),('09_degree_long',dist),('10_instructions',meta)]
w=openpyxl.Workbook();w.remove(w.active)
for name,rs in tables:
 write(name+'.csv',rs)
 s=w.create_sheet(name);keys=list(rs[0]);s.append(keys)
 for r in rs:
  vals=[]
  for k in keys:
   v=r.get(k,'')
   if name=='04_all_molecule_degrees' and k in ['representative_measured_mz','H/C']:v=float(v)
   if name=='09_degree_long' and k in ['molecules','percent']:v=float(v)
   vals.append(v if v!='' else None)
  s.append(vals)
 for c in s[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='315B78')
 s.freeze_panes='B2';s.auto_filter.ref=s.dimensions
 s.column_dimensions['A'].width=24;s.column_dimensions['B'].width=25
w.save(O/'two_figures_plot_data.xlsx')
(O/'README.md').write_text('''# 两张图的原始作图数据

下载 two_figures_plot_data.xlsx 即可，10个sheet也分别提供CSV。

## 图1：连接次数分布+RI/marker柱状图

- 左图：01_degree_percent.csv；第一列是分类，Lake/Sediment/Groundwater三列是百分数，直接做分组柱状图。百分数已为0–100，不要再次乘100。
- 02_degree_counts.csv是对应分子数，09_degree_long.csv是原始长表，04_all_molecule_degrees.csv是每个分子实际连接数，可独立重算分布。
- 右图：03_RI_marker_pools.csv，取RI_pool_k_le_1及marker_pool_k_eq_0两列。对应Lake 215/117、Sediment 157/94、Groundwater 264/138。marker是RI子集，两柱不能相加。

## 图2：Lake候选峰强热图

- 05_heatmap_raw.csv：原始峰强整数矩阵，行顺序完全对应截图，前19行地下水、后6行沉积物。
- 06_heatmap_log10.csv：颜色矩阵，使用这张表画热图，按全图共同最小/最大值确定色阶，不作行归一化。
- 07_heatmap_labels.csv：格内文字，原始峰强除以10^6，保留两位小数。
- 空白表示未检出，显示灰色和横线；不能填0后取log10。
- 08_original_peak_records.csv：25个分子在来源和Lake中的筛后原始峰记录，包含样本名、实测m/z、原始峰强、来源工作簿、sheet、Excel行号。CSV保留精确十进制文本。

本交付复现用户截图19+6的已有图，不使用后续17个或双规则交集10个替换。候选零连接指来源筛后中位质量网络；Lake检出不是稳定性验证。峰强未经归一化，不解释为来源氮贡献比例。
''')
(O/'export_two_figures_data.py').write_bytes(Path(__file__).read_bytes())
files=sorted(p for p in O.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
with zipfile.ZipFile(R/'two_figures_plot_data.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.iterdir()):z.write(p,p.name)
with zipfile.ZipFile(R/'two_figures_plot_data.zip') as z:assert z.testzip() is None
print('PASS: percentages sum to100; degree counts match full molecule tables; all 25 heatmap intensity rows equal original Lake records')
print('pools',pools);print('molecule_rows',len(allm),'original_peak_records',len(records))
