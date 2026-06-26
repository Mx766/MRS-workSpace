"""
讯飞 OCRforLLM 真实图片OCR测试
"""
import base64, hashlib, hmac, json, os, sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import httpx
import pymupdf

cfg_path = os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')
with open(cfg_path) as f:
    cfg = json.load(f)
APPID = cfg['appid']
API_KEY = cfg['apikey']
API_SECRET = cfg['apisecret']

HOST = "cn-huabei-1.xf-yun.com"
PATH = "/v1/private/se75ocrbm"

def ocr_page(pdf_path, page_num=0, dpi=150):
    """PDF单页→图片→OCR识别"""
    # 1. PDF页面转图片
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    mat = pymupdf.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpg")
    doc.close()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    print(f"Page {page_num+1}: {len(img_bytes)/1024:.0f}KB image, {len(img_b64)} chars base64")

    # 2. 鉴权
    now = datetime.now(timezone.utc)
    date_str = format_date_time(now.timestamp())
    sig_origin = f"host: {HOST}\ndate: {date_str}\nPOST {PATH} HTTP/1.1"
    sig_sha = hmac.new(API_SECRET.encode(), sig_origin.encode(), hashlib.sha256).digest()
    sig_b64 = base64.b64encode(sig_sha).decode()
    auth_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig_b64}"'
    auth = base64.b64encode(auth_origin.encode()).decode()
    url = f"https://{HOST}{PATH}?{urlencode({'authorization': auth, 'host': HOST, 'date': date_str})}"
    headers = {"Date": date_str, "Content-Type": "application/json"}

    # 3. 发送OCR请求
    body = {
        "header": {"app_id": APPID, "status": 2},  # status=2: 一次性完整请求
        "parameter": {
            "ocr": {
                "result_option": "normal",
                "result_format": "json"
            }
        },
        "payload": {
            "image": {
                "encoding": "jpg",
                "image": img_b64,
                "status": 2
            }
        }
    }

    print(f"Sending OCR request... (image size: {len(img_b64)} chars)")
    resp = httpx.post(url, headers=headers, json=body, timeout=120)
    print(f"HTTP {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print(f"Header: {json.dumps(result.get('header', {}), ensure_ascii=False, indent=2)}")

        payload = result.get('payload', {})
        # Try different response field names
        for key in ['ocr_output', 'result', 'text', 'content', 'data']:
            if key in payload:
                print(f"\n=== payload.{key} ===")
                val = payload[key]
                if isinstance(val, str):
                    print(val[:2000])
                else:
                    print(json.dumps(val, ensure_ascii=False, indent=2)[:2000])

        # Print full payload keys
        print(f"\nPayload keys: {list(payload.keys())}")

        # Save raw response
        with open('output/xfyun_ocr_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("Saved: output/xfyun_ocr_result.json")
        return result
    else:
        print(f"Error: {resp.text[:500]}")
        return None

# ── 测试 ──
if __name__ == "__main__":
    msds = r"d:\translation\original\CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf"
    if os.path.exists(msds):
        print(f"Testing: {msds}")
        ocr_page(msds, 0, dpi=120)
    else:
        print(f"Not found: {msds}")
