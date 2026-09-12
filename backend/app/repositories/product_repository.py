"""产品数据访问层"""

from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.product import Category, Product, ProductDocument
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """分类Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, Category)

    def get_tree(self, parent_id: str = None) -> List[Category]:
        """获取分类树"""
        return (
            self.db.execute(
                select(Category).filter(
                    Category.parent_id == parent_id).order_by(
                    Category.sort_order)) .scalars() .all())

    def get_all_with_parent(self) -> List[Category]:
        """获取所有分类（包含父分类信息）"""
        return (
            self.db.execute(
                select(Category) .options(
                    joinedload(
                        Category.parent).load_only(
                        Category.id,
                        Category.name)) .order_by(
                    Category.sort_order)) .scalars() .all())

    def get_by_slug(self, slug: str) -> Optional[Category]:
        """根据slug获取分类"""
        return self.db.execute(
            select(Category).filter(Category.slug == slug, Category.is_active)
        ).scalar_one_or_none()


class ProductRepository(BaseRepository[Product]):
    """产品Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, Product)

    def get_paginated_with_category(self,
                                    page: int = 1,
                                    page_size: int = 20,
                                    category_id: str = None,
                                    is_active: bool = None,
                                    search: str = None) -> Tuple[List[Product],
                                                                 int]:
        """分页获取产品（含分类信息）"""
        query = select(Product).options(joinedload(Product.category))
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))

        total = self.db.scalar(
            select(
                func.count()).select_from(
                query.subquery()))
        items = (
            self.db.execute(
                query.order_by(
                    Product.sort_order).offset(
                    (page - 1) * page_size).limit(page_size)) .scalars() .all())

        return items, total

    def get_by_slug(self, slug: str) -> Optional[Product]:
        """根据slug获取产品"""
        return self.db.execute(
            select(Product)
            .options(joinedload(Product.category))
            .filter(Product.slug == slug, Product.is_active)
        ).scalar_one_or_none()

    def exists_by_slug(self, slug: str, exclude_id: str = None) -> bool:
        """检查slug是否存在"""
        query = select(Product).filter(Product.slug == slug)
        if exclude_id:
            query = query.filter(Product.id != exclude_id)
        return self.db.execute(query).scalar() is not None

    def increment_view_count(self, product_id: str) -> bool:
        """增加浏览次数"""
        product = self.get_by_id(product_id)
        if product:
            product.view_count += 1
            self.db.commit()
            return True
        return False

    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """获取热门产品（按浏览量排序）"""
        return (
            self.db.execute(
                select(Product).filter(
                    Product.is_active).order_by(
                    desc(
                        Product.view_count)).limit(limit)) .scalars() .all())

    def get_products_by_category(self, category_id: str) -> List[Product]:
        """获取指定分类的产品"""
        return (
            self.db.execute(
                select(Product)
                .filter(Product.category_id == category_id, Product.is_active)
                .order_by(Product.sort_order)
            )
            .scalars()
            .all()
        )


class ProductDocumentRepository(BaseRepository[ProductDocument]):
    """产品文档Repository"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        super().__init__(db, ProductDocument)

    def get_by_product_id(self, product_id: str) -> List[ProductDocument]:
        """获取产品文档列表"""
        return (
            self.db.execute(
                select(ProductDocument) .filter(
                    ProductDocument.product_id == product_id,
                    ProductDocument.is_active) .order_by(
                    ProductDocument.sort_order)) .scalars() .all())

    def delete_by_product_id(self, product_id: str) -> int:
        """删除产品的所有文档"""
        result = self.db.execute(
            ProductDocument.__table__.delete().where(
                ProductDocument.product_id == product_id))
        self.db.commit()
        return result.rowcount
