import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.models.product import Category, Product, ProductDocument
from app.schemas.product import CategoryCreate, CategoryUpdate, ProductCreate, ProductUpdate, ProductResponse, CategoryResponse, CategoryTreeResponse, ProductDocumentCreate, ProductDocumentResponse
from typing import Optional

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

DOCUMENT_TYPES = {
    "pdf": "规格书",
    "cad": "CAD图纸",
    "report": "检测报告",
    "certificate": "资质证书",
    "other": "其他",
}


def build_category_tree(categories: list[Category], parent_id: str | None = None) -> list[dict]:
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            children = build_category_tree(categories, cat.id)
            tree.append(CategoryTreeResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                parent_id=cat.parent_id,
                sort_order=cat.sort_order,
                is_active=cat.is_active,
                created_at=cat.created_at,
                children=children,
            ))
    return tree


@router.get("/categories/tree", response_model=list[CategoryTreeResponse])
def get_category_tree(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.sort_order).all()
    return build_category_tree(categories)

@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.sort_order).all()

@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    return cat

@router.post("/categories", response_model=CategoryResponse)
def create_category(req: CategoryCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    cat = Category(**req.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: str, req: CategoryUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categories/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "删除成功"}

@router.get("")
def list_products(
    category_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    
    total = q.count()
    items = q.order_by(Product.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total}

@router.get("/by-slug/{slug}", response_model=ProductResponse)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    p.view_count += 1
    db.commit()
    return p

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    return p

@router.post("", response_model=ProductResponse)
def create_product(req: ProductCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    p = Product(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, req: ProductUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p

@router.delete("/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(p)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{product_id}/documents", response_model=list[ProductDocumentResponse])
def list_product_documents(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    return db.query(ProductDocument).filter(
        ProductDocument.product_id == product_id,
        ProductDocument.is_active == True
    ).order_by(ProductDocument.sort_order).all()


@router.post("/{product_id}/documents", response_model=ProductDocumentResponse)
async def upload_product_document(
    product_id: str,
    file: UploadFile = File(...),
    doc_type: str = "other",
    description: str = "",
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")

    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {doc_type}")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")
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
def delete_product_document(doc_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    doc = db.query(ProductDocument).filter(ProductDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    file_path = os.path.join(UPLOAD_DIR, os.path.basename(doc.file_path))
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(doc)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{product_id}/increment-view")
def increment_product_view(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="产品不存在")
    p.view_count += 1
    db.commit()
    return {"view_count": p.view_count}