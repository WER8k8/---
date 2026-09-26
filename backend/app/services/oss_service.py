"""
阿里云 OSS 存储服务
替代 MinIO，云存储更可靠，支持 CDN 加速
"""
import os
import logging
from typing import Optional, BinaryIO
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    logger.warning("oss2 not installed, OSS storage unavailable")


class OSSConfig:
    """阿里 OSS 配置"""
    def __init__(self):
        self.access_key = os.getenv("OSS_ACCESS_KEY", "")
        self.secret_key = os.getenv("OSS_SECRET_KEY", "")
        self.endpoint = os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
        self.bucket_name = os.getenv("OSS_BUCKET", "youding-files")
        self.cdn_domain = os.getenv("OSS_CDN_DOMAIN", "")
        self.internal_endpoint = os.getenv("OSS_INTERNAL_ENDPOINT", "")


class OSSService:
    """阿里云 OSS 存储服务"""

    def __init__(self, config: Optional[OSSConfig] = None):
        if not OSS_AVAILABLE:
            raise ImportError("oss2 package not installed. Run: pip install oss2")
        self.config = config or OSSConfig()
        self._bucket = None

    def _get_bucket(self):
        if self._bucket is None:
            auth = oss2.Auth(self.config.access_key, self.config.secret_key)
            endpoint = self.config.internal_endpoint or self.config.endpoint
            self._bucket = oss2.Bucket(auth, endpoint, self.config.bucket_name)
        return self._bucket

    def upload_file(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """
        上传文件到 OSS
        :param key: 文件路径（如 images/2024/01/product.jpg）
        :param data: 文件内容
        :param content_type: MIME 类型
        :return: 文件访问 URL
        """
        bucket = self._get_bucket()
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        bucket.put_object(key, data, headers=headers)
        url = self.get_public_url(key)
        logger.info(f"OSS uploaded: {key} -> {url}")
        return url

    def upload_fileobj(self, key: str, fileobj: BinaryIO, size: int, content_type: Optional[str] = None) -> str:
        """
        上传文件对象到 OSS
        :param key: 文件路径
        :param fileobj: 文件对象（如 Django UploadedFile）
        :param size: 文件大小
        :param content_type: MIME 类型
        :return: 文件访问 URL
        """
        bucket = self._get_bucket()
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        bucket.put_object(key, fileobj, headers=headers)
        url = self.get_public_url(key)
        logger.info(f"OSS uploaded: {key} -> {url}")
        return url

    def delete_file(self, key: str):
        """删除文件"""
        bucket = self._get_bucket()
        bucket.delete_object(key)
        logger.info(f"OSS deleted: {key}")

    def get_public_url(self, key: str, expires: int = 0) -> str:
        """
        获取文件公开访问 URL
        :param key: 文件路径
        :param expires: 过期时间（秒），0 表示永久
        :return: URL
        """
        if self.config.cdn_domain:
            return f"https://{self.config.cdn_domain}/{key}"
        return f"https://{self.config.bucket_name}.{self.config.endpoint}/{key}"

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        """
        获取签名 URL（用于私有文件访问）
        :param key: 文件路径
        :param expires: 过期时间（秒），默认 1 小时
        :return: 签名 URL
        """
        bucket = self._get_bucket()
        return bucket.sign_url("GET", key, expires)

    def file_exists(self, key: str) -> bool:
        """检查文件是否存在"""
        bucket = self._get_bucket()
        return bucket.object_exists(key)

    def get_file_size(self, key: str) -> Optional[int]:
        """获取文件大小"""
        bucket = self._get_bucket()
        try:
            head = bucket.head_object(key)
            return head.content_length
        except Exception:
            return None

    def list_files(self, prefix: str = "", max_keys: int = 100) -> list:
        """列出文件"""
        bucket = self._get_bucket()
        result = bucket.list_objects(prefix=prefix, max_keys=max_keys)
        return [
            {
                "key": obj.key,
                "size": obj.size,
                "last_modified": obj.last_modified,
            }
            for obj in result.object_list
        ]


# 全局实例
_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    """获取 OSS 服务全局实例"""
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service


def is_oss_configured() -> bool:
    """检查 OSS 是否已配置"""
    return bool(os.getenv("OSS_ACCESS_KEY") and os.getenv("OSS_SECRET_KEY"))
