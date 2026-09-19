# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""内容服务层"""

import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.content import ContentPage, ContentVersion
from app.models.seo_metadata import SeoMetadata
from app.repositories.content_repository import (ContentPageRepository,
                                                 ContentVersionRepository,
                                                 SeoMetadataRepository)
from app.repositories.user_repository import OperationLogRepository
from app.schemas.content import (ContentPageCreate, ContentPageResponse,
                                 ContentPageUpdate, ContentVersionCreate,
                                 SeoMetadataCreate, SeoMetadataUpdate)


class ContentPageService:
    """内容页面服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.page_repo = ContentPageRepository(db)
        self.version_repo = ContentVersionRepository(db)
        self.log_repo = OperationLogRepository(db)
        self.upload_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)))),
            "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self.allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
        self.max_file_size = 5 * 1024 * 1024  # 5MB

    def list_pages(self,
                   page_type: str = None,
                   page: int = 1,
                   page_size: int = 20,
                   search: str = None,
                   is_published: str = None) -> Tuple[List[ContentPage],
                                                      int]:
        """分页获取页面列表"""
        status = "published" if is_published == "true" else (
            "draft" if is_published == "false" else None)
        return self.page_repo.get_paginated(
            page=page,
            page_size=page_size,
            page_type=page_type,
            status=status,
            search=search)

    def search_pages(self, keyword: str, page: int = 1,
                     page_size: int = 20) -> Tuple[List[ContentPage], int]:
        """搜索页面"""
        return self.page_repo.search_pages(keyword, page, page_size)

    def get_page(self, page_id: str) -> Optional[ContentPage]:
        """获取单个页面"""
        return self.page_repo.get_by_id(page_id)

    def get_page_by_slug(self, slug: str) -> Optional[ContentPage]:
        """根据slug获取页面"""
        page = self.page_repo.get_by_slug(slug)
        if page:
            self.page_repo.increment_view_count(page.id)
        return page

    def create_page(
            self,
            data: ContentPageCreate,
            created_by: str = None) -> ContentPage:
        """创建页面"""
        # 检查slug是否已存在
        if self.page_repo.exists_by_slug(data.slug):
            raise ValueError("页面slug已存在")

        payload = data.model_dump()
        if created_by and "author_id" not in payload:
            payload["author_id"] = created_by
        page = self.page_repo.create(**payload)
        if created_by:
            self.log_repo.create_log(
                user_id=created_by,
                action="create",
                resource_type="page",
                resource_id=page.id,
                detail=f"创建页面: {page.title}",
            )

        return page

    def update_page(self, page_id: str, data: ContentPageUpdate,
                    updated_by: str = None) -> Optional[ContentPage]:
        """更新页面"""
        update_data = data.model_dump(exclude_unset=True)
        # 如果slug变更，检查是否重复
        if "slug" in update_data:
            if self.page_repo.exists_by_slug(
                    update_data["slug"], exclude_id=page_id):
                raise ValueError("页面slug已存在")

        page = self.page_repo.update(page_id, **update_data)
        if page and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="update",
                resource_type="page",
                resource_id=page.id,
                detail=f"更新页面: {page.title}",
            )

        return page

    def delete_page(self, page_id: str, deleted_by: str = None) -> bool:
        """删除页面"""
        success = self.page_repo.delete(page_id)
        if success and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="delete",
                resource_type="page",
                resource_id=page_id,
                detail="删除页面")

        return success

    def upload_image(self, file_content: bytes, file_name: str) -> dict:
        """上传图片"""
        # 验证文件名
        if not file_name or "." not in file_name:
            raise ValueError("无效的文件名")

        # 验证扩展名
        ext = file_name.rsplit(".", 1)[-1].lower()
        if ext not in self.allowed_extensions:
            raise ValueError(
                f"不支持的图片格式: .{ext}，仅支持 {', '.join(self.allowed_extensions)}")

        # 验证文件大小
        if len(file_content) > self.max_file_size:
            raise ValueError("文件大小不能超过 5MB")

        if len(file_content) == 0:
            raise ValueError("文件内容为空")

        # 保存文件
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)

        return {"url": f"/uploads/{filename}", "filename": filename}

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.page_repo.get_stats()

    def batch_delete(self, ids: List[str], deleted_by: str = None) -> int:
        """批量删除页面"""
        deleted = self.page_repo.bulk_delete(ids)
        if deleted > 0 and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="batch_delete",
                resource_type="page",
                detail=f"批量删除 {deleted} 个页面")

        return deleted

    def batch_update_status(
            self,
            ids: List[str],
            status: str,
            updated_by: str = None) -> int:
        """批量更新页面状态"""
        count = 0
        now = datetime.now(timezone.utc)
        for id in ids:
            update_data = {"status": status}
            if status == "published":
                update_data["published_at"] = now
            page = self.page_repo.update(id, **update_data)
            if page:
                count += 1

        if count > 0 and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="batch_update",
                resource_type="page",
                detail=f"批量更新 {count} 个页面状态为 {status}",
            )

        return count

    def batch_publish(self, ids: List[str], published_by: str = None) -> int:
        """批量发布页面"""
        return self.batch_update_status(ids, "published", published_by)


class SeoMetadataService:
    """SEO元数据服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.seo_repo = SeoMetadataRepository(db)
        self.log_repo = OperationLogRepository(db)

    def get_seo_meta(
            self,
            resource_type: str,
            resource_id: str) -> Optional[SeoMetadata]:
        """获取SEO元数据"""
        return self.seo_repo.get_by_resource(resource_type, resource_id)

    def get_page_seo_meta(self, resource_id: str) -> Optional[SeoMetadata]:
        """获取页面SEO元数据"""
        return self.get_seo_meta("page", resource_id)

    def create_seo_meta(
            self,
            data: SeoMetadataCreate,
            created_by: str = None) -> SeoMetadata:
        """创建SEO元数据"""
        meta = self.seo_repo.create(**data.model_dump())
        if created_by:
            self.log_repo.create_log(
                user_id=created_by,
                action="create",
                resource_type="seo",
                resource_id=meta.id,
                detail=f"创建SEO元数据: {data.resource_type}/{data.resource_id}",
            )

        return meta

    def update_seo_meta(
            self,
            resource_type: str,
            resource_id: str,
            data: SeoMetadataUpdate,
            updated_by: str = None) -> SeoMetadata:
        """更新SEO元数据"""
        meta = self.seo_repo.create_or_update(
            resource_type, resource_id, **data.model_dump(exclude_unset=True))

        if updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="update",
                resource_type="seo",
                resource_id=meta.id,
                detail=f"更新SEO元数据: {resource_type}/{resource_id}",
            )

        return meta

    def update_page_seo_meta(
            self,
            resource_id: str,
            data: SeoMetadataUpdate,
            updated_by: str = None) -> SeoMetadata:
        """更新页面SEO元数据"""
        return self.update_seo_meta("page", resource_id, data, updated_by)


class ContentVersionService:
    """内容版本服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.version_repo = ContentVersionRepository(db)
        self.page_repo = ContentPageRepository(db)
        self.log_repo = OperationLogRepository(db)

    def create_version(
            self,
            page_id: str,
            change_note: str = None,
            author_id: str = None) -> ContentVersion:
        """创建页面版本"""
        page = self.page_repo.get_by_id(page_id)
        if not page:
            raise ValueError("页面不存在")

        version = self.version_repo.create_version(
            page_id, page, change_note, author_id)

        if author_id:
            self.log_repo.create_log(
                user_id=author_id,
                action="create",
                resource_type="version",
                resource_id=version.id,
                detail=f"创建版本 {version.version_number} 用于页面: {page.title}",
            )

        return version

    def list_versions(self, page_id: str) -> List[ContentVersion]:
        """获取页面版本列表"""
        page = self.page_repo.get_by_id(page_id)
        if not page:
            raise ValueError("页面不存在")

        return self.version_repo.get_by_page_id(page_id)

    def get_version(
            self,
            page_id: str,
            version_id: str) -> Optional[ContentVersion]:
        """获取指定版本"""
        return self.version_repo.get_by_page_id_and_version(
            page_id, version_id)

    def rollback_to_version(
            self,
            page_id: str,
            version_id: str,
            rolled_by: str = None) -> Optional[ContentPage]:
        """回滚到指定版本"""
        page = self.page_repo.get_by_id(page_id)
        if not page:
            raise ValueError("页面不存在")

        version = self.version_repo.get_by_page_id_and_version(
            page_id, version_id)
        if not version:
            raise ValueError("版本不存在")

        # 回滚内容
        page.title = version.title
        page.content = version.content
        page.summary = version.summary
        self.page_repo.db.commit()
        self.page_repo.db.refresh(page)
        if rolled_by:
            self.log_repo.create_log(
                user_id=rolled_by,
                action="rollback",
                resource_type="page",
                resource_id=page_id,
                detail=f"回滚页面 {page.title} 到版本 {version.version_number}",
            )

        return page

    @staticmethod
    def sanitize_html(content: str) -> str:
        """清理HTML内容，防止XSS攻击"""
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<form[^>]*>.*?</form>",
        ]
        for pattern in dangerous_patterns:
            content = re.sub(
                pattern,
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL)
        return content
