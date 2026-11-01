"""Render the maintained public course catalog with the existing cloud renderer."""
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    results=[]
    for source in sorted((ROOT/'outputs/catalog').glob('*.md'),key=lambda p:p.name):
        subprocess.run([sys.executable,str(Path(__file__).with_name('cloud_render.py')),'--input',str(source)],cwd=ROOT,check=True)
        results.append(json.loads((ROOT/'render-result.json').read_text(encoding='utf-8')))
    if len(results)!=13: raise ValueError('课程目录数量不是13，请先检查产品索引')
    (ROOT/'render-catalog.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Catalog rendered:',len(results))

if __name__=='__main__': main()
