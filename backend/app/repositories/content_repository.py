"""内容数据访问层"""

from typing import List, Optional, Tuple

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.content import ContentPage, ContentVersion
from app.models.seo_metadata import SeoMetadata
from app.repositories.base_repository import BaseRepository


class ContentPageRepository(BaseRepository[ContentPage]):
    """内容页面Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, ContentPage)

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        page_type: str = None,
        status: str = None,
        search: str = None,
        is_active: bool = True,
    ) -> Tuple[List[ContentPage], int]:
        """分页获取页面"""
        query = select(ContentPage).filter(ContentPage.is_active == is_active)
        if page_type:
            query = query.filter(ContentPage.page_type == page_type)
        if status:
            query = query.filter(ContentPage.status == status)
        if search:
            query = query.filter(or_(ContentPage.title.ilike(
                f"%{search}%"), ContentPage.summary.ilike(f"%{search}%")))

        total = self.db.execute(
            select(
                func.count()).select_from(
                query.subquery())).scalar()
        items = (
            self.db.execute(
                query.order_by(
                    desc(
                        ContentPage.created_at)).offset(
                    (page - 1) * page_size).limit(page_size)) .scalars() .all())

        return items, total

    def get_by_slug(self, slug: str) -> Optional[ContentPage]:
        """根据slug获取页面"""
        return self.db.execute(
            select(ContentPage).filter(
                ContentPage.slug == slug,
                ContentPage.is_active)).scalar_one_or_none()

    def search_pages(self, keyword: str, page: int = 1,
                     page_size: int = 20) -> Tuple[List[ContentPage], int]:
        """搜索页面"""
        query = select(ContentPage).filter(
            ContentPage.is_active,
            or_(
                ContentPage.title.ilike(f"%{keyword}%"),
                ContentPage.summary.ilike(f"%{keyword}%"),
                ContentPage.content.ilike(f"%{keyword}%"),
            ),
        )
        total = self.db.execute(
            select(
                func.count()).select_from(
                query.subquery())).scalar()
        items = (
            self.db.execute(
                query.order_by(
                    desc(
                        ContentPage.created_at)).offset(
                    (page - 1) * page_size).limit(page_size)) .scalars() .all())

        return items, total

    def increment_view_count(self, page_id: str) -> bool:
        """增加浏览次数"""
        page = self.get_by_id(page_id)
        if page:
            page.view_count += 1
            self.db.commit()
            return True
        return False

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_pages = self.db.execute(
            select(
                func.count(
                    ContentPage.id)).filter(
                ContentPage.is_active)).scalar()

        published_pages = self.db.execute(
            select(
                func.count(
                    ContentPage.id)).filter(
                ContentPage.status == "published",
                ContentPage.is_active)).scalar()

        draft_pages = self.db.execute(
            select(
                func.count(
                    ContentPage.id)).filter(
                ContentPage.status == "draft",
                ContentPage.is_active)).scalar()

        page_type_stats = self.db.execute(
            select(ContentPage.page_type, func.count(ContentPage.id))
            .filter(ContentPage.is_active)
            .group_by(ContentPage.page_type)
        ).all()
        return {
            "total_pages": total_pages,
            "published_pages": published_pages,
            "draft_pages": draft_pages,
            "page_type_stats": {pt: count for pt, count in page_type_stats},
        }

    def exists_by_slug(self, slug: str, exclude_id: str = None) -> bool:
        """检查slug是否存在"""
        query = select(ContentPage).filter(ContentPage.slug == slug)
        if exclude_id:
            query = query.filter(ContentPage.id != exclude_id)
        return self.db.execute(query).scalar() is not None


class SeoMetadataRepository(BaseRepository[SeoMetadata]):
    """SEO元数据Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, SeoMetadata)

    def get_by_resource(
            self,
            resource_type: str,
            resource_id: str) -> Optional[SeoMetadata]:
        """根据资源类型和ID获取SEO元数据"""
        return self.db.execute(
            select(SeoMetadata).filter(
                SeoMetadata.resource_type == resource_type,
                SeoMetadata.resource_id == resource_id)).scalar_one_or_none()

    def create_or_update(
            self,
            resource_type: str,
            resource_id: str,
            **kwargs) -> SeoMetadata:
        """创建或更新SEO元数据"""
        meta = self.get_by_resource(resource_type, resource_id)
        if meta:
            for key, value in kwargs.items():
                if hasattr(meta, key):
                    setattr(meta, key, value)
        else:
            kwargs["resource_type"] = resource_type
            kwargs["resource_id"] = resource_id
            meta = SeoMetadata(**kwargs)
            self.db.add(meta)

        self.db.commit()
        self.db.refresh(meta)
        return meta


class ContentVersionRepository(BaseRepository[ContentVersion]):
    """内容版本Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, ContentVersion)

    def get_by_page_id(self, page_id: str) -> List[ContentVersion]:
        """获取页面版本列表"""
        return (
            self.db.execute(
                select(ContentVersion)
                .filter(ContentVersion.page_id == page_id)
                .order_by(desc(ContentVersion.version_number))
            )
            .scalars()
            .all()
        )

    def get_by_page_id_and_version(
            self,
            page_id: str,
            version_id: str) -> Optional[ContentVersion]:
        """获取指定页面的指定版本"""
        return self.db.execute(
            select(ContentVersion).filter(
                ContentVersion.page_id == page_id,
                ContentVersion.id == version_id)).scalar_one_or_none()

    def get_max_version_number(self, page_id: str) -> int:
        """获取最大版本号"""
        result = self.db.execute(
            select(
                func.max(
                    ContentVersion.version_number)).filter(
                ContentVersion.page_id == page_id)).scalar()
        return result or 0

    def create_version(
            self,
            page_id: str,
            page: ContentPage,
            change_note: str = None,
            author_id: str = None) -> ContentVersion:
        """创建页面版本"""
        max_version = self.get_max_version_number(page_id)
        new_version = ContentVersion(
            page_id=page_id,
            version_number=max_version + 1,
            title=page.title,
            content=page.content,
            summary=page.summary,
            change_note=change_note or f"版本 {max_version + 1}",
            author_id=author_id,
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version
