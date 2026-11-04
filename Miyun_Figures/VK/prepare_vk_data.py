from pathlib import Path
import csv,openpyxl
root=Path(__file__).resolve().parents[1];base=root/'completed_output';out=root/'vk_figures'
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
markers={g:{r['formula'] for r in read(base/g/'source_unique_marker_candidates.csv') if int(r['lake_detection_count'])>0} for g in ['Groundwater','Sediment']}
allrows=[];markerrows=[]
for g in ['Lake','Sediment','Groundwater']:
 for r in read(base/g/'merged_formula_matrix.csv'):
  c,h,o=int(r['C']),int(r['H']),int(r['O']);assert c>0
  origin=next((s for s in markers if r['formula'] in markers[s]),'')
  row={'group':g,'formula':r['formula'],'C':c,'H':h,'N':int(r['N']),'O':o,'P':int(r['P']),'S':int(r['S']),'O/C':o/c,'H/C':h/c,'representative_measured_mz':r['representative_measured_mz'],'network_filter_pass':int(r['network_filter_pass']),'detection_count':int(r['detection_count']),'candidate_source':origin}
  allrows.append(row)
  if origin:markerrows.append(row)
network=[r for r in allrows if r['network_filter_pass']]
w=openpyxl.Workbook();w.remove(w.active)
for name,rs in [('all_molecules',allrows),('network_molecules',network),('markers',markerrows)]:
 with (out/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rs[0]));wr.writeheader();wr.writerows(rs)
 s=w.create_sheet(name);keys=list(rs[0]);s.append(keys)
 for r in rs:s.append([r[k] for k in keys])
 s.freeze_panes='C2';s.auto_filter.ref=s.dimensions
w.save(out/'vk_plot_data.xlsx')
assert len(network)==5842 and len(markerrows)==50
print('all',len(allrows),'network',len(network),'marker source+Lake rows',len(markerrows))
