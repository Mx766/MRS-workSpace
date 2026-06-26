"""
API 配置管理 — 加密存储，多服务商支持
"""
import json, os, base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config.json')

SERVICE_PRESETS = {
    'deepseek': {
        'name': 'DeepSeek',
        'base_url': 'https://api.deepseek.com',
        'models': ['deepseek-chat', 'deepseek-v4-pro', 'deepseek-v4-flash'],
        'default_model': 'deepseek-v4-flash',
    },
    'openai': {
        'name': 'OpenAI',
        'base_url': 'https://api.openai.com',
        'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
        'default_model': 'gpt-4o-mini',
    },
    'ollama': {
        'name': 'Ollama (本地)',
        'base_url': 'http://localhost:11434',
        'models': ['llama3', 'qwen3', 'deepseek-r1'],
        'default_model': 'qwen3',
    },
    'custom': {
        'name': '自定义',
        'base_url': '',
        'models': [],
        'default_model': '',
    },
}

def _get_key():
    """生成机器绑定密钥"""
    machine_id = os.environ.get('COMPUTERNAME', '') + os.environ.get('USERNAME', '')
    salt = b'doctrans_salt_2026'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))

def load_config():
    """加载配置，失败返回默认值"""
    default = {
        'service': 'deepseek',
        'api_key': '',
        'model': 'deepseek-v4-flash',
        'base_url_override': '',
    }
    if not os.path.exists(CONFIG_FILE):
        return default
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'api_key' in data and data['api_key']:
            f = Fernet(_get_key())
            data['api_key'] = f.decrypt(data['api_key'].encode()).decode()
        for k in default:
            if k not in data:
                data[k] = default[k]
        return data
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.warning(f'Failed to load config: {e}')
        return default

def save_config(service, api_key, model, base_url_override=''):
    """保存配置，加密Key"""
    data = {
        'service': service,
        'api_key': '',
        'model': model,
        'base_url_override': base_url_override,
    }
    if api_key:
        f = Fernet(_get_key())
        data['api_key'] = f.encrypt(api_key.encode()).decode()
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def test_connection(service, api_key, model, base_url_override=''):
    """测试 API 连接"""
    import httpx
    preset = SERVICE_PRESETS.get(service, SERVICE_PRESETS['custom'])
    base = base_url_override or preset['base_url']
    try:
        resp = httpx.post(
            f'{base}/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5},
            timeout=15
        )
        if resp.status_code == 200:
            return True, '连接成功'
        return False, f'HTTP {resp.status_code}: {resp.text[:200]}'
    except Exception as e:
        return False, str(e)
