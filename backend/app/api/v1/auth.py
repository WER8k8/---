from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
import logging
import json
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# 使用文件持久化登录尝试记录
LOGIN_ATTEMPTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "login_attempts.json")
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 15

def load_login_attempts():
    try:
        if os.path.exists(LOGIN_ATTEMPTS_FILE):
            with open(LOGIN_ATTEMPTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换时间字符串为datetime对象
                for key in data:
                    data[key][1] = datetime.fromisoformat(data[key][1])
                return data
    except Exception as e:
        logger.warning(f"加载登录尝试记录失败: {e}")
    return {}

def save_login_attempts(attempts):
    try:
        data = {}
        for key in attempts:
            # 转换datetime为字符串
            data[key] = [attempts[key][0], attempts[key][1].isoformat()]
        with open(LOGIN_ATTEMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"保存登录尝试记录失败: {e}")

LOGIN_ATTEMPTS = load_login_attempts()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now()
    
    login_key = f"{client_ip}:{req.username}"
    if login_key in LOGIN_ATTEMPTS:
        attempts, lockout_until = LOGIN_ATTEMPTS[login_key]
        if attempts >= MAX_LOGIN_ATTEMPTS and lockout_until > now:
            remaining = int((lockout_until - now).total_seconds())
            raise HTTPException(
                status_code=429,
                detail=f"登录尝试次数过多，请{remaining}秒后再试"
            )
        if lockout_until <= now:
            LOGIN_ATTEMPTS[login_key] = (0, now)
    
    user = db.query(User).filter(User.username == req.username, User.is_active == True).first()
    if not user or not verify_password(req.password, user.hashed_password):
        if login_key in LOGIN_ATTEMPTS:
            attempts, _ = LOGIN_ATTEMPTS[login_key]
            LOGIN_ATTEMPTS[login_key] = (attempts + 1, now + timedelta(minutes=LOCKOUT_DURATION))
        else:
            LOGIN_ATTEMPTS[login_key] = (1, now + timedelta(minutes=LOCKOUT_DURATION))
        save_login_attempts(LOGIN_ATTEMPTS)
        
        logger.warning(f"登录失败: username={req.username}, ip={client_ip}")
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if login_key in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[login_key]
        save_login_attempts(LOGIN_ATTEMPTS)
    
    user.last_login = now
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    logger.info(f"登录成功: username={req.username}, ip={client_ip}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        }
    }

@router.post("/logout")
def logout():
    return {"message": "登出成功"}
