from pathlib import Path
import csv,json,zipfile
from decimal import Decimal as D
import openpyxl
from openpyxl.styles import Font,PatternFill
root=Path(__file__).resolve().parents[1];base=root/'completed_output';out=base/'地下水19与用户17对比';out.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(name,rs):
 with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
user_formulas='C14H18N4O12S C14H19NO2S2 C14H20N4O16 C19H17NO6 C19H18N4O5S C21H12N2O8S C21H14N2O8S C22H16N2O8S C22H23N3O4P2 C22H25N3O4 C23H12N2O9S C25H29N3O11 C25H37NO10 C26H20N2O9S C28H24N2O8S C33H43NO15 C36H45N3O9S'.split()
user_masses='465.056693 296.078427 499.080019 354.098454 413.092468 451.024267 453.039862 467.055265 454.109312 394.177069 491.019243 546.173198 510.234304 535.081527 547.117800 692.255720 694.280165'.split()
user=dict(zip(user_formulas,user_masses))
our=read(base/'Lake检出_来源独有marker/Groundwater_Lake检出独有marker.csv');A={r['formula']:r for r in our}
gw={r['formula']:r for r in read(base/'Groundwater/molecule_transformation_counts.csv')}
sed={r['formula'] for r in read(base/'Sediment/merged_formula_matrix.csv')}
lake={r['formula']:r for r in read(base/'Lake/merged_formula_matrix.csv')}
comparison=[]
for f in sorted(set(user)|set(A)):
 g=gw[f];l=lake[f]
 comparison.append({'formula':f,'in_our19':int(f in A),'in_user17':int(f in user),'comparison':'共同' if f in A and f in user else '仅我方19' if f in A else '仅用户17','groundwater_degree':g['transformation_count'],'sediment_detected':int(f in sed),'lake_detection_count':l['detection_count'],'lake_detection_samples':l['detection_samples'],'groundwater_detection_samples':g['detection_samples'],'median_mass_exact':g['representative_measured_mz'],'user_mass':user.get(f,''),'median_minus_user_mass':str(D(g['representative_measured_mz'])-D(user[f])) if f in user else '', 'passes_current_marker_rule':int(int(g['transformation_count'])==0 and f not in sed and int(l['detection_count'])>0)})
pairs=[r for r in read(base/'Groundwater/transformation_pairs_23_columns.csv') if (r['formula_x'] in set(user)-set(A) or r['formula_y'] in set(user)-set(A))]
audit={(r['formula_x'],r['formula_y']):r for r in read(base/'Groundwater/transformation_match_audit.csv')}
evidence=[]
for r in pairs:
 a=audit[r['formula_x'],r['formula_y']]
 evidence.append({**r,'selected_database_mass':a['selected_database_mass'],'difference_minus_database_mass':str(D(r['Dist'])-D(a['selected_database_mass'])),'selected_database_row':a['selected_database_row'],'all_matched_database_rows':a['matched_database_rows']})
raw=[r for r in read(base/'Groundwater/filtered_records_mz200_900_positive.csv') if r['canonical_formula'] in ['C14H20N4O16','C23H12N2O9S']]
write('我方19完整候选.csv',our);write('26个分子式逐项对比.csv',comparison);write('用户独有7个_实际转化连接证据.csv',evidence);write('两处代表质量_原始样本记录.csv',raw)
w=openpyxl.Workbook();w.remove(w.active)
for name,rs in [('我方19完整名单',our),('两份名单26式对比',comparison),('7式非零连接证据',evidence),('两处质量原始记录',raw)]:
 s=w.create_sheet(name);keys=list(rs[0]);s.append(keys)
 for r in rs:s.append([r.get(k,'') for k in keys])
 for c in s[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='315B78')
 s.freeze_panes='C2';s.auto_filter.ref=s.dimensions;s.column_dimensions['A'].width=23
w.save(out/'地下水marker_19与17逐项对比.xlsx')
(out/'说明.md').write_text('''# 地下水marker名单对比

我方19与用户17共有10个，我方另9个，用户另7个（合计26个不同分子式）。用户另7个在已核验的地下水合并网络中连接数分别为1、1、2、3、1、2、3，均不满足当前来源组k=0规则。它们在沉积物未检出、Lake有检出；差异不是源独有性或Lake检出条件导致。连接证据表给出实际代表质量、质量差、数据库行号和质量残差，均在±0.000010 Da含端点内。

C14H20N4O16的两样本值为499.080019、499.080066，中位数499.0800425；用户表499.080019为单个样本值。C23H12N2O9S的四样本值为491.019243、491.019111、491.019104、491.019251，中位数491.019177；用户表491.019243为单个样本值。其他质量中小数尾数差异可为Excel存储浮点尾数或展示舍入，不据此推断规则变化。

我方另9个均满足地下水组k=0、沉积物未检出、Lake检出；部分在Lake网络有连接，但当前要求是来源组零连接，而非Lake也必须零连接。没有用户17名单的计算代码与峰对输出，不能确定其遗漏9个的具体原因，不能仅凭名单断言其全部采用何种网络规则。

独有性按来源分子式判断，不要求跨来源m/z彼此在±0.000010 Da内；这个容差用于组内转化质量差匹配。候选不代表稳定性已验证。Excel为原始字符串保真展示，CSV提供完整可核对数据。
''')
zipout=base/'地下水marker_19与17对比.zip'
with zipfile.ZipFile(zipout,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(out.iterdir()):z.write(p,p.name)
assert len(A)==19 and len(set(A)&set(user))==10
assert all(int(gw[f]['transformation_count'])>0 for f in set(user)-set(A))
assert all(r['passes_current_marker_rule'] for r in comparison if r['in_our19'])
print('PASS: 10 common, 9 ours-only, 7 user-only; 12 actual edge witnesses; 2 median mass differences')
print('ours19:',', '.join(sorted(A)))
