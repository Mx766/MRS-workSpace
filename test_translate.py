"""测试翻译"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from config import load_config
from translator import translate_pdf

cfg = load_config()
print(f'Model: {cfg["model"]}, Key: {cfg["api_key"][:10]}...')

pdf = r'd:\translation\original\CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf'
out = r'd:\translation\output\test_direct\MSDS_中文版.pdf'

result, count = translate_pdf(pdf, out,
    api_key=cfg['api_key'],
    model=cfg['model'],
    base_url=cfg.get('base_url_override', ''),
    progress_callback=lambda p, msg: print(f'  [{p*100:.0f}%] {msg}')
)
print(f'Done: {result} ({count} replacements)')
