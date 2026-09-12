"""输入验证模块"""

import re
from typing import Any, List, Optional

from fastapi import HTTPException

# 尝试导入 filetype 库做 MIME 类型检测
try:
    import filetype as _filetype
    _HAS_FILETYPE = True
except ImportError:
    _filetype = None  # type: ignore[assignment]
    _HAS_FILETYPE = False

# 常见文件类型的 magic bytes 映射（filetype 不可用时的退路）
_MAGIC_BYTES_MAP = {
    # (开头字节, 偏移量) → 期望扩展名集合
    b'\x89PNG\r\n\x1a\n': {'png'},
    b'\xff\xd8\xff': {'jpg', 'jpeg'},
    b'GIF89a': {'gif'},
    b'GIF87a': {'gif'},
    b'%PDF': {'pdf'},
    b'PK\x03\x04': {'zip', 'docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp'},
    b'RIFF': {'webp'},  # RIFF....WEBP
}

# 验证正则表达式
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PHONE_REGEX = r"^1[3-9]\d{9}$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
SLUG_REGEX = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
UUID_REGEX = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    return re.match(EMAIL_REGEX, email) is not None


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return re.match(PHONE_REGEX, phone) is not None


def validate_password(password: str) -> bool:
    """验证密码强度（至少8位，包含大小写字母、数字和特殊字符）"""
    return re.match(PASSWORD_REGEX, password) is not None


def validate_slug(slug: str) -> bool:
    """验证slug格式（小写字母、数字和连字符）"""
    return re.match(SLUG_REGEX, slug) is not None


def validate_uuid(uuid_str: str) -> bool:
    """验证UUID格式"""
    return re.match(UUID_REGEX, uuid_str) is not None


def validate_str_length(
        value: str,
        min_len: int,
        max_len: int,
        field_name: str) -> None:
    """验证字符串长度"""
    if len(value) < min_len:
        raise HTTPException(status_code=400,
                            detail=f"{field_name}长度不能少于{min_len}个字符")
    if len(value) > max_len:
        raise HTTPException(status_code=400,
                            detail=f"{field_name}长度不能超过{max_len}个字符")


def validate_not_empty(value: Any, field_name: str) -> None:
    """验证非空"""
    if value is None:
        raise HTTPException(status_code=400, detail=f"{field_name}不能为空")
    if isinstance(value, str) and value.strip() == "":
        raise HTTPException(status_code=400, detail=f"{field_name}不能为空")
    if isinstance(value, (list, dict)) and len(value) == 0:
        raise HTTPException(status_code=400, detail=f"{field_name}不能为空")


def validate_max_file_size(
        content: bytes,
        max_size_mb: int,
        field_name: str = "文件") -> None:
    """验证文件大小"""
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=400,
                            detail=f"{field_name}大小不能超过{max_size_mb}MB")


def validate_file_extension(filename: str,
                            allowed_extensions: List[str],
                            content: Optional[bytes] = None) -> str:
    """验证文件扩展名，可选 MIME 类型检测（magic bytes）。

    Args:
        filename: 原始文件名
        allowed_extensions: 允许的扩展名列表（小写）
        content: 可选的文件内容字节，用于 magic bytes 校验

    Returns:
        验证通过的文件扩展名（小写）

    Raises:
        HTTPException: 扩展名不允许或 MIME 类型不匹配
    """
    if not filename or "." not in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: .{ext}，仅支持 {', '.join(allowed_extensions)}")

    # MIME 类型 / magic bytes 校验
    if content:
        detected_exts = _detect_content_type(content)
        if detected_exts:
            allowed_set = set(allowed_extensions)
            # 归一化：jpeg ↔ jpg
            normalized_detected = set()
            for d in detected_exts:
                if d == 'jpeg':
                    normalized_detected.add('jpg')
                elif d == 'jpg':
                    normalized_detected.add('jpeg')
                normalized_detected.add(d)
            if not (normalized_detected & allowed_set):
                raise HTTPException(
                    status_code=400,
                    detail=f"文件内容与扩展名 .{ext} 不匹配，检测到: {', '.join(sorted(detected_exts))}")

    return ext


def _detect_content_type(content: bytes) -> Optional[set]:
    """通过 magic bytes 或 filetype 库检测文件真实类型。

    Returns:
        检测到的扩展名集合，无法识别时返回 None
    """
    if _HAS_FILETYPE:
        try:
            kind = _filetype.guess(content)
            if kind and kind.extension:
                return {kind.extension.lower()}
            return None
        except Exception:
            pass

    # filetype 不可用：退回到 magic bytes 匹配
    for magic, exts in _MAGIC_BYTES_MAP.items():
        if content.startswith(magic):
            return exts

    return None


def sanitize_input(value: str) -> str:
    """清理输入，防止XSS攻击"""
    dangerous_patterns = [
        (r"<script[^>]*>.*?</script>", ""),
        (r"javascript:", ""),
        (r"on\w+\s*=", ""),
        (r"<iframe[^>]*>.*?</iframe>", ""),
        (r"<object[^>]*>.*?</object>", ""),
        (r"<embed[^>]*>.*?</embed>", ""),
        (r"<form[^>]*>.*?</form>", ""),
    ]
    for pattern, replacement in dangerous_patterns:
        value = re.sub(
            pattern,
            replacement,
            value,
            flags=re.IGNORECASE | re.DOTALL)

    return value


def validate_pagination(page: int, page_size: int) -> None:
    """验证分页参数"""
    if page < 1:
        raise HTTPException(status_code=400, detail="页码不能小于1")
    if page_size < 1:
        raise HTTPException(status_code=400, detail="每页数量不能小于1")
    if page_size > 100:
        raise HTTPException(status_code=400, detail="每页数量不能超过100")


def validate_sort_by(sort_by: str, allowed_fields: List[str]) -> None:
    """验证排序字段"""
    if sort_by and sort_by not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"无效的排序字段: {sort_by}，可选字段: {', '.join(allowed_fields)}")


def validate_role(role: str) -> None:
    """验证角色"""
    allowed_roles = ["admin", "super_admin", "editor", "user"]
    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"无效的角色: {role}，可选角色: {', '.join(allowed_roles)}")


# 验证结果类
class ValidationResult:
    def __init__(self, valid: bool = True, errors: List[str] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param valid: 参数 valid
        :param errors: 参数 errors
        :return: 返回处理结果。
        """
        self.valid = valid
        self.errors = errors or []

    def add_error(self, error: str):
        """add_error。

        参数说明：
        :param self: 参数 self
        :param error: 参数 error
        :return: 返回处理结果。
        """
        self.valid = False
        self.errors.append(error)

    def __bool__(self):
        """__bool__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.valid
