"""
对话式审校引擎 — 自然语言指令修改译文
"""
import os, re, json, logging
import httpx
from config import load_config

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str | None:
    """
    安全地从 LLM 返回内容中提取第一个完整 JSON 对象。
    使用括号配对而非贪婪正则，避免多 JSON 块时捕获错误。
    """
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    for i, c in enumerate(text[start:], start):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def review_action(user_message, current_text, page_context=''):
    """
    解析用户的审校指令并返回操作
    返回: {'action': 'replace'|'locate'|'unknown', 'details': {...}}
    """
    cfg = load_config()
    bb = cfg.get('base_url_override') or 'https://api.deepseek.com'

    prompt = f"""你是一个审校指令解析器。用户正在审校一篇翻译文档。

当前第{page_context}页内容片段：
{current_text[:2000]}

用户指令："{user_message}"

请解析指令并返回 JSON：
{{
  "action": "replace" | "locate_page" | "list_terms" | "add_term" | "unknown",
  "find": "要查找的文本",
  "replace": "替换成的文本",
  "page": 页码数字或null,
  "explanation": "简短说明"
}}

如果是全文替换（不限于当前页），page 设为 null。
如果是查看某个术语标记，action 用 list_terms。
如果指令是要把某个翻译加入术语库，action 用 add_term。
JSON:"""

    try:
        resp = httpx.post(
            f'{bb}/v1/chat/completions',
            headers={'Authorization': f'Bearer {cfg["api_key"]}',
                     'Content-Type': 'application/json'},
            json={'model': cfg['model'], 'temperature': 0, 'max_tokens': 300,
                  'messages': [{'role': 'user', 'content': prompt}]},
            timeout=30
        )
        data = resp.json()
        content = data['choices'][0]['message']['content']

        # 安全提取 JSON（括号配对，非贪婪正则）
        json_str = _extract_json(content)
        if json_str:
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f'JSON parse failed: {e}')
    except httpx.HTTPError as e:
        logger.warning(f'HTTP error in review: {e}')
    except KeyError as e:
        logger.warning(f'Unexpected API response format: {e}')
    except Exception as e:
        logger.warning(f'Review action failed: {e}')

    return {'action': 'unknown', 'explanation': '无法解析指令，请更具体地描述修改内容'}


def execute_replace(full_text, find_text, replace_text):
    """全文替换"""
    count = full_text.count(find_text) if find_text else 0
    return full_text.replace(find_text, replace_text), count


def extract_unknown_terms(text, glossary_db):
    """提取文本中可能未匹配的专业术语"""
    # 标记 {?术语?} 格式
    marked = re.findall(r'\{\?(.*?)\?\}', text)
    # 大写开头的连续词（可能的专有名词）
    proper_nouns = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))
    # 过滤常见词
    common = {'The', 'This', 'These', 'Those', 'Each', 'All', 'Some', 'Any', 'No', 'Not',
              'When', 'Where', 'Which', 'What', 'After', 'Before', 'During', 'Section',
              'Product', 'Information', 'Identification', 'Description', 'General', 'Special',
              'Safety', 'Health', 'Fire', 'Handling', 'Storage', 'Transport', 'Disposal'}
    proper_nouns = [w for w in proper_nouns if w not in common and len(w) > 5]

    # 从术语库检测缺失
    from glossary import get_db
    db = get_db()
    unknown = []
    for term in proper_nouns:
        try:
            exist = db.execute('SELECT id FROM terms WHERE source=?', (term,)).fetchone()
            if not exist:
                unknown.append(term)
        except Exception as e:
            logger.warning(f'Term lookup failed for "{term}": {e}')

    return list(set(list(marked) + unknown))
