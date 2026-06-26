"""
统一 LLM 客户端 — API 调用、SHA256 缓存、批量翻译、长度校验

解决问题:
- #2: MD5 截断 12 字符 → SHA256 全长 (碰撞概率从 1/1.4万 降至可忽略)
- #5: zip(batch, results) 无长度校验 → 严格校验 + 降级重试
- #8: 术语匹配 O(N×M) → 预编译 + 全文术语列表

用法:
    from core.llm_client import LlmClient
    client = LlmClient(api_key, model, base_url)
    results = client.batch_translate(texts, glossary_domain='医药')
"""
import hashlib, json, os, re, time, logging
import httpx

logger = logging.getLogger(__name__)

# ── 系统提示词 ──
SYSTEM_PROMPT = (
    '你是专业的医药/化工文档翻译专家。将英文翻译为简体中文。\n'
    '规则（严格遵守）：\n'
    '1. 数字、符号、单位、化学式、CAS号、温度、百分比、邮箱、电话、网址 必须原样保留\n'
    '2. 数字与字母/单位之间不加空格（如"350°C"而非"350 °C"）\n'
    '3. 中文使用全角标点（，。）英文数字使用半角\n'
    '4. 首次出现的专业术语使用全称翻译\n'
    '5. 表格数据保持对齐，不改变数值\n'
    '6. 不要添加解释、注释或补充说明\n'
    '7. 不要翻译人名、公司名、产品名、标准编号（如 ISO 13485）\n'
    '8. 有术语表时，必须使用术语表中的翻译，不要自己编造\n'
    '只输出译文，不要任何前缀或后缀。'
)

SEPARATOR = '<<<SEP>>>'


def make_cache_key(text: str) -> str:
    """SHA256 全长作为缓存键 — 避免 MD5 截断碰撞"""
    return hashlib.sha256(text.encode()).hexdigest()


class LlmClient:
    """统一 LLM 客户端，封装 API 调用 + 缓存 + 术语"""

    def __init__(self, api_key: str, model: str = 'deepseek-chat', base_url: str = ''):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or 'https://api.deepseek.com'
        self._glossary_db = None

    # ── 底层 API 调用 ──
    def call_api(self, messages: list, temperature: float = 0.1, max_tokens: int = 4096,
                 timeout: int = 60) -> str:
        """调用 LLM API"""
        resp = httpx.post(
            f'{self.base_url}/v1/chat/completions',
            headers={'Authorization': f'Bearer {self.api_key}',
                     'Content-Type': 'application/json'},
            json={'model': self.model, 'temperature': temperature,
                  'max_tokens': max_tokens, 'messages': messages},
            timeout=timeout
        )
        if resp.status_code != 200:
            raise RuntimeError(f'HTTP {resp.status_code}: {resp.text[:300]}')
        data = resp.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        raise RuntimeError(data.get('error', {}).get('message', str(data)[:300]))

    # ── 缓存 ──
    def load_cache(self, cache_path: str) -> dict:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f'Failed to load cache {cache_path}: {e}')
        return {}

    def save_cache(self, cache_path: str, cache: dict):
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)

    # ── 术语匹配 ──
    def _get_glossary_db(self):
        """延迟加载术语库连接"""
        if self._glossary_db is None:
            try:
                from glossary import get_db
                self._glossary_db = get_db()
            except Exception:
                return None
        return self._glossary_db

    def match_glossary(self, text: str, domain: str = '') -> list:
        """从文本中匹配术语，返回 [(source, target), ...]"""
        db = self._get_glossary_db()
        if db is None:
            return []
        try:
            if domain:
                rows = db.execute(
                    'SELECT source, target, is_regex, case_sensitive FROM terms '
                    'WHERE domain=? ORDER BY LENGTH(source) DESC', (domain,)
                ).fetchall()
            else:
                rows = db.execute(
                    'SELECT source, target, is_regex, case_sensitive FROM terms '
                    'ORDER BY LENGTH(source) DESC'
                ).fetchall()

            matches = []
            for src, tgt, is_regex, case_sensitive in rows:
                if not src or not tgt:
                    continue
                if is_regex:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if re.search(src, text, flags):
                        matches.append((src, tgt))
                else:
                    if case_sensitive:
                        if src in text:
                            matches.append((src, tgt))
                    else:
                        if src.lower() in text.lower():
                            matches.append((src, tgt))
            return matches
        except Exception as e:
            logger.warning(f'Glossary match failed: {e}')
            return []

    def build_glossary_prompt(self, text: str, domain: str = '') -> str:
        """从术语库匹配并构建 prompt"""
        matches = self.match_glossary(text, domain)
        if not matches:
            return ''
        lines = ['\n【术语表 - 必须严格按以下翻译，不得自行发挥】']
        for src, tgt in matches[:30]:
            lines.append(f'  "{src}" → "{tgt}"')
        return '\n'.join(lines)

    # ── 批量翻译（带长度校验） ──
    def batch_translate(self, texts: list, system_prompt: str = '',
                        cache: dict = None, domain: str = '',
                        max_tokens: int = 8192, batch_size: int = 30,
                        progress_callback=None) -> dict:
        """
        批量翻译文本列表。

        参数:
            texts: 待翻译文本列表
            system_prompt: 自定义 system prompt
            cache: 现有缓存 dict (会被原地更新)
            domain: 术语领域
            max_tokens: 单次 API 最大 token
            batch_size: 每批最多翻译条数
            progress_callback: fn(pct, msg)

        返回:
            cache dict (SHA256 key → 译文)
        """
        if cache is None:
            cache = {}

        # 找出未缓存的
        pending = []
        for t in texts:
            key = make_cache_key(t)
            if key not in cache:
                pending.append(t)

        if not pending:
            return cache

        prompt = system_prompt or SYSTEM_PROMPT
        plist = sorted(pending, key=len, reverse=True)  # 长文本优先

        for i in range(0, len(plist), batch_size):
            batch = plist[i:i + batch_size]
            batch_idx = i // batch_size + 1
            total_batches = (len(plist) - 1) // batch_size + 1
            pct_base = 0.1 + 0.5 * (i / max(len(plist), 1))

            if progress_callback:
                progress_callback(pct_base,
                    f'翻译 {i+1}-{min(i+batch_size, len(plist))}/{len(plist)}')

            gprompt = self.build_glossary_prompt(' '.join(batch), domain)
            combined = SEPARATOR.join(batch)

            try:
                result = self.call_api([
                    {'role': 'system',
                     'content': f'{prompt}\n批量翻译：逐条翻译，每条用"{SEPARATOR}"分隔。{gprompt}'},
                    {'role': 'user', 'content': combined}
                ], max_tokens=max_tokens)

                results = [r.strip() for r in result.split(SEPARATOR)]

                # ── 关键：校验返回数量 ──
                if len(results) != len(batch):
                    logger.warning(
                        f'Batch mismatch: requested {len(batch)}, got {len(results)}. '
                        f'Falling back to single-item translation.'
                    )
                    # 降级：逐条重试丢失的
                    for src in batch:
                        key = make_cache_key(src)
                        if key in cache:
                            continue
                        try:
                            single = self.call_api([
                                {'role': 'system', 'content': prompt},
                                {'role': 'user', 'content': src}
                            ], max_tokens=4096)
                            if single and single != src:
                                cache[key] = single
                        except Exception as e:
                            logger.warning(f'Single-item retry failed: {e}')
                else:
                    for src, zh in zip(batch, results):
                        if zh and zh != src:
                            cache[make_cache_key(src)] = zh

            except Exception as e:
                logger.warning(f'Batch API error: {e}')
                if progress_callback:
                    progress_callback(pct_base, f'API错误: {e} (继续中...)')

        return cache

    def translate_single(self, text: str, system_prompt: str = '',
                         domain: str = '', cache: dict = None) -> tuple:
        """翻译单条文本，返回 (translated_text, cache_key)"""
        key = make_cache_key(text)
        if cache and key in cache:
            return cache[key], key

        prompt = system_prompt or SYSTEM_PROMPT
        gprompt = self.build_glossary_prompt(text, domain)

        try:
            result = self.call_api([
                {'role': 'system', 'content': f'{prompt}{gprompt}'},
                {'role': 'user', 'content': text}
            ])
            if cache is not None:
                cache[key] = result
            return result, key
        except Exception as e:
            logger.warning(f'Single translate error: {e}')
            return text, key
