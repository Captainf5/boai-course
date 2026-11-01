#!/usr/bin/env python3
"""轻量表格体检。CSV/TSV零依赖；XLSX用标准库读取首个工作表的基础值。"""
import csv, json, sys, zipfile, re
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def profile_rows(rows):
    if not rows: return {"rows":0,"cols":0}
    header = [str(x) if x is not None else "" for x in rows[0]]
    data = rows[1:]
    width = max(len(header), max((len(r) for r in data), default=0))
    header += [f"COL_{i+1}" for i in range(len(header), width)]
    norm = [(list(r)+[None]*width)[:width] for r in data]
    missing = {header[i]: sum(1 for r in norm if r[i] in (None, "")) for i in range(width)}
    serial = [json.dumps(r, ensure_ascii=False, default=str) for r in norm]
    dup_count = len(serial) - len(set(serial))
    samples = {header[i]: [r[i] for r in norm if r[i] not in (None, "")][:5] for i in range(width)}
    return {"rows":len(norm),"cols":width,"headers":header,"missing":missing,"duplicate_rows":dup_count,"samples":samples}

def read_csv(path):
    delim = "\t" if path.suffix.lower()==".tsv" else ","
    for enc in ("utf-8-sig","utf-8","gb18030"):
        try:
            with path.open("r",encoding=enc,newline="") as f: return list(csv.reader(f, delimiter=delim))
        except UnicodeDecodeError: pass
    raise ValueError("无法识别CSV编码")

def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n=0
    for ch in letters: n=n*26+ord(ch)-64
    return n-1

def read_xlsx_first_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si",NS):
                texts=[t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
                shared.append("".join(texts))
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        first=wb.find("m:sheets/m:sheet",NS)
        rid=first.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target=None
        for rel in rels:
            if rel.attrib.get("Id")==rid: target=rel.attrib["Target"]
        sheet_path="xl/"+target.lstrip("/") if not target.startswith("xl/") else target
        root=ET.fromstring(z.read(sheet_path))
        rows=[]
        for row in root.findall(".//m:sheetData/m:row",NS):
            vals={}
            maxc=-1
            for c in row.findall("m:c",NS):
                idx=col_index(c.attrib["r"]); maxc=max(maxc,idx)
                t=c.attrib.get("t"); v=c.find("m:v",NS); val=None if v is None else v.text
                if t=="s" and val is not None: val=shared[int(val)]
                elif t=="inlineStr":
                    ts=[x.text or "" for x in c.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]; val="".join(ts)
                vals[idx]=val
            arr=[None]*(maxc+1 if maxc>=0 else 0)
            for i,v in vals.items(): arr[i]=v
            rows.append(arr)
        return rows

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: profile_tabular.py file.csv|file.tsv|file.xlsx")
    p=Path(sys.argv[1]); ext=p.suffix.lower()
    rows=read_csv(p) if ext in (".csv",".tsv") else read_xlsx_first_sheet(p) if ext==".xlsx" else None
    if rows is None: raise SystemExit("当前支持 csv/tsv/xlsx")
    print(json.dumps(profile_rows(rows),ensure_ascii=False,indent=2,default=str))
if __name__=="__main__": main()
