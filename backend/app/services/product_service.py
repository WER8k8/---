"""产品服务层"""

import os
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.product import Category, Product, ProductDocument
from app.repositories.product_repository import (CategoryRepository,
                                                 ProductDocumentRepository,
                                                 ProductRepository)
from app.repositories.user_repository import OperationLogRepository
from app.schemas.product import (CategoryCreate, CategoryTreeResponse,
                                 CategoryUpdate, ProductCreate, ProductUpdate)


class CategoryService:
    """分类服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.category_repo = CategoryRepository(db)
        self.log_repo = OperationLogRepository(db)

    def get_category_tree(self) -> List[CategoryTreeResponse]:
        """获取分类树"""
        categories = self.category_repo.get_all_with_parent()
        return self._build_tree(categories)

    def _build_tree(
            self,
            categories: List[Category],
            parent_id: str = None) -> List[CategoryTreeResponse]:
        """递归构建分类树"""
        tree = []
        for cat in categories:
            if cat.parent_id == parent_id:
                children = self._build_tree(categories, cat.id)
                tree.append(
                    CategoryTreeResponse(
                        id=cat.id,
                        name=cat.name,
                        slug=cat.slug,
                        description=cat.description,
                        parent_id=cat.parent_id,
                        sort_order=cat.sort_order,
                        is_active=cat.is_active,
                        created_at=cat.created_at,
                        children=children,
                    )
                )
        return tree

    def list_categories(self) -> List[Category]:
        """获取所有分类"""
        return self.category_repo.get_all_with_parent()

    def get_category(self, category_id: str) -> Optional[Category]:
        """获取单个分类"""
        return self.category_repo.get_by_id(category_id)

    def create_category(
            self,
            data: CategoryCreate,
            created_by: str = None) -> Category:
        """创建分类"""
        category = self.category_repo.create(**data.model_dump())
        if created_by:
            self.log_repo.create_log(
                user_id=created_by,
                action="create",
                resource_type="category",
                resource_id=category.id,
                detail=f"创建分类: {category.name}",
            )

        return category

    def update_category(
            self,
            category_id: str,
            data: CategoryUpdate,
            updated_by: str = None) -> Optional[Category]:
        """更新分类"""
        category = self.category_repo.update(
            category_id, **data.model_dump(exclude_unset=True))

        if category and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="update",
                resource_type="category",
                resource_id=category.id,
                detail=f"更新分类: {category.name}",
            )

        return category

    def delete_category(
            self,
            category_id: str,
            deleted_by: str = None) -> bool:
        """删除分类"""
        success = self.category_repo.delete(category_id)
        if success and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="delete",
                resource_type="category",
                resource_id=category_id,
                detail=f"删除分类",
            )

        return success


class ProductService:
    """产品服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.product_repo = ProductRepository(db)
        self.doc_repo = ProductDocumentRepository(db)
        self.log_repo = OperationLogRepository(db)
        self.upload_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)))),
            "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def list_products(self,
                      category_id: str = None,
                      is_active: bool = None,
                      search: str = None,
                      page: int = 1,
                      page_size: int = 20) -> Tuple[List[Product],
                                                    int]:
        """分页获取产品列表"""
        return self.product_repo.get_paginated_with_category(
            page=page,
            page_size=page_size,
            category_id=category_id,
            is_active=is_active,
            search=search)

    def get_product(self, product_id: str) -> Optional[Product]:
        """获取单个产品"""
        return self.product_repo.get_by_id(product_id)

    def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """根据slug获取产品"""
        product = self.product_repo.get_by_slug(slug)
        if product:
            self.product_repo.increment_view_count(product.id)
        return product

    def create_product(
            self,
            data: ProductCreate,
            created_by: str = None) -> Product:
        """创建产品"""
        # 检查slug是否已存在
        if self.product_repo.exists_by_slug(data.slug):
            raise ValueError("产品slug已存在")

        product = self.product_repo.create(**data.model_dump())
        if created_by:
            self.log_repo.create_log(
                user_id=created_by,
                action="create",
                resource_type="product",
                resource_id=product.id,
                detail=f"创建产品: {product.name}",
            )

        return product

    def update_product(
            self,
            product_id: str,
            data: ProductUpdate,
            updated_by: str = None) -> Optional[Product]:
        """更新产品"""
        update_data = data.model_dump(exclude_unset=True)
        # 如果slug变更，检查是否重复
        if "slug" in update_data:
            if self.product_repo.exists_by_slug(
                    update_data["slug"], exclude_id=product_id):
                raise ValueError("产品slug已存在")

        product = self.product_repo.update(product_id, **update_data)
        if product and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="update",
                resource_type="product",
                resource_id=product.id,
                detail=f"更新产品: {product.name}",
            )

        return product

    def delete_product(self, product_id: str, deleted_by: str = None) -> bool:
        """删除产品"""
        # 删除关联文档
        self.doc_repo.delete_by_product_id(product_id)
        success = self.product_repo.delete(product_id)
        if success and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="delete",
                resource_type="product",
                resource_id=product_id,
                detail=f"删除产品")

        return success

    def increment_view_count(self, product_id: str) -> int:
        """增加浏览次数"""
        product = self.product_repo.get_by_id(product_id)
        if product:
            self.product_repo.increment_view_count(product_id)
            return product.view_count + 1
        return 0

    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """获取热门产品"""
        return self.product_repo.get_popular_products(limit)

    def batch_delete(self, ids: List[str], deleted_by: str = None) -> int:
        """批量删除产品"""
        deleted = self.product_repo.bulk_delete(ids)
        if deleted > 0 and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="batch_delete",
                resource_type="product",
                detail=f"批量删除 {deleted} 个产品")

        return deleted

    def batch_update_status(
            self,
            ids: List[str],
            is_active: bool,
            updated_by: str = None) -> int:
        """批量更新产品状态"""
        count = 0
        for id in ids:
            product = self.product_repo.update(id, is_active=is_active)
            if product:
                count += 1

        if count > 0 and updated_by:
            self.log_repo.create_log(
                user_id=updated_by,
                action="batch_update",
                resource_type="product",
                detail=f"批量更新 {count} 个产品状态为 {'启用' if is_active else '禁用'}",
            )

        return count


class ProductDocumentService:
    """产品文档服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.doc_repo = ProductDocumentRepository(db)
        self.product_repo = ProductRepository(db)
        self.log_repo = OperationLogRepository(db)
        self.upload_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)))),
            "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        self.allowed_extensions = {
            "pdf",
            "dwg",
            "dxf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp",
        }
        self.max_file_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def get_documents(self, product_id: str) -> List[ProductDocument]:
        """获取产品文档列表"""
        return self.doc_repo.get_by_product_id(product_id)

    def upload_document(
        self,
        product_id: str,
        file_content: bytes,
        file_name: str,
        doc_type: str = "other",
        description: str = "",
        uploaded_by: str = None,
    ) -> ProductDocument:
        """上传产品文档"""
        # 验证产品存在
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError("产品不存在")

        # 验证文件类型
        if doc_type not in ["pdf", "cad", "report", "certificate", "other"]:
            raise ValueError("不支持的文件类型")

        # 验证文件名
        if not file_name or "." not in file_name:
            raise ValueError("无效的文件名")

        # 验证文件扩展名
        ext = file_name.rsplit(".", 1)[-1].lower()
        if ext not in self.allowed_extensions:
            raise ValueError(f"不支持的文件格式: .{ext}")

        # 验证文件大小
        if len(file_content) > self.max_file_size:
            raise ValueError(f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")

        if len(file_content) == 0:
            raise ValueError("文件内容为空")

        # 保存文件
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)

        # 创建文档记录
        doc = self.doc_repo.create(
            product_id=product_id,
            doc_type=doc_type,
            file_name=file_name,
            file_path=f"/uploads/{filename}",
            file_size=len(file_content),
            description=description,
        )
        if uploaded_by:
            self.log_repo.create_log(
                user_id=uploaded_by,
                action="upload",
                resource_type="document",
                resource_id=doc.id,
                detail=f"上传产品文档: {file_name}",
            )

        return doc

    def delete_document(self, doc_id: str, deleted_by: str = None) -> bool:
        """删除文档"""
        doc = self.doc_repo.get_by_id(doc_id)
        if not doc:
            return False

        # 删除物理文件
        file_path = os.path.join(
            self.upload_dir,
            os.path.basename(
                doc.file_path))
        if os.path.exists(file_path):
            os.remove(file_path)

        # 删除数据库记录
        success = self.doc_repo.delete(doc_id)
        if success and deleted_by:
            self.log_repo.create_log(
                user_id=deleted_by,
                action="delete",
                resource_type="document",
                resource_id=doc_id,
                detail=f"删除文档: {doc.file_name}",
            )

        return success
