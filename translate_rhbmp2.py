"""翻译 rhBMP-2"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from config import load_config
from translator import translate_pdf

import argparse
cfg = load_config()
ROOT = os.path.dirname(__file__)
pdf = os.path.join(ROOT, 'original', 'rhBMP-2 (DWP431) Repeat-Dose Toxicity_Rat_2 weeks.pdf')
out = os.path.join(ROOT, 'output', 'toxicity', 'rhBMP-2_中文版_v2.pdf')
if len(sys.argv) > 1:
    pdf = sys.argv[1]
if len(sys.argv) > 2:
    out = sys.argv[2]

result, count = translate_pdf(pdf, out,
    api_key=cfg['api_key'],
    model=cfg['model'],
    base_url=cfg.get('base_url_override', ''),
    progress_callback=lambda p, msg: print(f'  [{p*100:.0f}%] {msg}')
)
print(f'\nDone: {result} ({count} replacements)')
