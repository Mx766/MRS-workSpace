"""
Run translation on original/[1].pdf
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from translate_pdf_final import translate_pdf

input_pdf = 'original/[1].pdf'
output_pdf = 'original/[1]_中文版.pdf'

print(f'Translating: {input_pdf} -> {output_pdf}')
translate_pdf(input_pdf, output_pdf)
print('Done!')
