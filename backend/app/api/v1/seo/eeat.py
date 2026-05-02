from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from app.services.eeat_scorer import EEATScorer
from app.models.eeat import Author, AuthorCertification, ArticleAuthor, EEATScore, TrustSignal
from app.core.database import get_db

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
eeat_scorer = EEATScorer()

# 作者管理

@router.post("/authors", summary="创建作者", response_model=Dict)
def create_author(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """创建新作者/专家"""
    author = Author(
        id=str(uuid4()),
        name=data.get("name"),
        bio=data.get("bio"),
        title=data.get("title"),
        company=data.get("company"),
        email=data.get("email"),
        linkedin_url=data.get("linkedin_url"),
        twitter_url=data.get("twitter_url"),
        expertise_areas=data.get("expertise_areas"),
        credentials=data.get("credentials"),
        is_verified=data.get("is_verified", False),
        trust_score=data.get("trust_score", 0.0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(author)
    db.commit()
    db.refresh(author)
    
    return {"success": True, "author": {
        "id": author.id,
        "name": author.name,
        "title": author.title,
        "company": author.company,
        "is_verified": author.is_verified,
        "trust_score": author.trust_score,
    }}

@router.get("/authors", summary="获取作者列表", response_model=Dict)
def get_authors(
    page: int = 1,
    limit: int = 10,
    verified_only: bool = False,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取作者列表"""
    query = db.query(Author)
    if verified_only:
        query = query.filter(Author.is_verified == True)
    
    authors = query.offset((page - 1) * limit).limit(limit).all()
    total = query.count()
    
    return {"success": True, "data": [
        {
            "id": a.id,
            "name": a.name,
            "title": a.title,
            "company": a.company,
            "is_verified": a.is_verified,
            "trust_score": a.trust_score,
            "expertise_areas": a.expertise_areas,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        } for a in authors
    ], "total": total}

@router.get("/authors/{author_id}", summary="获取作者详情", response_model=Dict)
def get_author(
    author_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取单个作者详情"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    # 获取认证信息
    certifications = db.query(AuthorCertification)\
        .filter(AuthorCertification.author_id == author_id)\
        .all()
    
    return {"success": True, "author": {
        "id": author.id,
        "name": author.name,
        "bio": author.bio,
        "title": author.title,
        "company": author.company,
        "email": author.email,
        "linkedin_url": author.linkedin_url,
        "twitter_url": author.twitter_url,
        "expertise_areas": author.expertise_areas,
        "credentials": author.credentials,
        "is_verified": author.is_verified,
        "trust_score": author.trust_score,
        "certifications": [{
            "id": c.id,
            "certification_name": c.certification_name,
            "issuing_body": c.issuing_body,
            "issue_date": c.issue_date.isoformat() if c.issue_date else None,
            "is_valid": c.is_valid,
        } for c in certifications],
        "created_at": author.created_at.isoformat() if author.created_at else None,
    }}

@router.put("/authors/{author_id}", summary="更新作者", response_model=Dict)
def update_author(
    author_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """更新作者信息"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    if "name" in data:
        author.name = data["name"]
    if "bio" in data:
        author.bio = data["bio"]
    if "title" in data:
        author.title = data["title"]
    if "company" in data:
        author.company = data["company"]
    if "email" in data:
        author.email = data["email"]
    if "linkedin_url" in data:
        author.linkedin_url = data["linkedin_url"]
    if "twitter_url" in data:
        author.twitter_url = data["twitter_url"]
    if "expertise_areas" in data:
        author.expertise_areas = data["expertise_areas"]
    if "credentials" in data:
        author.credentials = data["credentials"]
    if "is_verified" in data:
        author.is_verified = data["is_verified"]
    if "trust_score" in data:
        author.trust_score = data["trust_score"]
    
    author.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(author)
    
    return {"success": True, "message": "作者信息已更新"}

@router.delete("/authors/{author_id}", summary="删除作者", response_model=Dict)
def delete_author(
    author_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """删除作者"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    # 删除关联数据
    db.query(AuthorCertification)\
        .filter(AuthorCertification.author_id == author_id)\
        .delete()
    db.query(ArticleAuthor)\
        .filter(ArticleAuthor.author_id == author_id)\
        .delete()
    
    db.delete(author)
    db.commit()
    
    return {"success": True, "message": "作者已删除"}

# 认证管理

@router.post("/authors/{author_id}/certifications", summary="添加认证", response_model=Dict)
def add_certification(
    author_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """为作者添加专业认证"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    certification = AuthorCertification(
        id=str(uuid4()),
        author_id=author_id,
        certification_name=data.get("certification_name"),
        issuing_body=data.get("issuing_body"),
        issue_date=datetime.fromisoformat(data.get("issue_date")) if data.get("issue_date") else None,
        expiration_date=datetime.fromisoformat(data.get("expiration_date")) if data.get("expiration_date") else None,
        credential_number=data.get("credential_number"),
        is_valid=data.get("is_valid", True),
        created_at=datetime.utcnow(),
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    
    # 更新作者信任分数
    author.trust_score = min(author.trust_score + 5, 100)
    db.commit()
    
    return {"success": True, "certification": {
        "id": certification.id,
        "certification_name": certification.certification_name,
        "issuing_body": certification.issuing_body,
    }}

@router.delete("/certifications/{cert_id}", summary="删除认证", response_model=Dict)
def delete_certification(
    cert_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """删除认证"""
    cert = db.query(AuthorCertification).filter(AuthorCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="认证不存在")
    
    author_id = cert.author_id
    db.delete(cert)
    
    # 更新作者信任分数
    author = db.query(Author).filter(Author.id == author_id).first()
    if author:
        author.trust_score = max(author.trust_score - 5, 0)
    
    db.commit()
    
    return {"success": True, "message": "认证已删除"}

# EEAT评分

@router.post("/score", summary="计算EEAT分数", response_model=Dict)
def calculate_eeat_score(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """计算内容的EEAT分数"""
    content_id = data.get("content_id")
    content_type = data.get("content_type", "article")
    content_data = data.get("content_data", {})
    
    result = eeat_scorer.evaluate_eeat(content_data)
    
    # 保存评分记录
    score_record = EEATScore(
        id=str(uuid4()),
        content_id=content_id,
        content_type=content_type,
        experience_score=result["experience_score"],
        expertise_score=result["expertise_score"],
        authoritativeness_score=result["authoritativeness_score"],
        trustworthiness_score=result["trustworthiness_score"],
        overall_score=result["overall_score"],
        factors=result["factors"],
        recommendations=result["recommendations"],
        evaluated_at=datetime.utcnow(),
    )
    db.add(score_record)
    db.commit()
    
    return {"success": True, "score": result}

@router.get("/score/{content_id}", summary="获取内容EEAT分数", response_model=Dict)
def get_eeat_score(
    content_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取内容的EEAT评分记录"""
    scores = db.query(EEATScore)\
        .filter(EEATScore.content_id == content_id)\
        .order_by(EEATScore.evaluated_at.desc())\
        .all()
    
    if not scores:
        return {"success": False, "message": "未找到评分记录"}
    
    latest_score = scores[0]
    
    return {"success": True, "score": {
        "id": latest_score.id,
        "content_id": latest_score.content_id,
        "content_type": latest_score.content_type,
        "experience_score": latest_score.experience_score,
        "expertise_score": latest_score.expertise_score,
        "authoritativeness_score": latest_score.authoritativeness_score,
        "trustworthiness_score": latest_score.trustworthiness_score,
        "overall_score": latest_score.overall_score,
        "factors": latest_score.factors,
        "recommendations": latest_score.recommendations,
        "evaluated_at": latest_score.evaluated_at.isoformat() if latest_score.evaluated_at else None,
    }}

@router.get("/scores", summary="获取评分列表", response_model=Dict)
def get_eeat_scores(
    page: int = 1,
    limit: int = 10,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取EEAT评分记录列表"""
    query = db.query(EEATScore)
    if content_type:
        query = query.filter(EEATScore.content_type == content_type)
    
    scores = query.offset((page - 1) * limit).limit(limit).all()
    total = query.count()
    
    return {"success": True, "data": [
        {
            "id": s.id,
            "content_id": s.content_id,
            "content_type": s.content_type,
            "overall_score": s.overall_score,
            "evaluated_at": s.evaluated_at.isoformat() if s.evaluated_at else None,
        } for s in scores
    ], "total": total}

# 信任信号

@router.get("/trust-signals", summary="获取信任信号分类", response_model=Dict)
def get_trust_signals(token: str = Depends(oauth2_scheme)):
    """获取信任信号分类"""
    categories = eeat_scorer.get_trust_signal_categories()
    return {"success": True, "categories": categories}

@router.post("/content/{content_id}/trust-signals", summary="添加信任信号", response_model=Dict)
def add_trust_signal(
    content_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """为内容添加信任信号"""
    signal = TrustSignal(
        id=str(uuid4()),
        content_id=content_id,
        signal_type=data.get("signal_type"),
        signal_value=data.get("signal_value"),
        score_impact=data.get("score_impact", 0.0),
        is_positive=data.get("is_positive", True),
        created_at=datetime.utcnow(),
    )
    db.add(signal)
    db.commit()
    
    return {"success": True, "signal": {
        "id": signal.id,
        "signal_type": signal.signal_type,
        "score_impact": signal.score_impact,
    }}

@router.get("/content/{content_id}/trust-signals", summary="获取内容信任信号", response_model=Dict)
def get_content_trust_signals(
    content_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取内容的信任信号列表"""
    signals = db.query(TrustSignal)\
        .filter(TrustSignal.content_id == content_id)\
        .all()
    
    return {"success": True, "signals": [
        {
            "id": s.id,
            "signal_type": s.signal_type,
            "signal_value": s.signal_value,
            "score_impact": s.score_impact,
            "is_positive": s.is_positive,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in signals
    ]}

# 文章-作者关联

@router.post("/articles/{article_id}/authors", summary="关联作者到文章", response_model=Dict)
def add_article_author(
    article_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """将作者关联到文章"""
    author_id = data.get("author_id")
    
    # 检查作者是否存在
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")
    
    # 检查是否已关联
    existing = db.query(ArticleAuthor)\
        .filter(ArticleAuthor.article_id == article_id)\
        .filter(ArticleAuthor.author_id == author_id)\
        .first()
    if existing:
        raise HTTPException(status_code=400, detail="作者已关联到该文章")
    
    article_author = ArticleAuthor(
        id=str(uuid4()),
        article_id=article_id,
        author_id=author_id,
        author_type=data.get("author_type", "primary"),
        role=data.get("role"),
        created_at=datetime.utcnow(),
    )
    db.add(article_author)
    db.commit()
    
    return {"success": True, "article_author": {
        "id": article_author.id,
        "article_id": article_author.article_id,
        "author_id": article_author.author_id,
        "author_type": article_author.author_type,
    }}

@router.delete("/articles/{article_id}/authors/{author_id}", summary="取消文章作者关联", response_model=Dict)
def remove_article_author(
    article_id: str,
    author_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """取消文章与作者的关联"""
    article_author = db.query(ArticleAuthor)\
        .filter(ArticleAuthor.article_id == article_id)\
        .filter(ArticleAuthor.author_id == author_id)\
        .first()
    
    if not article_author:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    db.delete(article_author)
    db.commit()
    
    return {"success": True, "message": "关联已取消"}
