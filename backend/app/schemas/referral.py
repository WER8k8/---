"""客户裂变推荐系统 Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReferralCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    total_referred: int = 0
    total_earned: int = 0
    invite_link: str = ""
    created_at: datetime


class ReferralRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inviter_name: Optional[str] = None
    invited_name: Optional[str] = None
    status: str
    reward_type: Optional[str] = None
    reward_amount: int = 0
    invited_at: datetime
    rewarded_at: Optional[datetime] = None


class ReferralStatsResponse(BaseModel):
    total_invited: int = 0
    total_rewarded: int = 0
    pending_rewards: int = 0
    current_tier: int = 0
    next_tier_at: int = 0
    next_tier_reward: str = ""
    estimated_discount: int = 0


class ReferralLeaderboardItem(BaseModel):
    company_name: str
    invite_count: int
    rank: int


class ApplyReferralResponse(BaseModel):
    success: bool
    message: str = ""
    extra_days: int = 0
