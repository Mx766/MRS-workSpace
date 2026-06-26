"""
测试讯飞 OCRforLLM API — 多种鉴权方式
读取配置: xfyun_config.json
"""
import base64, hashlib, hmac, json, os
from datetime import datetime, timezone
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import httpx

# 加载配置
cfg_path = os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')
with open(cfg_path) as f:
    cfg = json.load(f)
APPID = cfg['appid']
API_KEY = cfg['apikey']
API_SECRET = cfg['apisecret']

HOST = "api.xf-yun.com"
PATH = "/v1/private/se75ocrbm"
BASE_URL = f"https://{HOST}{PATH}"

def test_auth_method(method="GET", date_in_url=True, extra_headers=True):
    now = datetime.now(timezone.utc)
    date_str = format_date_time(now.timestamp())

    signature_origin = f"host: {HOST}\ndate: {date_str}\n{method} {PATH} HTTP/1.1"
    print(f"\n=== Testing {method}, date_in_url={date_in_url}, extra_headers={extra_headers} ===")
    print(f"Signature origin:\n{signature_origin}")

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

    url_params = {"authorization": authorization, "host": HOST}
    if date_in_url:
        url_params["date"] = date_str
    url = f"{BASE_URL}?{urlencode(url_params)}"

    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers["Date"] = date_str

    if method == "GET":
        resp = httpx.get(url, headers=headers, timeout=30)
    else:
        body = {
            "header": {"app_id": APPID, "status": 3},
            "parameter": {"ocr": {"result_option": "normal", "result_format": "json"}},
            "payload": {"image": {"encoding": "jpg", "image": "test", "status": 3}}
        }
        resp = httpx.post(url, headers=headers, json=body, timeout=30)

    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
    return resp

print("=" * 60)
print("Test 1: GET, date in URL only")
test_auth_method("GET", date_in_url=True, extra_headers=False)

print("\n" + "=" * 60)
print("Test 2: GET, date in URL + Date header")
test_auth_method("GET", date_in_url=True, extra_headers=True)

print("\n" + "=" * 60)
print("Test 3: POST, date in URL + Date header")
test_auth_method("POST", date_in_url=True, extra_headers=True)
