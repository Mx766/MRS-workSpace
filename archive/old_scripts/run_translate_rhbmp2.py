"""Translate rhBMP-2 PDF"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
from translate_pdf_v5 import translate_pdf
translate_pdf(
    'original/rhBMP-2 (DWP431) Repeat-Dose Toxicity_Rat_2 weeks.pdf',
    'original/rhBMP-2_中文版.pdf'
)
print('Done!')
