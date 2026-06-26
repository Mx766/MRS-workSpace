"""
PDF 翻译 v4 — API完整翻译 + 无填充覆写（保留背景色/阴影）+ 可靠分批
用法: python translate_pdf_final.py input.pdf -o output.pdf
"""
import sys, io, json, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymupdf
import httpx
from tqdm import tqdm

API_KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.deepseek.com/anthropic')
MODEL = os.environ.get('ANTHROPIC_MODEL', 'deepseek-v4-flash')

def text_key(text):
    return hashlib.md5(text.strip().encode()).hexdigest()[:12]

def load_cache(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(path, cache):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

def api_translate(texts, lang_in='en', lang_out='zh'):
    """分批调用 Anthropic 兼容 API 翻译"""
    BATCH = 50
    SEP = '\n<<<SEP>>>\n'
    cache = {}

    total_batches = (len(texts) - 1) // BATCH + 1
    for i in tqdm(range(0, len(texts), BATCH), desc='API Translating', unit='batch', ncols=80):
        batch = texts[i:i+BATCH]
        combined = SEP.join(batch)

        try:
            resp = httpx.post(
                f'{BASE_URL}/v1/messages',
                headers={'x-api-key': API_KEY, 'anthropic-version': '2023-06-01',
                         'content-type': 'application/json'},
                json={
                    'model': MODEL, 'max_tokens': 8192, 'temperature': 0.1,
                    'system': f'逐条翻译{len(batch)}条文本从{lang_in}到{lang_out}。每条译文间用"<<<SEP>>>"分隔。只输出译文，不解释。保留数字、代码、专有名词。',
                    'messages': [{'role': 'user', 'content': combined}]
                }, timeout=300
            )
            data = resp.json()
            text_blocks = [b for b in data.get('content', []) if b.get('type') == 'text']
            if text_blocks:
                results = [r.strip() for r in text_blocks[0]['text'].split(SEP)]
                for src, zh in zip(batch, results):
                    if zh and zh != src:
                        cache[text_key(src)] = zh
                pass  # translated OK
            else:
                tqdm.write(f'  Warning: no text block - {[b.get("type") for b in data.get("content",[])]}')
        except Exception as e:
            tqdm.write(f'  API error: {e}')

    return cache


def translate_pdf(input_path, output_path, lang_in='en', lang_out='zh'):
    print(f'Input: {input_path}')
    doc = pymupdf.open(input_path)
    cache_path = os.path.join(os.path.dirname(input_path) or '.',
        os.path.basename(input_path).rsplit('.', 1)[0] + '_cache.json')
    cache = load_cache(cache_path)

    # 收集所有文本
    all_texts = set()
    for page in doc:
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                for s in l['spans']:
                    t = s['text'].strip()
                    if t and len(t) > 1:
                        all_texts.add(t)

    print(f'Unique texts: {len(all_texts)}')

    # API 翻译缺失的
    pending = [t for t in all_texts if text_key(t) not in cache]
    if pending:
        print(f'Translating {len(pending)} texts via API...')
        new_translations = api_translate(pending, lang_in, lang_out)
        cache.update(new_translations)
        save_cache(cache_path, cache)
    else:
        print('All texts already cached')

    # 原位替换（无填充 — 保留背景）
    replaced = 0
    for page_num in tqdm(range(len(doc)), desc='Rendering PDF', unit='page', ncols=80):
        page = doc[page_num]
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                for s in l['spans']:
                    text = s['text'].strip()
                    if not text or len(text) <= 1: continue

                    k = text_key(text)
                    zh = cache.get(k)
                    if not zh or zh == text: continue

                    bbox = s['bbox']
                    font_size = s['size']
                    color = s['color']
                    font_name = s.get('font', '')
                    flags = s.get('flags', 0)

                    # 检测粗体 (flags bit 2 = bold, 或字体名含 Bold)
                    is_bold = bool(flags & 2) or 'bold' in font_name.lower()

                    # 无填充redact — 仅移除文字，保留背景
                    page.add_redact_annot(bbox)
                    page.apply_redactions()

                    # 中文宽度约英文60%，适当缩小但尽量保持原字号
                    ratio = len(zh) / max(len(text), 1)
                    if ratio > 1.5:
                        adj = font_size * 0.85  # 长中文略缩小
                    else:
                        adj = font_size  # 保持原字号

                    # 用无衬线中文字体匹配原文风格
                    cjk_font = 'china-ss'  # sans-serif

                    # 插入中文 — 粗体模拟用两次叠加
                    pos = (bbox[0], bbox[3] - font_size * 0.15)
                    page.insert_text(pos, zh, fontname=cjk_font, fontsize=adj,
                                     color=pymupdf.sRGB_to_pdf(color))
                    if is_bold:
                        page.insert_text((pos[0]+0.3, pos[1]), zh, fontname=cjk_font,
                                         fontsize=adj, color=pymupdf.sRGB_to_pdf(color))
                    replaced += 1

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f'Saved: {output_path} ({replaced} replacements)')
    return output_path


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='PDF翻译 v4 - 完整API翻译 + 保留背景')
    ap.add_argument('input', help='输入PDF')
    ap.add_argument('-o', '--output', help='输出PDF', default=None)
    args = ap.parse_args()

    if not args.output:
        args.output = args.input.rsplit('.', 1)[0] + '_中文版.pdf'

    translate_pdf(args.input, args.output)
