"""
调试讯飞PDF OCR — /v1/pdfOcr/start 接口
"""
import base64, hashlib, hmac, json, os
from datetime import datetime, timezone
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import httpx

with open(os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')) as f:
    cfg = json.load(f)

# 尝试多个可能的 Host
HOSTS = [
    "api.xf-yun.com",
    "webapi.xf-yun.com",
    "cn-huabei-1.xf-yun.com",
    "rest-api.xf-yun.com",
]

def test_pdf_ocr(host):
    path = "/v1/pdfOcr/start"
    now = datetime.now(timezone.utc)
    date_str = format_date_time(now.timestamp())

    sig = f"host: {host}\ndate: {date_str}\nPOST {path} HTTP/1.1"
    sig_sha = hmac.new(cfg['apisecret'].encode(), sig.encode(), hashlib.sha256).digest()
    sig_b64 = base64.b64encode(sig_sha).decode()
    auth = f'api_key="{cfg["apikey"]}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig_b64}"'
    auth_b64 = base64.b64encode(auth.encode()).decode()

    url = f"https://{host}{path}?{urlencode({'authorization': auth_b64, 'host': host, 'date': date_str})}"
    headers = {"Date": date_str, "Content-Type": "application/json"}

    # 最小测试body
    body = {
        "header": {"app_id": cfg['appid'], "status": 2},
        "parameter": {"ocr": {"result_option": "normal", "result_format": "json"}},
        "payload": {"pdf": {"encoding": "jpg", "image": "dGVzdA==", "status": 2}}  # "test" in base64
    }

    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=15)
        print(f"  {host}: {resp.status_code} - {resp.text[:200]}")
        if resp.status_code in (200, 400):
            return True
    except Exception as e:
        print(f"  {host}: 连接失败 - {e}")
    return False

print("测试 PDF OCR (/v1/pdfOcr/start) 接口...")
for host in HOSTS:
    test_pdf_ocr(host)
