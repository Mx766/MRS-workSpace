"""
MSDS PDF 完整翻译 — API翻译所有文字 + 保留背景色 + 原位覆写
"""
import sys, io, json, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymupdf
import httpx

# API 配置
API_KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.deepseek.com/anthropic')

# 缓存
CACHE_FILE = r'd:\translation\cache\msds_translation_cache.json'
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

def translate_batch(texts):
    """批量翻译文本列表"""
    # 去重 + 过滤
    to_translate = []
    for t in texts:
        if not t or not t.strip():
            continue
        key = hashlib.md5(t.encode()).hexdigest()[:12]
        if key not in cache:
            to_translate.append((key, t))

    if not to_translate:
        return cache

    # 合并为批量翻译请求
    combined = "\n---SEPARATOR---\n".join([t for _, t in to_translate])

    try:
        resp = httpx.post(
            f"{BASE_URL}/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "deepseek-v4-pro",
                "max_tokens": 8192,
                "temperature": 0.1,
                "system": (
                    "你是专业化工翻译。将每条英文翻译为简体中文。"
                    "规则：1)保留产品名/代码/数字/CAS号原样 2)专业术语准确 "
                    "3)每条译文一行，用'---SEPARATOR---'分隔 4)不输出原文"
                ),
                "messages": [{"role": "user", "content": f"翻译以下{len(to_translate)}条MSDS文本（用'---SEPARATOR---'分隔）：\n\n{combined}"}]
            },
            timeout=120
        )
        data = resp.json()
        if 'content' in data:
            results = data['content'][0]['text'].strip().split('---SEPARATOR---')
            for (key, _), zh in zip(to_translate, results):
                cache[key] = zh.strip()
        else:
            print(f"API error: {data.get('error', {}).get('message', 'unknown')}")
    except Exception as e:
        print(f"API error: {e}")
        # API失败时用原文
        for key, t in to_translate:
            cache[key] = t

    # 保存缓存
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

    return cache

def get_key(text):
    return hashlib.md5(text.strip().encode()).hexdigest()[:12]

def translate_pdf(pdf_path, output_path):
    doc = pymupdf.open(pdf_path)

    # ==== 第1步：收集所有待翻译文本 ====
    all_texts = set()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    t = span["text"].strip()
                    if t and len(t) > 1:
                        all_texts.add(t)

    print(f'Collected {len(all_texts)} unique text spans')

    # ==== 第2步：API批量翻译 ====
    text_list = sorted(all_texts, key=len, reverse=True)
    translate_batch(text_list)
    print(f'Translation cache: {len(cache)} entries')

    # ==== 第3步：写回PDF ====
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=30)  # 低分辨率用于采样背景色
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or len(text) <= 1:
                        continue

                    key = get_key(text)
                    zh = cache.get(key)
                    if not zh or zh == text:
                        continue  # 跳过无翻译的

                    bbox = span["bbox"]
                    x0, y0, x1, y1 = bbox
                    font_size = span["size"]
                    font_color = span["color"]

                    # 采样背景色 (取文本周围/中间的像素)
                    cx = int((x0 + x1) / 2)
                    cy = int((y0 + y1) / 2)
                    try:
                        sample_x = min(max(int(x0 - 2), 0), pix.width - 1)
                        sample_y = min(max(cy, 0), pix.height - 1)
                        # 转换坐标
                        scale_x = page.rect.width / pix.width
                        scale_y = page.rect.height / pix.height
                        px = int(sample_x / scale_x) if scale_x else sample_x
                        py = int(sample_y / scale_y) if scale_y else sample_y
                        bg_sample = pix.pixel(sample_x, sample_y)
                        bg_color = bg_sample  # (r, g, b)
                    except:
                        bg_color = (255, 255, 255)  # 默认白色

                    # 计算中文合适的字体大小
                    ratio = len(zh) / len(text)
                    adj_size = font_size * min(0.95, 1.0 / max(ratio * 0.7, 0.5))
                    adj_size = max(7, min(adj_size, font_size + 2))

                    # 用背景色覆盖原文
                    bg_rect = pymupdf.Rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
                    shape = page.new_shape()
                    shape.draw_rect(bg_rect)
                    shape.finish(
                        fill=pymupdf.sRGB_to_pdf(bg_color[0], bg_color[1], bg_color[2]),
                        color=None,
                        width=0
                    )
                    shape.commit()

                    # 插入中文
                    try:
                        page.insert_text(
                            (x0, y1 - font_size * 0.2),
                            zh,
                            fontname="china-s",
                            fontsize=adj_size,
                            color=pymupdf.sRGB_to_pdf(font_color),
                        )
                    except:
                        page.insert_text(
                            (x0, y1 - font_size * 0.2),
                            zh,
                            fontname="helv",
                            fontsize=adj_size,
                            color=pymupdf.sRGB_to_pdf(font_color),
                        )

        print(f'  Page {page_num+1}/{len(doc)} done')

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    translated = sum(1 for v in cache.values() if v != cache.get(get_key(k), k))
    print(f'\nSaved: {output_path}')
    print(f'Cache size: {len(cache)} entries')

if __name__ == '__main__':
    pdf = r"d:\translation\original\CH2.4.1(4-2) 1. MSDS_Barrel_TOPAS MSDS-EN V8.00_0 (2).pdf"
    output = r"d:\translation\output\MSDS_TOPAS_中文版_v2.pdf"
    translate_pdf(pdf, output)
