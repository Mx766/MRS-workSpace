"""
Word COM PDF 导入 — 利用 Word 内置 OCR 处理扫描件
"""
import os, sys, time
import pythoncom
import win32com.client

# 路径 — 可通过命令行参数覆盖
ROOT = os.path.dirname(os.path.dirname(__file__))
PDF = os.path.join(ROOT, 'original', 'Attachment2. Microbiologica.pdf')
OUT = os.path.join(ROOT, 'output', 'Attachment2_word_ocr.docx')
if len(sys.argv) > 1:
    PDF = sys.argv[1]
if len(sys.argv) > 2:
    OUT = sys.argv[2]

print(f'PDF: {PDF}')
print(f'Output: {OUT}')

# 初始化 COM
pythoncom.CoInitialize()
word = None

try:
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0  # 抑制所有对话框
    word.AutomationSecurity = 3  # msoAutomationSecurityForceDisable

    print('Opening PDF in Word...')
    doc = word.Documents.Open(
        PDF,
        ConfirmConversions=False,
        ReadOnly=True,
        Format='PDF Files',
        NoEncodingDialog=True
    )

    print(f'Opened: {doc.Name}, Pages: {doc.ComputeStatistics(2)}')  # 2=wdStatisticPages

    # 等待 OCR 完成（扫描件需要时间）
    print('Waiting for OCR to complete...')
    time.sleep(5)

    print('Saving as DOCX...')
    doc.SaveAs2(OUT, FileFormat=16)  # 16=wdFormatDocumentDefault
    doc.Close()
    print(f'Saved: {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)')

finally:
    if word:
        word.Quit()
    pythoncom.CoUninitialize()
