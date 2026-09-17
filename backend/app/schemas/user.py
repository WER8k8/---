# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from datetime import datetime
from typing import List, Optional

from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    @field_validator("id", mode="before")
    @classmethod
    def _id_to_str(cls, v):
        """_id_to_str。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        if isinstance(v, UUID):
            return str(v)
        return v

    username: str
    email: str
    display_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserStatusUpdate(BaseModel):
    is_active: bool
