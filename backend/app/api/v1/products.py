# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import csv
import io
import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.product import Category, Product, ProductDocument
from app.schemas.product import (CategoryCreate, CategoryResponse,
                                 CategoryTreeResponse, CategoryUpdate,
                                 ProductCreate, ProductDocumentResponse,
                                 ProductResponse, ProductUpdate)

UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)))),
    "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

DOCUMENT_TYPES = {
    "pdf": "规格书",
    "cad": "CAD图纸",
    "report": "检测报告",
    "certificate": "资质证书",
    "other": "其他",
}


class BatchDeleteRequest(BaseModel):
    ids: List[str]


class BatchUpdateStatusRequest(BaseModel):
    ids: List[str]
    is_active: bool


class ProductExportItem(BaseModel):
    id: str
    name: str
    slug: str
    category_id: str
    description: Optional[str]
    density: Optional[str]
    strength: Optional[str]
    is_active: bool


def build_category_tree(
        categories: list[Category],
        parent_id: str | None = None) -> list[dict]:
    """build_category_tree。

    参数说明：
    :param categories: 参数 categories
    :param parent_id: 参数 parent_id
    :return: 返回处理结果。
    """
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            children = build_category_tree(categories, cat.id)
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


@router.get("/categories/tree", response_model=list[CategoryTreeResponse])
def get_category_tree(db: Session = Depends(get_db)):
    """get_category_tree。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    categories = db.query(Category).order_by(Category.sort_order).all()
    return build_category_tree(categories)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """list_categories。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    return (
        db.query(Category) .options(
            joinedload(
                Category.parent).load_only(
                Category.id,
                Category.name)) .order_by(
                    Category.sort_order) .all())


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    """get_category。

    参数说明：
    :param category_id: 参数 category_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    return cat


@router.post("/categories", response_model=CategoryResponse)
def create_category(
        req: CategoryCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_category。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    cat = Category(**req.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
        category_id: str,
        req: CategoryUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_category。

    参数说明：
    :param category_id: 参数 category_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}")
def delete_category(
        category_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_category。

    参数说明：
    :param category_id: 参数 category_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return success_response(message="删除成功")


@router.get("")
def list_products(
    category_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """list_products。

    参数说明：
    :param category_id: 参数 category_id
    :param is_active: 参数 is_active
    :param search: 参数 search
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(Product)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))

    total = q.count()
    items = q.order_by(Product.sort_order).offset(
        (page - 1) * page_size).limit(page_size).all()
    return success_response(data={"items": items, "total": total})


@router.get("/by-slug/{slug}", response_model=ProductResponse)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    """get_product_by_slug。

    参数说明：
    :param slug: 参数 slug
    :param db: 参数 db
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(
        Product.slug == slug,
        Product.is_active).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    p.view_count += 1
    db.commit()
    return p


# ============= 导入导出API =============


@router.get("/export")
def export_products(
    category_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """export_products。

    参数说明：
    :param category_id: 参数 category_id
    :param is_active: 参数 is_active
    :param search: 参数 search
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    q = db.query(Product)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))

    products = q.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "产品名称", "Slug", "分类ID",
                    "描述", "密度", "强度", "状态", "创建时间"])

    for p in products:
        writer.writerow([p.id,
                         p.name,
                         p.slug,
                         p.category_id,
                         p.description or "",
                         p.density or "",
                         p.strength or "",
                         "启用" if p.is_active else "禁用",
                         p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
                         ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.post("/import")
async def import_products(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """import_products。

    参数说明：
    :param file: 参数 file
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持CSV文件")

    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
        reader = csv.DictReader(csv_content.splitlines())
        imported_count = 0
        errors = []
        for row in reader:
            try:
                # 检查slug是否已存在
                existing = db.query(Product).filter(
                    Product.slug == row.get("slug")).first()
                if existing:
                    errors.append(f"产品 {row.get('name')} 的slug已存在")
                    continue

                product = Product(
                    name=row.get("name"),
                    slug=row.get("slug"),
                    category_id=row.get("category_id"),
                    description=row.get("description"),
                    density=row.get("density"),
                    strength=row.get("strength"),
                    is_active=True if row.get("状态") == "启用" else False,
                )
                db.add(product)
                imported_count += 1
            except (ValueError, TypeError, Exception) as e:
                logger = logging.getLogger(__name__)
                logger.warning("导入产品失败: %s", e)
                errors.append(f"导入产品 {row.get('name')} 失败: {str(e)}")

        db.commit()
        if errors:
            return success_response(data={"imported_count": imported_count, "errors": errors})
        return success_response(data={"imported_count": imported_count})

    except (ValueError, TypeError, Exception) as e:
        logger = logging.getLogger(__name__)
        logger.error("文件解析失败: %s", e)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """get_product。

    参数说明：
    :param product_id: 参数 product_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    return p


@router.post("", response_model=ProductResponse)
def create_product(
        req: ProductCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_product。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    p = Product(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
        product_id: str,
        req: ProductUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_product。

    参数说明：
    :param product_id: 参数 product_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{product_id}")
def delete_product(
        product_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_product。

    参数说明：
    :param product_id: 参数 product_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(p)
    db.commit()
    return success_response(message="删除成功")


@router.get("/{product_id}/documents",
            response_model=list[ProductDocumentResponse])
def list_product_documents(product_id: str, db: Session = Depends(get_db)):
    """list_product_documents。

    参数说明：
    :param product_id: 参数 product_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    return (
        db.query(ProductDocument) .filter(
            ProductDocument.product_id == product_id,
            ProductDocument.is_active) .order_by(
            ProductDocument.sort_order) .all())


@router.post("/{product_id}/documents", response_model=ProductDocumentResponse)
async def upload_product_document(
    product_id: str,
    file: UploadFile = File(...),
    doc_type: str = "other",
    description: str = "",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """upload_product_document。

    参数说明：
    :param product_id: 参数 product_id
    :param file: 参数 file
    :param doc_type: 参数 doc_type
    :param description: 参数 description
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")

    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {doc_type}")

    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    ALLOWED_DOC_EXTENSIONS = {
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
        "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: .{ext}")

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")

    with open(filepath, "wb") as f:
        f.write(content)

    doc = ProductDocument(
        product_id=product_id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=f"/uploads/{filename}",
        file_size=len(content),
        description=description,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}")
def delete_product_document(
        doc_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_product_document。

    参数说明：
    :param doc_id: 参数 doc_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    doc = db.query(ProductDocument).filter(
        ProductDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    file_path = os.path.join(UPLOAD_DIR, os.path.basename(doc.file_path))
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(doc)
    db.commit()
    return success_response(message="删除成功")


@router.post("/{product_id}/increment-view")
def increment_product_view(product_id: str, db: Session = Depends(get_db)):
    """increment_product_view。

    参数说明：
    :param product_id: 参数 product_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    p = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    p.view_count += 1
    db.commit()
    return success_response(data={"view_count": p.view_count})


# ============= 批量操作API =============


@router.post("/batch-delete")
def batch_delete_products(
        req: BatchDeleteRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_delete_products。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not req.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的产品")

    deleted = db.query(Product).filter(
        Product.id.in_(
            req.ids)).delete(
        synchronize_session=False)
    db.commit()
    return success_response(data={"message": f"成功删除 {deleted} 个产品", "deleted_count": deleted})


@router.post("/batch-update-status")
def batch_update_status(
        req: BatchUpdateStatusRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_update_status。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not req.ids:
        raise HTTPException(status_code=400, detail="请选择要更新的产品")

    updated = (
        db.query(Product)
        .filter(Product.id.in_(req.ids))
        .update({"is_active": req.is_active}, synchronize_session=False)
    )
    db.commit()
    return success_response(data={"message": f"成功更新 {updated} 个产品状态", "updated_count": updated})
