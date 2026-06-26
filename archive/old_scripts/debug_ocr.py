"""
调试讯飞OCR — 单页测试，打印完整请求响应
"""
import base64, hashlib, hmac, json, os
from datetime import datetime, timezone
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import httpx
import pymupdf

# 加载配置
with open(os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')) as f:
    cfg = json.load(f)

HOST = "cn-huabei-1.xf-yun.com"
PATH = "/v1/private/se75ocrbm"

def test_page(pdf_path, page_num=0, dpi=150):
    print(f"=" * 60)
    print(f"测试: {pdf_path}")
    print(f"页码: {page_num+1}, DPI: {dpi}")

    # 1. 渲染图片
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    mat = pymupdf.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpg")
    doc.close()
    img_b64 = base64.b64encode(img_bytes).decode()
    print(f"图片: {len(img_bytes)/1024:.0f} KB")

    # 2. 鉴权
    now = datetime.now(timezone.utc)
    date_str = format_date_time(now.timestamp())
    sig = f"host: {HOST}\ndate: {date_str}\nPOST {PATH} HTTP/1.1"
    sig_sha = hmac.new(cfg['apisecret'].encode(), sig.encode(), hashlib.sha256).digest()
    sig_b64 = base64.b64encode(sig_sha).decode()
    auth = f'api_key="{cfg["apikey"]}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig_b64}"'
    auth_b64 = base64.b64encode(auth.encode()).decode()

    url = f"https://{HOST}{PATH}?{urlencode({'authorization': auth_b64, 'host': HOST, 'date': date_str})}"
    headers = {"Date": date_str, "Content-Type": "application/json"}

    # 3. 请求 (status=2 一次性)
    body = {
        "header": {"app_id": cfg['appid'], "status": 2},
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

    print(f"\n请求URL: {url[:120]}...")
    print(f"请求body大小: {len(json.dumps(body))/1024:.0f} KB")

    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=120)
        print(f"\nHTTP状态码: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"响应长度: {len(resp.text)} 字符")

            # 打印header
            h = data.get('header', {})
            print(f"Header: code={h.get('code')}, message={h.get('message', '')}")

            # 打印payload结构
            p = data.get('payload', {})
            print(f"Payload keys: {list(p.keys())}")

            # 尝试提取文本
            for key in p:
                val = p[key]
                if isinstance(val, str) and len(val) > 0:
                    print(f"\n=== payload.{key} (前500字符) ===")
                    print(val[:500])
                elif isinstance(val, dict):
                    print(f"\n=== payload.{key} (dict, keys={list(val.keys())}) ===")
                    print(json.dumps(val, ensure_ascii=False, indent=2)[:1000])
                elif isinstance(val, list):
                    print(f"\n=== payload.{key} (list, length={len(val)}) ===")
                    if val:
                        first = val[0]
                        if isinstance(first, str):
                            print(first[:500])
                        else:
                            print(json.dumps(first, ensure_ascii=False, indent=2)[:500])

            # 保存完整响应
            out_path = 'output/ocr_debug_response.json'
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n完整响应已保存: {out_path}")

        else:
            print(f"错误响应: {resp.text[:1000]}")
            # 尝试解析错误
            try:
                err = resp.json()
                print(f"错误JSON: {json.dumps(err, ensure_ascii=False, indent=2)}")
            except:
                pass

    except Exception as e:
        print(f"连接错误: {e}")

# 测试
test_pdf = r"d:\translation\original\CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf"
if os.path.exists(test_pdf):
    test_page(test_pdf, 0, dpi=100)
else:
    print(f"文件不存在: {test_pdf}")
