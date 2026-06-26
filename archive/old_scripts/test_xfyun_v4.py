"""
测试讯飞 OCRforLLM API v4 — 不同Host
"""
import base64, hashlib, hmac, json, os
from datetime import datetime, timezone
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import httpx

cfg_path = os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')
with open(cfg_path) as f:
    cfg = json.load(f)
APPID = cfg['appid']
API_KEY = cfg['apikey']
API_SECRET = cfg['apisecret']

PATH = "/v1/private/se75ocrbm"

# 候选 hosts
HOSTS = [
    "api.xf-yun.com",
    "cbm01.cn-huabei-1.xf-yun.com",
    "cn-huabei-1.xf-yun.com",
    "ltm-cn-huabei-1.xf-yun.com",
]

def test_host(host):
    now = datetime.now(timezone.utc)
    date_str = format_date_time(now.timestamp())

    signature_origin = f"host: {host}\ndate: {date_str}\nPOST {PATH} HTTP/1.1"
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

    url_params = {"authorization": authorization, "host": host, "date": date_str}
    url = f"https://{host}{PATH}?{urlencode(url_params)}"

    headers = {"Date": date_str, "Content-Type": "application/json"}

    body = {
        "header": {"app_id": APPID, "status": 3},
        "parameter": {"ocr": {"result_option": "normal", "result_format": "json"}},
        "payload": {"image": {"encoding": "jpg", "image": "test", "status": 3}}
    }

    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=15)
        print(f"  Status: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

print("Testing OCRforLLM hosts...")
for host in HOSTS:
    print(f"\nHost: {host}")
    test_host(host)
