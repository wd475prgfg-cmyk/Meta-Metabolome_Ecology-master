#!/usr/bin/env python3
"""Screen endpoint-exclusive molecular formulae with sample-level RI <= 1."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import xlsxwriter

ELEMENTS = ('C', 'H', 'N', 'O', 'P', 'S')
FIELDS = ['endpoint','formula',*ELEMENTS,'endpoint_sample_total','detected_samples',
          'detected_fraction','RI_le1_samples','RI_le1_fraction_all_samples',
          'RI_le1_fraction_detected','RI_eq0_samples','opposite_detected_samples',
          'always_RI_le1_when_detected','RI_le1_at_least_2_samples',
          'min_transformation_count','max_transformation_count',
          'detected_sample_names','RI_le1_sample_names']

def run(source, out):
    out.mkdir(parents=True, exist_ok=True)
    data = defaultdict(lambda: {'GW': {}, 'Lake': {}, 'elements': None})
    with source.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            formula, end, sample = r['formula'], r['endpoint'], r['sample']
            if not formula or formula == 'NA' or end not in ('GW','Lake'):
                raise ValueError('Missing formula or invalid endpoint')
            elems = tuple(int(r[x]) for x in ELEMENTS)
            entry = data[formula]
            if entry['elements'] is not None and entry['elements'] != elems:
                raise ValueError(f'Inconsistent elemental composition for {formula}')
            entry['elements'] = elems
            if sample in entry[end]:
                raise ValueError(f'Duplicate formula within sample: {formula}, {sample}')
            degree = int(r['transformation_count'])
            if int(r['RI_le1']) != (degree <= 1) or int(r['RI_eq0']) != (degree == 0):
                raise ValueError('RI flags disagree with transformation counts')
            entry[end][sample] = degree
    sample_sets = {e: set() for e in ('GW','Lake')}
    for entry in data.values():
        for end in sample_sets: sample_sets[end].update(entry[end])
    if (len(sample_sets['GW']),len(sample_sets['Lake'])) != (6,50):
        raise ValueError('Unexpected number of endpoint samples')

    candidates = {'GW': [], 'Lake': []}
    comparison = []
    for formula, entry in sorted(data.items()):
        gw, lake = entry['GW'], entry['Lake']
        comparison.append([formula,*entry['elements'],len(gw),len(lake),
                           sum(v <= 1 for v in gw.values()),sum(v <= 1 for v in lake.values())])
        for end, other in (('GW','Lake'),('Lake','GW')):
            observed, opposite = entry[end], entry[other]
            ri = sorted(s for s, degree in observed.items() if degree <= 1)
            if not observed or opposite or not ri: continue
            total = len(sample_sets[end]); detected = len(observed)
            candidates[end].append([end,formula,*entry['elements'],total,detected,
                detected/total,len(ri),len(ri)/total,len(ri)/detected,
                sum(v == 0 for v in observed.values()),len(opposite),
                int(len(ri)==detected),int(len(ri)>=2),min(observed.values()),
                max(observed.values()),'; '.join(sorted(observed)),'; '.join(ri)])

    def write_csv(path, header, rows):
        with path.open('w', newline='', encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(header);w.writerows(rows)
    for end in ('GW','Lake'):
        write_csv(out/f'{end}_marker_candidates.csv',FIELDS,candidates[end])
        write_csv(out/f'{end}_marker_RI_at_least_2_samples.csv',FIELDS,
                  [r for r in candidates[end] if r[FIELDS.index('RI_le1_at_least_2_samples')]==1])
    write_csv(out/'all_formula_endpoint_comparison.csv',
              ['formula',*ELEMENTS,'GW_detected_samples','Lake_detected_samples',
               'GW_RI_le1_samples','Lake_RI_le1_samples'],comparison)

    selected = {end:{r[1] for r in candidates[end]} for end in candidates}
    detail_fields=['endpoint','sample','Mass','formula',*ELEMENTS,'transformation_count','RI_eq0','RI_le1']
    detail_files = {e:(out/f'{e}_candidate_sample_details.csv').open('w',newline='',encoding='utf-8-sig') for e in candidates}
    try:
        writers={e:csv.DictWriter(f,fieldnames=detail_fields,extrasaction='ignore') for e,f in detail_files.items()}
        for w in writers.values():w.writeheader()
        with source.open(newline='',encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['formula'] in selected[r['endpoint']]:writers[r['endpoint']].writerow(r)
    finally:
        for f in detail_files.values():f.close()

    book=xlsxwriter.Workbook(str(out/'Miyun_marker_candidates.xlsx'),{'constant_memory':True})
    fmt=book.add_format({'bold':True,'bg_color':'#245A81','font_color':'white'})
    for end in ('GW','Lake'):
        for title, rows in ((f'{end}_candidates',candidates[end]),
                            (f'{end}_RI_ge2',[r for r in candidates[end] if r[FIELDS.index('RI_le1_at_least_2_samples')]==1])):
            ws=book.add_worksheet(title);ws.freeze_panes(1,2)
            for j,v in enumerate(FIELDS):ws.write_string(0,j,v,fmt)
            for i,row in enumerate(rows,1):
                for j,v in enumerate(row):
                    if isinstance(v,str):ws.write_string(i,j,v)
                    else:ws.write_number(i,j,v)
            ws.autofilter(0,0,len(rows),len(FIELDS)-1);ws.set_column(0,1,22);ws.set_column(2,len(FIELDS)-3,18);ws.set_column(len(FIELDS)-2,len(FIELDS)-1,65)
    book.close()
    for end in ('GW','Lake'):
        print(end,'candidates',len(candidates[end]),'RI>=2',sum(r[FIELDS.index('RI_le1_at_least_2_samples')] for r in candidates[end]),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-peak',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();run(args.per_peak,args.output_dir)
