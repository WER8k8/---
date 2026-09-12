"""
Merchant Profiles API Router - 商家资料API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.response import success_response
from app.models.merchant_profile import MerchantProfile
from app.models.user import User

router = APIRouter(prefix="/api/v1/merchant-profiles", tags=["merchant-profiles"])


@router.post("/", response_model=dict)
def create_merchant_profile(
    user_id: str,
    company_name: str,
    company_address: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    business_license: Optional[str] = None,
    contact_person: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    wechat_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建商家资料"""
    try:
        profile = MerchantProfile(
            user_id=uuid.UUID(user_id),
            company_name=company_name,
            company_address=company_address,
            country=country,
            city=city,
            business_license=business_license,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone,
            whatsapp_number=whatsapp_number,
            wechat_id=wechat_id,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return success_response(data={"id": str(profile.id), "company_name": profile.company_name, "verified": profile.verified})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{profile_id}", response_model=dict)
def get_merchant_profile(profile_id: str, db: Session = Depends(get_db)):
    """获取商家资料详情"""
    profile = db.query(MerchantProfile).filter(MerchantProfile.id == uuid.UUID(profile_id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Merchant profile not found")
    
    return success_response(data={
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "company_name": profile.company_name,
        "company_address": profile.company_address,
        "country": profile.country,
        "city": profile.city,
        "verified": profile.verified,
        "contact_person": profile.contact_person,
        "contact_email": profile.contact_email,
        "whatsapp_number": profile.whatsapp_number,
        "wechat_id": profile.wechat_id,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    })


@router.put("/{profile_id}", response_model=dict)
def update_merchant_profile(
    profile_id: str,
    company_name: Optional[str] = None,
    company_address: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    verified: Optional[bool] = None,
    contact_person: Optional[str] = None,
    contact_email: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    wechat_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新商家资料"""
    profile = db.query(MerchantProfile).filter(MerchantProfile.id == uuid.UUID(profile_id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Merchant profile not found")
    
    if company_name is not None:
        profile.company_name = company_name
    if company_address is not None:
        profile.company_address = company_address
    if country is not None:
        profile.country = country
    if city is not None:
        profile.city = city
    if verified is not None:
        profile.verified = verified
    if contact_person is not None:
        profile.contact_person = contact_person
    if contact_email is not None:
        profile.contact_email = contact_email
    if whatsapp_number is not None:
        profile.whatsapp_number = whatsapp_number
    if wechat_id is not None:
        profile.wechat_id = wechat_id
    
    db.commit()
    db.refresh(profile)
    return success_response(data={"id": str(profile.id), "company_name": profile.company_name, "verified": profile.verified})


@router.delete("/{profile_id}")
def delete_merchant_profile(profile_id: str, db: Session = Depends(get_db)):
    """删除商家资料"""
    profile = db.query(MerchantProfile).filter(MerchantProfile.id == uuid.UUID(profile_id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Merchant profile not found")
    
    db.delete(profile)
    db.commit()
    return success_response(message="Merchant profile deleted successfully")


@router.get("/", response_model=List[dict])
def list_merchant_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """列出商家资料（支持过滤）"""
    query = db.query(MerchantProfile)
    if verified is not None:
        query = query.filter(MerchantProfile.verified == verified)
    
    profiles = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(p.id),
            "company_name": p.company_name,
            "country": p.country,
            "city": p.city,
            "verified": p.verified,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in profiles
    ]
