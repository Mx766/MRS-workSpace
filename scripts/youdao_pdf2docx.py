"""
有道智云 PDF → DOCX 格式转换（高级版）
API: https://openapi.youdao.com/file_convert/v2

请求必须用 multipart/form-data，httpx 的 data= 是 form-encoded，
需要手动构建 multipart body。
"""
import sys, io, os, json, hashlib, time, base64, random, uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import httpx
from pathlib import Path

# API 密钥从环境变量读取（不再硬编码）
APP_KEY = os.environ.get('YOUDAO_APP_KEY', '')
APP_SECRET = os.environ.get('YOUDAO_APP_SECRET', '')
BASE_URL = 'https://openapi.youdao.com/file_convert/v2'


def make_sign(app_key, input_str, app_secret, salt=None, curtime=None):
    """生成有道 v3 签名 — salt/curtime 可传入以保持一致性"""
    if salt is None:
        salt = str(random.randint(100000, 999999))
    if curtime is None:
        curtime = str(int(time.time()))

    if len(input_str) <= 20:
        inp = input_str
    else:
        inp = input_str[:10] + str(len(input_str)) + input_str[-10:]

    sign_str = app_key + inp + salt + curtime + app_secret
    sign = hashlib.sha256(sign_str.encode()).hexdigest()
    return salt, curtime, sign


def _build_multipart(fields):
    """手动构建 multipart/form-data body"""
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
    body = b''
    for name, value in fields.items():
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += value.encode() if isinstance(value, str) else value
        body += b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    content_type = f'multipart/form-data; boundary={boundary}'
    return body, content_type


def upload_pdf(pdf_path):
    """上传 PDF，返回 flownumber"""
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    q = base64.b64encode(pdf_bytes).decode()
    file_name = Path(pdf_path).name

    print(f'  File: {file_name}')
    print(f'  Original: {len(pdf_bytes)/1024:.0f} KB → Base64: {len(q)/1024:.0f} KB')

    if len(q) > 40 * 1024 * 1024:
        print(f'  ERROR: Base64 size {len(q)/1024/1024:.1f}MB exceeds 40MB limit')
        return None

    salt, curtime, sign = make_sign(APP_KEY, q, APP_SECRET)

    body, ct = _build_multipart({
        'appKey': APP_KEY,
        'salt': salt,
        'curtime': curtime,
        'sign': sign,
        'signType': 'v3',
        'q': q,
        'fileName': file_name,
        'fileType': 'pdf',
        'targetFileType': 'docx',
    })

    resp = httpx.post(
        f'{BASE_URL}/upload',
        content=body,
        headers={'Content-Type': ct},
        timeout=120
    )
    data = resp.json()
    if data.get('successful'):
        flownumber = data['data']['flownumber']
        print(f'  ✓ Uploaded, flownumber: {flownumber}')
        return flownumber
    else:
        print(f'  ✗ Upload failed: {data}')
        return None


def query_task(flownumber, max_wait=300):
    """轮询任务状态，返回下载 URL"""
    print(f'  Polling task {flownumber}...', end=' ', flush=True)
    waited = 0

    while waited < max_wait:
        salt = str(random.randint(100000, 999999))
        curtime = str(int(time.time()))
        _, _, sign = make_sign(APP_KEY, flownumber, APP_SECRET, salt=salt, curtime=curtime)

        body, ct = _build_multipart({
            'appKey': APP_KEY,
            'salt': salt,
            'curtime': curtime,
            'sign': sign,
            'signType': 'v3',
            'flownumber': flownumber,
        })

        resp = httpx.post(
            f'{BASE_URL}/query',
            content=body,
            headers={'Content-Type': ct},
            timeout=30
        )
        data = resp.json()
        if not data.get('successful'):
            print(f'\n  ✗ Query error: {data}')
            return None

        d = data['data']
        status = d['status']
        if status == 4:
            url = d['resultUrl']
            print(f'done!')
            return url
        elif status == -2:
            print(f'failed: {d.get("statusString")}')
            return None
        else:
            print(f'{d.get("statusString", status)}...', end=' ', flush=True)
            time.sleep(5)
            waited += 5

    print(f'timeout')
    return None


def convert_pdf_to_docx(pdf_path, output_path=None):
    """PDF → DOCX，返回输出路径"""
    print(f'\n{"="*60}')
    print(f'PDF → DOCX: {pdf_path}')
    print(f'{"="*60}')

    flownumber = upload_pdf(pdf_path)
    if not flownumber:
        return None

    result_url = query_task(flownumber)
    if not result_url:
        return None

    # Download result
    print(f'  Downloading: {result_url[:80]}...')
    resp = httpx.get(result_url, timeout=120)
    if resp.status_code != 200:
        print(f'  ✗ Download failed: HTTP {resp.status_code}')
        return None

    if output_path is None:
        output_dir = Path('output/toxicity')
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(pdf_path).stem
        output_path = output_dir / f'{stem}.docx'

    with open(output_path, 'wb') as f:
        f.write(resp.content)

    size_kb = len(resp.content) / 1024
    print(f'  ✓ Saved: {output_path} ({size_kb:.0f} KB)')
    return str(output_path)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='有道 PDF → DOCX 转换')
    ap.add_argument('input', help='输入 PDF')
    ap.add_argument('-o', '--output', default=None)
    args = ap.parse_args()

    result = convert_pdf_to_docx(args.input, args.output)
    if result:
        print(f'\nDone! → {result}')
    else:
        print('\nFailed!')
        sys.exit(1)
