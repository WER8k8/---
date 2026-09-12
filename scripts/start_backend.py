#!/usr/bin/env python3
"""启动后端服务脚本 - 简化版，禁用Redis依赖"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 设置环境变量禁用Redis
os.environ['REDIS_ENABLED'] = 'false'
os.environ['ENVIRONMENT'] = 'development'

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json

# 导入我们的用户模型和数据库
from app.models.user import User
from app.core.database import SessionLocal, engine, Base
from app.core.security import verify_password, create_access_token

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="优丁建材 API",
    description="超级管理员后端API",
    version="1.0.0",
)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 登录响应模型
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# 简单的API响应包装
class APIResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[dict] = None

# 登录接口
@app.post("/api/v1/auth/login", response_model=APIResponse)
async def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username, User.is_active == True).first()
        if not user or not verify_password(req.password, user.hashed_password):
            return APIResponse(code=401, message="用户名或密码错误")
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        
        return APIResponse(
            code=0,
            message="登录成功",
            data={
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
        )
    except Exception as e:
        print(f"登录错误: {e}")
        return APIResponse(code=500, message="服务器内部错误")
    finally:
        db.close()

# 健康检查
@app.get("/api/v1/health")
async def health_check():
    return APIResponse(code=0, message="success", data={"status": "healthy"})

# 首页
@app.get("/")
async def root():
    return APIResponse(code=0, message="success", data={"message": "超级管理员后端服务已启动"})

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动超级管理员后端服务...")
    print("📍 API地址: http://127.0.0.1:8000")
    print("📚 文档地址: http://127.0.0.1:8000/docs")
    print("👤 登录信息: admin / 123456")
    uvicorn.run(app, host="127.0.0.1", port=8000)
