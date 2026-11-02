#!/usr/bin/env python3
"""Export provisional GW molecular candidates and their Lake detections."""
import argparse
from collections import defaultdict
import csv
from io import BytesIO
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from openpyxl import load_workbook
import xlsxwriter

def run(candidate_csv, peaks_csv, groundwater, lake_zip, out):
    out.mkdir(parents=True,exist_ok=True)
    with candidate_csv.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; candidates=list(reader)
    formulas={r['formula'] for r in candidates}
    if len(formulas)!=len(candidates):raise ValueError('Duplicate candidate formula')
    degree={}; sample_names={'GW':set(),'Lake':set()}
    with peaks_csv.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            e,s,formula=r['endpoint'],r['sample'],r['formula'];sample_names[e].add(s)
            if formula in formulas:
                key=(e,s,formula)
                if key in degree:raise ValueError(f'Duplicate sample/formula {key}')
                degree[key]=(round(float(r['Mass']),6),int(r['transformation_count']))
    if (len(sample_names['GW']),len(sample_names['Lake']))!=(6,50):raise ValueError('Unexpected sample count')
    intensities={}
    def collect(sheet,endpoint,name):
        rows=sheet.iter_rows(values_only=True); header=next(rows); ix={v:i for i,v in enumerate(header)}
        for r in rows:
            formula=r[ix['formula']]
            if formula not in formulas:continue
            key=(endpoint,f'Sample_{endpoint}_{name}',formula)
            if key not in degree:continue
            mass=round(float(r[ix['meas.m/z']]),6);value=float(r[ix['intens']])
            if mass!=degree[key][0] or value<=0 or key in intensities:raise ValueError(f'Input mismatch {key}')
            intensities[key]=value
    w=load_workbook(groundwater,read_only=True,data_only=True)
    for sheet in w:
        if sheet.title!='ALL_6_GW':collect(sheet,'GW',sheet.title)
    w.close()
    with ZipFile(lake_zip) as z:
        names=[n for n in z.namelist() if n.startswith('Lake/') and n.endswith('_result.xlsx') and len(PurePosixPath(n).parts)==2]
        if len(names)!=50:raise ValueError('Expected 50 lake workbooks')
        for n in names:
            name=PurePosixPath(n).stem.removesuffix('_result')
            book=load_workbook(BytesIO(z.read(n)),read_only=True,data_only=True)
            collect(book.active,'Lake',name);book.close()
    if set(degree)!=set(intensities):raise ValueError('Missing intensity for retained peak')
    for r in candidates:
        f=r['formula'];gw=[k for k in degree if k[0]=='GW' and k[2]==f];lake=[k for k in degree if k[0]=='Lake' and k[2]==f]
        if len(gw)!=int(r['GW_detected_samples']) or len(lake)!=int(r['Lake_detected_samples']) or sum(degree[k][1]==0 for k in gw)!=int(r['GW_zero_samples']):raise ValueError(f'Candidate summary mismatch {f}')
    detected=[r for r in candidates if int(r['Lake_detected_samples'])>0]
    absent=[r for r in candidates if int(r['Lake_detected_samples'])==0]
    assert (len(candidates),len(detected),len(absent))==(510,440,70)
    with (out/'GW候选_湖水检出.csv').open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader();wr.writerows(detected)
    detail_fields=['endpoint','sample','formula','Mass','raw_intensity','transformation_count','GW_zero_condition']
    with (out/'候选_逐样本明细.csv').open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.writer(f);wr.writerow(detail_fields)
        for key in sorted(degree):
            e,s,formula=key;mass,n=degree[key]
            wr.writerow([e,s,formula,f'{mass:.6f}',intensities[key],n,int(e=='GW' and n==0)])
    book=xlsxwriter.Workbook(str(out/'地下水零次候选marker.xlsx'),{'constant_memory':True})
    header_fmt=book.add_format({'bold':True,'bg_color':'#245A81','font_color':'white'})
    notes=book.add_worksheet('说明')
    for i,line in enumerate(['地下水零次候选 marker（Lake 为受体）',
       '条件：H/C < 1.5 且在至少一个地下水样本中转化次数 = 0；按分子式合并。',
       '共510个候选分子式，440个在湖水至少一个样本检出，70个未检出。',
       '尚无其他来源端元比较，不能认定来源独有；论文的稳定性验证也尚未完成。',
       '逐样本表和峰强矩阵保留原始峰强，空白表示该样本未检出。']):notes.write_string(i,0,line)
    notes.set_column(0,0,110)
    numeric=set(fields)-{'formula','GW_zero_sample_names','Lake_detected_sample_names'}
    def table(title,rows):
        ws=book.add_worksheet(title);ws.freeze_panes(1,1)
        for j,v in enumerate(fields):ws.write_string(0,j,v,header_fmt)
        for i,r in enumerate(rows,1):
            for j,k in enumerate(fields):
                if k in numeric:ws.write_number(i,j,float(r[k]))
                else:ws.write_string(i,j,r[k])
        ws.autofilter(0,0,len(rows),len(fields)-1);ws.set_column(0,len(fields)-3,20);ws.set_column(len(fields)-2,len(fields)-1,60)
    table('GW候选_510',candidates);table('湖水检出_440',detected);table('湖水未检出_70',absent)
    ws=book.add_worksheet('逐样本明细');ws.freeze_panes(1,2)
    for j,v in enumerate(detail_fields):ws.write_string(0,j,v,header_fmt)
    for i,key in enumerate(sorted(degree),1):
        e,s,formula=key;mass,n=degree[key];row=[e,s,formula,mass,intensities[key],n,int(e=='GW' and n==0)]
        for j,v in enumerate(row):
            if isinstance(v,str):ws.write_string(i,j,v)
            else:ws.write_number(i,j,v)
    ws.autofilter(0,0,len(degree),len(detail_fields)-1);ws.set_column(0,6,25)
    ws=book.add_worksheet('原始峰强矩阵');ws.freeze_panes(1,1)
    samples=sorted(sample_names['GW'])+sorted(sample_names['Lake'])
    for j,v in enumerate(['formula']+samples):ws.write_string(0,j,v,header_fmt)
    for i,formula in enumerate(sorted(formulas),1):
        ws.write_string(i,0,formula)
        for j,s in enumerate(samples,1):
            key=('GW' if s.startswith('Sample_GW_') else 'Lake',s,formula)
            if key in intensities:ws.write_number(i,j,intensities[key])
    ws.set_column(0,0,22);ws.set_column(1,len(samples),18)
    book.close()
    print('GW candidates',len(candidates),'detected in Lake',len(detected),'sample observations',len(degree))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidates',type=Path,required=True);p.add_argument('--peaks',type=Path,required=True)
    p.add_argument('--groundwater',type=Path,required=True);p.add_argument('--lake-zip',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    run(a.candidates,a.peaks,a.groundwater,a.lake_zip,a.output_dir)
