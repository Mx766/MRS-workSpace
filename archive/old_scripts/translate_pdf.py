"""
PDF 原位翻译工具 v3 — 保留格式 + API驱动 + 可复用
用法:
  python translate_pdf.py input.pdf -o output.pdf --lang-in en --lang-out zh
"""
import sys, io, json, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymupdf
import httpx

# ── API 配置（从环境变量读取，不硬编码密钥） ──
API_KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN', os.environ.get('DEEPSEEK_API_KEY', ''))
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.deepseek.com/anthropic')

# ── 翻译缓存 ──
def load_cache(cache_path):
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache_path, cache):
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

def text_key(text):
    return hashlib.md5(text.strip().encode()).hexdigest()[:12]

def translate_batch(texts, lang_in='en', lang_out='zh', cache=None):
    """批量翻译 — 调用 Anthropic 兼容 API"""
    if cache is None:
        cache = {}

    # 去重，找出未翻译的
    pending = []
    for t in set(texts):
        t = t.strip()
        if not t or len(t) <= 1:
            continue
        k = text_key(t)
        if k not in cache:
            pending.append((k, t))

    if not pending:
        return cache

    # 分批翻译（每批最多60条，避免分隔符混乱）
    BATCH_SIZE = 60
    separator = '\n<<<SEP>>>\n'

    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start:batch_start + BATCH_SIZE]
        print(f'  Translating batch {batch_start//BATCH_SIZE + 1}: {len(batch)} texts via API...')

        combined = separator.join([t for _, t in batch])

        try:
            resp = httpx.post(
                f'{BASE_URL}/v1/messages',
                headers={
                    'x-api-key': API_KEY,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                },
                json={
                    'model': os.environ.get('ANTHROPIC_MODEL', 'deepseek-chat'),
                    'max_tokens': 8192,
                    'temperature': 0.1,
                    'system': f'你是专业翻译引擎。将以下{len(batch)}条文本逐条从{lang_in}翻译为{lang_out}。每条译文用"<<<SEP>>>"分隔。只输出译文不输出原文不解释。保留数字/代码/公式。',
                    'messages': [{'role': 'user', 'content': combined}]
                },
                timeout=300
            )
            data = resp.json()

            if 'content' in data and isinstance(data['content'], list):
                text_blocks = [b for b in data['content'] if b.get('type') == 'text']
                if text_blocks:
                    raw = text_blocks[0].get('text', '')
                    results = [r.strip() for r in raw.split(separator)]
                    matched = 0
                    for (k, src), zh in zip(batch, results):
                        if zh and zh.strip() != src.strip():
                            cache[k] = zh.strip()
                            matched += 1
                    print(f'    Got {matched}/{len(batch)} translations')
                else:
                    types = [b.get('type') for b in data['content']]
                    print(f'    No text block, content types: {types}')
            else:
                print(f'    API error: {json.dumps(data, ensure_ascii=False)[:200]}')
        except Exception as e:
            print(f'    API exception: {e}')

    # 回退：未翻译的保留原文
    for k, t in pending:
        if k not in cache:
            cache[k] = t

    return cache


def sample_bg_color(page, bbox):
    """采样文本周围背景色，返回整数RGB值"""
    try:
        x0, y0, x1, y1 = bbox
        clip = pymupdf.Rect(x0-2, y0-2, x1+2, y1+2)
        pix = page.get_pixmap(dpi=30, clip=clip)
        samples = pix.samples
        if len(samples) >= 3:
            r, g, b = samples[0], samples[1], samples[2]
            return (r << 16) | (g << 8) | b
    except:
        pass
    return 0xFFFFFF  # 默认白色


def translate_pdf(input_path, output_path, lang_in='en', lang_out='zh', cache_path=None, use_dict=False):
    """
    PDF 原位翻译主函数
    - 提取所有文本块
    - API 批量翻译
    - 用背景色覆盖原文后插入译文
    """
    print(f'Opening: {input_path}')
    doc = pymupdf.open(input_path)

    if cache_path is None:
        cache_path = input_path.rsplit('.', 1)[0] + '_translation_cache.json'

    cache = load_cache(cache_path)

    # ── 第1步：收集所有文本 ──
    all_texts = set()
    for page in doc:
        blocks = page.get_text('dict')['blocks']
        for b in blocks:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                for s in l['spans']:
                    t = s['text'].strip()
                    if t and len(t) > 1:
                        all_texts.add(t)

    print(f'Found {len(all_texts)} unique text spans')

    # ── 第2步：翻译（字典模式跳过API） ──
    if use_dict:
        # 字典模式：只使用预定义翻译
        missing = [t for t in all_texts if text_key(t) not in cache]
        if missing:
            print(f'  Dict mode: {len(missing)} texts not in dictionary, keeping original')
            for t in missing:
                cache[text_key(t)] = t  # 未匹配的保留原文
    else:
        # API 模式：调用翻译
        cache = translate_batch(list(all_texts), lang_in, lang_out, cache)
        save_cache(cache_path, cache)

    # ── 第3步：写回 PDF ──
    pixmap_cache = {}  # 缓存页面像素图
    replaced = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text('dict')['blocks']

        for b in blocks:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                for s in l['spans']:
                    text = s['text'].strip()
                    if not text or len(text) <= 1:
                        continue

                    k = text_key(text)
                    zh = cache.get(k)
                    if not zh or zh == text:
                        continue  # 跳过未翻译或无变化的

                    bbox = s['bbox']
                    font_size = s['size']
                    font_color = s['color']

                    # 计算中文字号
                    ratio = len(zh) / max(len(text), 1)
                    adj_size = font_size * min(0.95, 1.0 / max(ratio * 0.65, 0.45))
                    adj_size = max(6.5, min(adj_size, font_size + 1))

                    # 采样背景色并覆盖原文
                    bg = sample_bg_color(page, bbox)
                    cover_rect = pymupdf.Rect(bbox[0]-1, bbox[1]-1, bbox[2]+1, bbox[3]+1)
                    shape = page.new_shape()
                    shape.draw_rect(cover_rect)
                    fill_color = pymupdf.sRGB_to_pdf(bg)
                    shape.finish(fill=fill_color, color=None, width=0)
                    shape.commit()

                    # 插入中文
                    try:
                        page.insert_text(
                            (bbox[0], bbox[3] - font_size * 0.2),
                            zh,
                            fontname='china-s',
                            fontsize=adj_size,
                            color=pymupdf.sRGB_to_pdf(font_color),
                        )
                        replaced += 1
                    except Exception as e:
                        pass

        print(f'  Page {page_num+1}/{len(doc)} done ({replaced} replaced)')

    # ── 保存 ──
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f'\nSaved: {output_path}')
    print(f'Replaced {replaced} text spans with translations')
    return output_path


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='PDF原位翻译 — 保留原版格式')
    ap.add_argument('input', help='输入PDF文件')
    ap.add_argument('-o', '--output', help='输出PDF路径', default=None)
    ap.add_argument('--lang-in', default='en', help='源语言 (default: en)')
    ap.add_argument('--lang-out', default='zh', help='目标语言 (default: zh)')
    ap.add_argument('--cache', help='翻译缓存JSON路径', default=None)
    ap.add_argument('--use-dict', help='使用预定义翻译字典JSON (跳过API)', default=None)
    args = ap.parse_args()

    if not args.output:
        base = os.path.splitext(args.input)[0]
        args.output = f'{base}_中文版.pdf'

    # 如果提供了预定义字典，直接用那个
    if args.use_dict:
        print(f'Using pre-defined dictionary: {args.use_dict}')
        cache = load_cache(args.use_dict)
        # 转换为 key → zh 格式
        new_cache = {}
        for en, zh in cache.items():
            new_cache[text_key(en)] = zh
        args.cache = args.cache or args.input.rsplit('.', 1)[0] + '_translation_cache.json'
        save_cache(args.cache, new_cache)

    translate_pdf(args.input, args.output, args.lang_in, args.lang_out, args.cache, use_dict=bool(args.use_dict))
