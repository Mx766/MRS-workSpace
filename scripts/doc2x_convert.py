"""
Doc2X PDF → DOCX 转换（免费 500 页/天，表格排版精准）
使用 pdfdeal SDK: pip install pdfdeal
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pdfdeal import Doc2X
from pathlib import Path


def convert_pdf_to_docx(pdf_path, api_key, output_path=None):
    """使用 Doc2X 将 PDF 转为 DOCX"""
    print(f'{"="*60}')
    print(f'Doc2X PDF → DOCX: {pdf_path}')
    print(f'{"="*60}')

    if output_path is None:
        output_dir = Path('output/toxicity')
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(pdf_path).stem
        output_path = str(output_dir)

    client = Doc2X(apikey=api_key, debug=True)

    print(f'  Converting...')
    success, failed, flag = client.pdf2file(
        pdf_file=str(Path(pdf_path).absolute()),
        output_path=output_path,
        output_format='docx',
    )

    if success:
        for f in success:
            size = os.path.getsize(f) / 1024 if os.path.exists(f) else 0
            print(f'  ✓ {f} ({size:.0f} KB)')
    if failed:
        for f, reason in failed.items():
            print(f'  ✗ {f}: {reason}')
    if flag:
        print(f'  ⚠ {flag}')

    return success, failed, flag


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Doc2X PDF → DOCX')
    ap.add_argument('input', help='输入 PDF 路径')
    ap.add_argument('-k', '--key', default=None, help='Doc2X API Key')
    ap.add_argument('-o', '--output', default=None)
    args = ap.parse_args()

    api_key = args.key or os.environ.get('DOC2X_API_KEY')
    if not api_key:
        print('Please provide API key with -k or set DOC2X_API_KEY env var')
        sys.exit(1)

    convert_pdf_to_docx(args.input, api_key, args.output)
