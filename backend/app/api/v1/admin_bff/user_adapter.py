"""用户 BFF — HTTP 薄层"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.admin_bff.user_context import build_uac_user_info
from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/info")
async def get_user_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """get_user_info。

    参数说明：
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    info = build_uac_user_info(user, db)
    return success_response(data=info.model_dump())
