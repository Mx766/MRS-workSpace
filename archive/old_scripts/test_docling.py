"""Docling — 拆单页处理，跳过问题页"""
import sys, io, os, subprocess, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
import pymupdf

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'original/rhBMP-2 (DWP431) Repeat-Dose Toxicity_Rat_2 weeks.pdf'
out_dir = Path('output/toxicity')
out_dir.mkdir(parents=True, exist_ok=True)
stem = Path(pdf_path).stem

src = pymupdf.open(pdf_path)
total = len(src)
print(f'Pages: {total}')

# Split into single-page PDFs
tmpdir = Path(tempfile.gettempdir()) / 'docling_split'
tmpdir.mkdir(parents=True, exist_ok=True)

page_files = []
for i in range(total):
    p = tmpdir / f'p{i+1:04d}.pdf'
    doc = pymupdf.open()
    doc.insert_pdf(src, from_page=i, to_page=i)
    doc.save(str(p))
    doc.close()
    page_files.append(p)
src.close()

# Process each page via subprocess to isolate memory
ok = 0
bad = []
all_md = []

script = '''
import sys, os
os.environ['OMP_NUM_THREADS'] = '1'
from docling.document_converter import DocumentConverter
try:
    r = DocumentConverter().convert(sys.argv[1])
    md = r.document.export_to_markdown()
    print(md, end='')
except Exception as e:
    print(f'ERROR:{e}', file=sys.stderr)
    sys.exit(1)
'''

script_path = tmpdir / '_worker.py'
script_path.write_text(script, encoding='utf-8')

for idx, pf in enumerate(page_files):
    if (idx + 1) % 10 == 0:
        print(f'  {idx+1}/{total}...', flush=True)
    try:
        r = subprocess.run(
            [sys.executable, str(script_path), str(pf)],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, 'OMP_NUM_THREADS': '1'}
        )
        if r.returncode == 0:
            all_md.append(r.stdout.strip())
            ok += 1
        else:
            all_md.append(f'[PAGE {idx+1} FAILED: {r.stderr.strip()}]')
            bad.append(idx+1)
    except subprocess.TimeoutExpired:
        all_md.append(f'[PAGE {idx+1} TIMEOUT]')
        bad.append(idx+1)

# Clean up page files
for pf in page_files:
    try: pf.unlink()
    except: pass

# Save
md_path = out_dir / f'{stem}_docling.md'
full_md = '\n\n--- PAGE BREAK ---\n\n'.join(all_md)
md_path.write_text(full_md, encoding='utf-8')
print(f'\nOK: {ok}/{total}  Failed: {bad}')
print(f'Saved: {md_path} ({len(full_md)} chars)')
