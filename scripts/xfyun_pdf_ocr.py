"""
讯飞 PDF文档识别(OCR大模型) — 直接传PDF，返回Word文件
API文档: https://www.xfyun.cn/doc/words/pdfOcr/API.html
"""
import hashlib, hmac, base64, json, os, sys, time
import httpx

# ═══════════════════════════════════════
# 配置 — 优先环境变量，回退到配置文件
# ═══════════════════════════════════════
APPID = os.environ.get('XFYUN_APPID', '')
API_SECRET = os.environ.get('XFYUN_APISECRET', '')
if not APPID or not API_SECRET:
    # 回退到旧配置文件（仅兼容，不建议使用）
    cfg_path = os.path.join(os.path.dirname(__file__), '..', 'xfyun_config.json')
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        APPID = APPID or cfg.get('appid', '')
        API_SECRET = API_SECRET or cfg.get('apisecret', '')

BASE_URL = "https://iocr.xfyun.cn/ocrzdq"

# ═══════════════════════════════════════
# 鉴权 (MD5 + HMAC-SHA1，与之前的HMAC-SHA256不同!)
# ═══════════════════════════════════════
def get_signature(app_id, api_secret, timestamp):
    """PDF OCR专用签名: HMAC-SHA1( MD5(appId+timestamp), apiSecret )"""
    auth = hashlib.md5((app_id + str(timestamp)).encode()).hexdigest()
    sig = hmac.new(api_secret.encode(), auth.encode(), hashlib.sha1).digest()
    return base64.b64encode(sig).decode()

def build_headers():
    """构建请求头"""
    ts = str(int(time.time()))
    sig = get_signature(APPID, API_SECRET, ts)
    return {
        "appId": APPID,
        "timestamp": ts,
        "signature": sig
    }

# ═══════════════════════════════════════
# API 调用
# ═══════════════════════════════════════
def start_pdf_ocr(pdf_path, export_format="word"):
    """
    上传PDF开始OCR识别
    返回: taskNo (任务编号)
    """
    print(f"上传PDF: {pdf_path}")
    print(f"文件大小: {os.path.getsize(pdf_path)/1024:.0f} KB")

    headers = build_headers()

    # multipart/form-data 上传
    with open(pdf_path, 'rb') as f:
        files = {
            'file': (os.path.basename(pdf_path), f, 'application/pdf')
        }
        data = {
            'fileName': os.path.basename(pdf_path),
            'exportFormat': export_format
        }

        resp = httpx.post(
            f"{BASE_URL}/v1/pdfOcr/start",
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    print(f"HTTP {resp.status_code}")
    result = resp.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")

    if result.get('code') != 0:
        print(f"错误: {result.get('desc')}")
        return None

    task_no = result['data']['taskNo']
    print(f"任务编号: {task_no}")
    return task_no

def check_status(task_no):
    """查询OCR任务状态"""
    headers = build_headers()
    resp = httpx.get(
        f"{BASE_URL}/v1/pdfOcr/status",
        headers=headers,
        params={'taskNo': task_no},
        timeout=30
    )
    return resp.json()

def wait_for_result(task_no, poll_interval=5, max_wait=600):
    """
    轮询等待OCR完成
    返回: 下载URL
    """
    start_time = time.time()
    while time.time() - start_time < max_wait:
        result = check_status(task_no)
        status = result.get('data', {}).get('status', '')
        tip = result.get('data', {}).get('tip', '')

        print(f"  状态: {status} - {tip}")

        if status == 'FINISH':
            down_url = result['data'].get('downUrl')
            print(f"  完成! 下载地址: {down_url}")
            return down_url
        elif status in ('FAILED', 'ERROR'):
            print(f"  失败: {result}")
            return None

        time.sleep(poll_interval)

    print(f"超时 ({max_wait}s)")
    return None

def download_result(down_url, output_path):
    """下载OCR结果Word文件"""
    print(f"下载: {down_url}")
    resp = httpx.get(down_url, timeout=120, follow_redirects=True)
    if resp.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        print(f"保存: {output_path} ({len(resp.content)/1024:.0f} KB)")
        return output_path
    else:
        print(f"下载失败: HTTP {resp.status_code}")
        return None

# ═══════════════════════════════════════
# 主流程
# ═══════════════════════════════════════
def pdf_to_word(pdf_path, output_dir=None, export_format="word"):
    """
    PDF → 讯飞 PDF OCR → Word 文件

    参数:
        pdf_path: PDF文件路径
        output_dir: 输出目录 (默认: PDF所在目录)
        export_format: 导出格式 "word" 或 "txt"
    返回: 输出Word文件路径
    """
    print("=" * 60)
    print(f"讯飞 PDF文档识别 (OCR大模型)")
    print(f"输入: {pdf_path}")
    print("=" * 60)

    # Step 1: 上传PDF
    task_no = start_pdf_ocr(pdf_path, export_format)
    if not task_no:
        return None

    # Step 2: 等待完成
    print("\n等待OCR处理...")
    down_url = wait_for_result(task_no)
    if not down_url:
        return None

    # Step 3: 下载结果
    if output_dir is None:
        output_dir = os.path.dirname(pdf_path) or '.'

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    ext = ".docx" if export_format == "word" else ".txt"
    output_path = os.path.join(output_dir, base_name + "_xfyun" + ext)

    result = download_result(down_url, output_path)
    return result

# ═══════════════════════════════════════
if __name__ == "__main__":
    # 默认测试: MSDS PDF
    root_dir = os.path.dirname(os.path.dirname(__file__))
    default_pdf = os.path.join(root_dir, 'original', 'CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf')

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    elif os.path.exists(default_pdf):
        pdf_path = default_pdf
    else:
        print("用法: python xfyun_pdf_ocr.py <pdf_path>")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    result = pdf_to_word(pdf_path)
    if result:
        print(f"\n✅ 成功! 输出文件: {result}")
    else:
        print(f"\n❌ 失败!")
