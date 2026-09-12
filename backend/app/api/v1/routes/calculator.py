"""Calculator 路由 — 工程计算器（Thermal / Fire Protection / Quantity）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.db.session import get_db
from app.services.calculators.engine import fire_calc, quantity_calc, thermal_calc

router = APIRouter()


@router.post("/thermal", summary="热工计算器")
def calc_thermal(params: dict, db: Session = Depends(get_db)):
    """热工计算：U值 / 热损失 / 保温厚度估算。"""
    result = thermal_calc(params)
    if result.get("code") != 0:
        return error_response(result["code"], result.get("error", "计算失败"))
    return success_response(data=result)


@router.post("/fire-protection", summary="防火计算器")
def calc_fire(params: dict, db: Session = Depends(get_db)):
    """防火计算：钢构件防火涂料厚度估算。"""
    result = fire_calc(params)
    if result.get("code") != 0:
        return error_response(result["code"], result.get("error", "计算失败"))
    return success_response(data=result)


@router.post("/quantity", summary="数量/包装估算器")
def calc_quantity(params: dict, db: Session = Depends(get_db)):
    """数量/包装估算：体积、重量、包装数。"""
    result = quantity_calc(params)
    if result.get("code") != 0:
        return error_response(result["code"], result.get("error", "计算失败"))
    return success_response(data=result)
