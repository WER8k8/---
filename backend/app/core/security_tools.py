import re
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def sanitize_html(content: str) -> str:
    """
    清理HTML内容，防止XSS攻击
    """
    if not content:
        return content
    
    escaped = escape(content)
    
    allowed_tags = [
        ('<b>', '</b>'),
        ('<strong>', '</strong>'),
        ('<i>', '</i>'),
        ('<em>', '</em>'),
        ('<p>', '</p>'),
        ('<br>', '</br>'),
        ('<ul>', '</ul>'),
        ('<ol>', '</ol>'),
        ('<li>', '</li>'),
        ('<a ', '</a>'),
        ('<h1>', '</h1>'),
        ('<h2>', '</h2>'),
        ('<h3>', '</h3>'),
        ('<h4>', '</h4>'),
    ]
    
    for opening, closing in allowed_tags:
        escaped = escaped.replace(escape(opening), opening)
        escaped = escaped.replace(escape(closing), closing)
    
    escaped = re.sub(r'<a\s+([^>]*?)>', r'<a \1>', escaped)
    escaped = re.sub(r'href\s*=\s*["\']([^"\']+)["\']', lambda m: f'href="{sanitize_url(m.group(1))}"', escaped)
    
    return escaped


def sanitize_url(url: str) -> str:
    """
    清理URL，防止恶意链接
    """
    if not url:
        return url
    
    parsed = urlparse(url)
    
    if parsed.scheme not in ('http', 'https'):
        return '#'
    
    if parsed.hostname:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$', parsed.hostname):
            return '#'
    
    return url


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    验证手机号码格式
    """
    if not phone:
        return False
    phone = re.sub(r'\D', '', phone)
    return len(phone) == 11 and phone.startswith('1')


def validate_password(password: str) -> bool:
    """
    验证密码强度
    - 至少8个字符
    - 包含至少一个数字
    - 包含至少一个字母
    """
    if not password or len(password) < 8:
        return False
    if not re.search(r'[a-zA-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True


def sanitize_input(value: Any) -> Any:
    """
    递归清理输入数据
    """
    if isinstance(value, str):
        return sanitize_html(value)
    elif isinstance(value, dict):
        return {key: sanitize_input(val) for key, val in value.items()}
    elif isinstance(value, list):
        return [sanitize_input(item) for item in value]
    else:
        return value


def detect_sql_injection(input_str: str) -> bool:
    """
    检测潜在的SQL注入攻击
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    patterns = [
        r"('|(\%27))",
        r";",
        r"--",
        r"\/\*",
        r"\*\//",
        r"UNION\s+ALL",
        r"INSERT\s+INTO",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"SELECT\s+.*FROM",
        r"EXEC\s+.*SP_",
        r"xp_cmdshell",
        r"0x[0-9a-fA-F]+",
        r"char\(",
        r"nchar\(",
        r"varchar\(",
        r"nvarchar\(",
    ]
    
    input_lower = input_str.lower()
    for pattern in patterns:
        if re.search(pattern, input_lower):
            return True
    return False


def detect_xss_attack(input_str: str) -> bool:
    """
    检测潜在的XSS攻击
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    patterns = [
        r"<script[^>]*>",
        r"</script>",
        r"<iframe[^>]*>",
        r"</iframe>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onclick\s*=",
        r"onerror\s*=",
        r"onmouseover\s*=",
        r"expression\(",
        r"eval\(",
        r"document\.location",
        r"document\.cookie",
        r"window\.location",
        r"alert\(",
    ]
    
    input_lower = input_str.lower()
    for pattern in patterns:
        if re.search(pattern, input_lower):
            return True
    return False


def validate_file_name(filename: str) -> bool:
    """
    验证文件名安全性
    """
    if not filename:
        return False
    
    dangerous_patterns = [
        r"^\.",
        r"\/",
        r"\\",
        r"\.\.",
        r"::",
        r":",
        r"\*",
        r"\?",
        r'\"',
        r"<",
        r">",
        r"\|",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False
    
    return True


def generate_csrf_token() -> str:
    """
    生成CSRF令牌
    """
    import secrets
    return secrets.token_hex(32)


def validate_csrf_token(token: str, stored_token: str) -> bool:
    """
    验证CSRF令牌
    """
    if not token or not stored_token:
        return False
    return secrets.compare_digest(token, stored_token)
