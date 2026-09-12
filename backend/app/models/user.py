"""用户模型 — 支持多角色、第三方登录、AI 推荐等。"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import UUID_TYPE, Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="viewer", nullable=False, index=True)
    role_id: Mapped[str | None] = mapped_column(UUID_TYPE, ForeignKey("admin_roles.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    third_party_logins = relationship("ThirdPartyLogin", back_populates="user")
    role_rel = relationship("AdminRole", back_populates="users", foreign_keys=[role_id], lazy="joined")
    notifications = relationship("Notification", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    orders_as_buyer = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    orders_as_merchant = relationship("Order", foreign_keys="Order.merchant_id", back_populates="merchant")
    quotes_as_merchant = relationship("Quote", foreign_keys="Quote.merchant_id", back_populates="merchant")
    merchant_profile = relationship("MerchantProfile", back_populates="user", uselist=False)
    ai_recommendations = relationship("AIRecommendation", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    sent_messages = relationship("IMMessage", foreign_keys="IMMessage.sender_id", back_populates="sender")
    received_messages = relationship("IMMessage", foreign_keys="IMMessage.receiver_id", back_populates="receiver")
    status = relationship("UserStatus", back_populates="user", uselist=False)
    ai_chat_sessions = relationship("AiChatSession", foreign_keys="AiChatSession.merchant_id", back_populates="merchant")
    knowledge_bases = relationship("AiKnowledgeBase", foreign_keys="AiKnowledgeBase.merchant_id", back_populates="merchant")


class ThirdPartyLogin(Base):
    __tablename__ = "third_party_logins"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # qq, wechat, email
    provider_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    access_token: Mapped[str | None] = mapped_column(String(500))
    refresh_token: Mapped[str | None] = mapped_column(String(500))
    token_expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    user = relationship("User", back_populates="third_party_logins")


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class OperationLog(Base):
    __tablename__ = "operation_logs"
    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(UUID_TYPE, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(50), index=True)
    detail: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
