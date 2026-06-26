"""
测试讯飞 OCRforLLM API — PDF页面 → 图片 → OCR识别 → 结构化文本
"""
import os, sys, json, base64, hashlib, hmac, re
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time

# ── 用户凭证 ──
APPID = "8ede4f1c"
API_KEY = "9d13285ceb795178b78378c3c07ffa9e"
API_SECRET = "ZmVjYjM1ZTFjMjJhZmQwYzBjZTUzN2E1"

# ── OCRforLLM API 配置 ──
HTTP_HOST = "api.xf-yun.com"
HTTP_PATH = "/v1/private/se75ocrbm"
HTTP_URL = f"https://{HTTP_HOST}{HTTP_PATH}"

# ── HMAC-SHA256 签名（URL参数方式 + HTTP Header） ──
def build_auth(method="POST", host=None, path=None):
    """生成鉴权URL + HTTP Headers"""
    host = host or HTTP_HOST
    path = path or HTTP_PATH

    from datetime import datetime as dt, timezone
    now = dt.now(timezone.utc)
    date = format_date_time(now.timestamp())

    signature_origin = f"host: {host}\ndate: {date}\n{method} {path} HTTP/1.1"
    signature_sha = hmac.new(
        API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature_sha).decode('utf-8')

    authorization_origin = (
        f'api_key="{API_KEY}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature_b64}"'
    )
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

    # URL参数：authorization + host
    url_params = {
        "authorization": authorization,
        "host": host
    }
    auth_url = f"https://{host}{path}?{urlencode(url_params)}"

    # HTTP Headers：Date 必须与签名中的date一致
    headers = {
        "Date": date,
        "Content-Type": "application/json"
    }

    return auth_url, headers

# ── 调用 OCR API ──
import httpx

def ocr_image(image_base64: str, encoding="jpg"):
    """调用讯飞 OCRforLLM 识别单张图片"""
    auth_url, headers = build_auth("POST")

    body = {
        "header": {
            "app_id": APPID,
            "status": 0  # 0=开始
        },
        "parameter": {
            "ocr": {
                "result_option": "normal",
                "result_format": "json"
            }
        },
        "payload": {
            "image": {
                "encoding": encoding,
                "image": image_base64,
                "status": 0
            }
        }
    }

    print(f"URL: {auth_url[:120]}...")
    print(f"Headers: {headers}")
    resp = httpx.post(auth_url, headers=headers, json=body, timeout=60)
    print(f"HTTP {resp.status_code}")
    print(f"Response: {resp.text[:3000]}")
    return resp.json() if resp.status_code == 200 else resp.text

# ── PDF页面转图片 ──
import pymupdf

def pdf_page_to_image(pdf_path, page_num=0, dpi=200):
    """将PDF页面渲染为图片"""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    # 渲染到pixmap
    mat = pymupdf.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpg")
    doc.close()
    return base64.b64encode(img_bytes).decode('utf-8')

# ── 主测试 ──
if __name__ == "__main__":
    # 测试1: MSDS PDF 第一页
    msds_pdf = r"d:\translation\original\CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf"

    if os.path.exists(msds_pdf):
        print(f"Testing MSDS PDF (small): {msds_pdf}")
        img_b64 = pdf_page_to_image(msds_pdf, 0, dpi=100)  # 先用低DPI测试
        print(f"Image: {len(img_b64)} chars base64")

        try:
            result = ocr_image(img_b64, "jpg")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {msds_pdf}")
