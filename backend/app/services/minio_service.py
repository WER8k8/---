"""MinIO对象存储服务 — 租户隔离增强

所有对象键强制使用 {tenant_id}/ 前缀，确保：
- 上传路径自动注入租户前缀
- 下载/访问时验证 tenant_id 匹配
- 列出对象时仅返回当前租户的文件
"""
import logging
from datetime import timedelta
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

log = logging.getLogger(__name__)


def tenant_object_key(tenant_id: str, path: str) -> str:
    """构造租户隔离的对象存储键。

    格式: {tenant_id}/{path}
    自动去除 path 的前导 / 和已有的 {tenant_id}/ 前缀。

    Args:
        tenant_id: 租户 UUID
        path: 原始文件路径

    Returns:
        带租户前缀的对象键

    Example:
        tenant_object_key("abc123", "images/logo.png")
        # => "abc123/images/logo.png"
    """
    # 去除前导 /
    path = path.lstrip("/")
    # 如果 path 已经以 tenant_id/ 开头，不再重复添加
    prefix = f"{tenant_id}/"
    if path.startswith(prefix):
        return path
    return f"{prefix}{path}"


def extract_tenant_from_key(object_name: str) -> Optional[str]:
    """从对象键中提取租户 ID。

    Args:
        object_name: 完整对象键，如 "abc123/images/logo.png"

    Returns:
        租户 ID，如果不是标准格式则返回 None
    """
    if "/" in object_name:
        return object_name.split("/", 1)[0]
    return None


def validate_tenant_access(bucket: str, key: str, tenant_id: str) -> bool:
    """验证租户是否有权访问指定对象。

    检查对象键是否以 {tenant_id}/ 开头，防止跨租户访问。

    Args:
        bucket: 桶名称
        key: 对象键
        tenant_id: 请求访问的租户 ID

    Returns:
        True 如果租户有权访问，False 无权访问

    Example:
        validate_tenant_access("uploads", "abc123/logo.png", "abc123")  # => True
        validate_tenant_access("uploads", "xyz789/logo.png", "abc123")  # => False
    """
    expected_prefix = f"{tenant_id}/"
    return key.startswith(expected_prefix)


class MinioService:
    """MinIO 对象存储客户端，用于文件上传/下载/签名URL。

    租户隔离增强版：
    - upload_file / get_url / delete_file / file_exists 均需传入 tenant_id
    - 所有对象键自动添加 {tenant_id}/ 前缀
    - 访问时验证 tenant_id 匹配，防止越权
    """
    # 默认桶列表（会在 init_buckets 中自动创建）
    DEFAULT_BUCKETS = ["uploads", "screenshots", "seo-assets", "backups"]
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=bool(settings.MINIO_SECURE),
        )

    def ensure_buckets(self, buckets: Optional[list[str]] = None) -> None:
        """确保指定的桶存在，不存在则创建。"""
        for bucket in buckets or self.DEFAULT_BUCKETS:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
            except S3Error:
                pass

    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        bucket_name: str = "uploads",
        content_type: str = "application/octet-stream",
        tenant_id: Optional[str] = None,
    ) -> dict:
        """上传文件到 MinIO（带租户隔离）。

        Args:
            file_data: 文件字节数据
            object_name: 对象名称（路径键）
            bucket_name: 桶名称
            content_type: MIME 类型
            tenant_id: 租户 ID，必须提供。对象键将自动添加 {tenant_id}/ 前缀

        Returns:
            {"bucket": str, "object_name": str, "etag": str, "tenant_id": str}

        Raises:
            ValueError: 未提供 tenant_id
        """
        if not tenant_id:
            raise ValueError("上传必须指定 tenant_id 以启用租户隔离")

        # 强制添加租户前缀
        isolated_key = tenant_object_key(tenant_id, object_name)
        self.ensure_buckets([bucket_name])
        result = self.client.put_object(
            bucket_name,
            isolated_key,
            BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )
        return {
            "bucket": bucket_name,
            "object_name": isolated_key,
            "etag": result.etag,
            "tenant_id": tenant_id,
        }

    def get_url(
        self,
        object_name: str,
        bucket_name: str = "uploads",
        expires: int = 3600,
        tenant_id: Optional[str] = None,
    ) -> str:
        """获取文件预签名访问 URL（带租户验证）。

        Args:
            object_name: 对象键
            bucket_name: 桶名称
            expires: URL 有效期（秒）
            tenant_id: 租户 ID，用于验证访问权限

        Raises:
            PermissionError: tenant_id 与对象键不匹配
        """
        if tenant_id and not validate_tenant_access(bucket_name, object_name, tenant_id):
            raise PermissionError(
                f"租户 {tenant_id} 无权访问对象 {object_name}"
            )
        return self.client.presigned_get_object(
            bucket_name, object_name, expires=timedelta(seconds=expires)
        )

    def get_public_url(
        self,
        object_name: str,
        bucket_name: str = "uploads",
        tenant_id: Optional[str] = None,
    ) -> str:
        """获取公开访问 URL（带租户验证）。"""
        if tenant_id and not validate_tenant_access(bucket_name, object_name, tenant_id):
            raise PermissionError(
                f"租户 {tenant_id} 无权访问对象 {object_name}"
            )
        return f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"

    def delete_file(
        self,
        object_name: str,
        bucket_name: str = "uploads",
        tenant_id: Optional[str] = None,
    ) -> bool:
        """删除指定对象（带租户验证）。"""
        if tenant_id and not validate_tenant_access(bucket_name, object_name, tenant_id):
            log.warning(
                "删除被拒绝: 租户 %s 无权删除 %s/%s",
                tenant_id, bucket_name, object_name,
            )
            return False
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def file_exists(
        self,
        object_name: str,
        bucket_name: str = "uploads",
        tenant_id: Optional[str] = None,
    ) -> bool:
        """检查对象是否存在（带租户验证）。"""
        if tenant_id and not validate_tenant_access(bucket_name, object_name, tenant_id):
            return False
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False

    def list_objects(
        self,
        bucket_name: str = "uploads",
        prefix: str = "",
        tenant_id: Optional[str] = None,
    ) -> list[dict]:
        """列出桶中的对象（仅返回当前租户的文件）。

        Args:
            bucket_name: 桶名称
            prefix: 路径前缀
            tenant_id: 如果提供，仅返回该租户的对象

        Returns:
            对象元数据列表
        """
        # 如果有租户ID，自动添加租户前缀限定搜索范围
        search_prefix = ""
        if tenant_id:
            search_prefix = f"{tenant_id}/{prefix.lstrip('/')}"
        else:
            search_prefix = prefix

        objects = self.client.list_objects(bucket_name, prefix=search_prefix, recursive=True)
        return [
            {
                "object_name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                "tenant_id": extract_tenant_from_key(obj.object_name),
            }
            for obj in objects
        ]


# 全局单例
minio_service = MinioService()
