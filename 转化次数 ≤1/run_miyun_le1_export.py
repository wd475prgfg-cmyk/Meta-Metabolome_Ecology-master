#!/usr/bin/env python3
"""Export the Miyun H/C < 1.5 and transformation count <= 1 RI pool."""
import argparse
from collections import defaultdict
import csv
from pathlib import Path
import xlsxwriter

PEAK_FIELDS=['endpoint','sample','Mass','formula','C','H','N','O','P','S','H_C',
             'transformation_count','RI_HC_lt_1_5_and_count_le1','WR_zero_condition']
FORM_FIELDS=['formula','C','H','N','O','P','S','H_C','GW_detected_samples',
             'GW_RI_le1_samples','GW_zero_samples','Lake_detected_samples',
             'GW_RI_sample_names','Lake_detected_sample_names']

def run(source,out):
    out.mkdir(parents=True,exist_ok=True)
    pool={'GW':[],'Lake':[]}
    molecules=defaultdict(lambda:{'GW':{},'Lake':{},'elements':None})
    with source.open(newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            e=r['endpoint'];formula=r['formula'];sample=r['sample']
            elems=tuple(int(r[k]) for k in ('C','H','N','O','P','S'))
            c,h=elems[:2];degree=int(r['transformation_count'])
            if c<=0 or e not in pool:raise ValueError('Invalid C count or endpoint')
            ri=2*h<3*c and degree<=1
            if int(r['RI_HC_lt_1_5_and_count_le1'])!=ri:raise ValueError('RI flag mismatch')
            m=molecules[formula]
            if m['elements'] is not None and m['elements']!=elems:raise ValueError('Formula mismatch')
            if sample in m[e]:raise ValueError('Duplicate formula in a sample')
            m['elements']=elems;m[e][sample]=degree
            if ri:pool[e].append(r)
    gw=[]
    for formula,m in sorted(molecules.items()):
        c,h=m['elements'][:2]
        if 2*h>=3*c or not any(d<=1 for d in m['GW'].values()):continue
        ri_names=sorted(s for s,d in m['GW'].items() if d<=1)
        gw.append([formula,*m['elements'],h/c,len(m['GW']),len(ri_names),
                   sum(d==0 for d in m['GW'].values()),len(m['Lake']),
                   '; '.join(ri_names),'; '.join(sorted(m['Lake']))])
    detected=[r for r in gw if r[11]>0]
    zero_detected=[r for r in detected if r[10]>0]
    assert (len(pool['GW']),len(pool['Lake']),len(gw),len(detected),len(zero_detected))==(1157,10454,953,845,440)
    for e in ('GW','Lake'):
        with (out/f'{e}_RI_le1.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=PEAK_FIELDS,extrasaction='ignore');w.writeheader();w.writerows(pool[e])
    for filename,rows in [('GW_RI_le1_formula.csv',gw),('GW_RI_le1_detected_in_Lake.csv',detected),('GW_zero_detected_in_Lake.csv',zero_detected)]:
        with (out/filename).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(FORM_FIELDS);w.writerows(rows)
    book=xlsxwriter.Workbook(str(out/'转化次数 ≤1.xlsx'),{'constant_memory':True})
    head=book.add_format({'bold':True,'bg_color':'#245A81','font_color':'white'})
    info=book.add_worksheet('说明')
    for i,line in enumerate(['转化次数 ≤1：密云 GW 与 Lake RI 初筛',
       '条件：H/C < 1.5 且样本内转化次数 ≤1；同一分子式在任一地下水样本符合即进入 GW 初筛池。',
       'Lake 是待溯源受体；GW 湖水检出仅说明相同分子式在湖水出现，不代表已确认来源特异性。',
       '毛等 WR 论文的进一步 marker 分子条件为 H/C < 1.5 且转化次数 =0，见 GW零次湖水检出。',
       '缺少其他来源端元和生态组装验证，结果为待验证候选。']):info.write_string(i,0,line)
    info.set_column(0,0,110)
    def sheet(title,fields,rows):
        ws=book.add_worksheet(title);ws.freeze_panes(1,2)
        for j,v in enumerate(fields):ws.write_string(0,j,v,head)
        for i,row in enumerate(rows,1):
            for j,v in enumerate(row):
                if fields[j] not in ('endpoint','sample','formula','GW_RI_sample_names','Lake_detected_sample_names'):
                    ws.write_number(i,j,float(v))
                else:ws.write_string(i,j,str(v))
        ws.autofilter(0,0,len(rows),len(fields)-1);ws.set_column(0,1,28);ws.set_column(2,len(fields)-1,19)
    for e in ('GW','Lake'):
        sheet(e+'_RI_≤1',PEAK_FIELDS,[[r[k] for k in PEAK_FIELDS] for r in pool[e]])
    sheet('GW分子式_≤1',FORM_FIELDS,gw)
    sheet('GW≤1_湖水检出',FORM_FIELDS,detected)
    sheet('GW零次_湖水检出',FORM_FIELDS,zero_detected)
    book.close()
    print('GW peaks',len(pool['GW']),'Lake peaks',len(pool['Lake']),'GW formula',len(gw),'in Lake',len(detected),'zero in Lake',len(zero_detected))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corrected-per-peak',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();run(a.corrected_per_peak,a.output_dir)
