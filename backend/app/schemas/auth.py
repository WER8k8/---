from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: "UserResponse"
    portals: Optional[dict] = None
    force_password_change: bool = False


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenRefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    is_default_password: bool = True


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailLoginRequest(BaseModel):
    email: EmailStr
    code: str


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str
    state: str
    provider: str


class ThirdPartyLoginRequest(BaseModel):
    provider: str  # qq, wechat, feishu, dingtalk
    code: str
    state: Optional[str] = None


class ThirdPartyLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse
    new_user: bool = False


class EmailVerificationResponse(BaseModel):
    message: str
    expires_in: int
    dev_code: Optional[str] = None
