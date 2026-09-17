# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""用户钱包路由"""
import logging
import os

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.user_wallet_service import (
    deposit,
    get_monthly_stats,
    get_transactions,
    get_wallet_summary,
    transfer,
    withdraw,
)

log = logging.getLogger(__name__)
ROUTE_PREFIX = ""
router = APIRouter(prefix='/wallet', tags=['用户钱包'])


def _wallet_deposit_allowed(db: Session) -> tuple[bool, str | None]:
    """未配置支付渠道且未显式允许 mock 时禁止假充值到账。"""
    from app.services.b2b_deposit_payment_service import probe_deposit_channels
    probe = probe_deposit_channels(db)
    if probe.get('any_channel_ready') or probe.get('mock_allowed'):
        return True, None
    return False, 'PAYMENT_CHANNEL_NOT_CONFIGURED'


@router.get('/balance', summary='查询余额', operation_id='get_wallet_balance', description='Getbalance (Wallet)。\n\n模块: Wallet\n方法: GET\n路径: /balance\n\n查询操作，幂等，无副作用。\n\n认证: 需要有效 JWT (get_current_user)')
def get_balance(current_user=Depends(get_current_user)):
    """查询当前用户钱包余额"""
    try:
        summary = get_wallet_summary(str(current_user.id))
        balances = summary.balances or {}
        cny = int(balances.get('CNY', 0))
        return success_response(
            data={'balance': cny / 100.0, 'balances': {k: v / 100.0 for k, v in balances.items()}},
            message='余额查询成功',
        )
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        log.exception('查询余额失败')
        return error_response(500, f'查询失败: {e}')


@router.post('/deposit', summary='充值', operation_id='wallet_post_deposit', response_model=APIResponse, description='Createdeposit (Wallet)。\n\n模块: Wallet\n方法: POST\n路径: /deposit\n\n创建操作，可能包含副作用：数据库写入、缓存失效、外部API调用。\n\n认证: 需要有效 JWT (get_current_user)')
def deposit_route(
    amount: float = Body(..., embed=True),
    currency: str = Body('CNY', embed=True),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """充值到钱包（amount 单位：元；须支付渠道或 dev mock）。"""
    allowed, _code = _wallet_deposit_allowed(db)
    if not allowed:
        return error_response(
            503,
            '支付渠道未配置，无法充值（PAYMENT_CHANNEL_NOT_CONFIGURED）；禁止假到账',
        )
    try:
        cents = max(1, int(round(float(amount) * 100)))
        result = deposit(str(current_user.id), cents, currency)
        if not result.success:
            return error_response(400, result.error or '充值失败')
        payload: dict = {'tx_id': result.tx_id, 'balance_after': result.balance_after / 100.0}
        if os.getenv('PAYMENT_ALLOW_MOCK', '0').lower() in ('1', 'true', 'yes'):
            payload['mode'] = 'mock'
        return success_response(data=payload, message='充值成功')
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        log.exception('充值失败')
        return error_response(500, f'充值失败: {e}')

@router.post('/withdraw', summary='提现申请', operation_id='wallet_withdraw', response_model=APIResponse, description='Createwithdraw (Wallet)。\n\n模块: Wallet\n方法: POST\n路径: /withdraw\n\n创建操作，可能包含副作用：数据库写入、缓存失效、外部API调用。\n\n认证: 需要有效 JWT (get_current_user)')
def withdraw_route(amount: int=Body(..., embed=True), currency: str=Body('CNY', embed=True), current_user=Depends(get_current_user)):
    """申请提现（amount 单位：分）"""
    try:
        result = withdraw(str(current_user.id), amount, currency)
        if not result.success:
            return error_response(400, result.error or '提现失败')
        return success_response(
            data={'tx_id': result.tx_id, 'balance_after': result.balance_after / 100.0},
            message='提现申请已提交',
        )
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        log.exception('提现失败')
        return error_response(500, f'提现失败: {e}')

@router.post('/transfer', summary='转账', operation_id='wallet_transfer', response_model=APIResponse, description='Createtransfer (Wallet)。\n\n模块: Wallet\n方法: POST\n路径: /transfer\n\n创建操作，可能包含副作用：数据库写入、缓存失效、外部API调用。\n\n认证: 需要有效 JWT (get_current_user)')
def transfer_route(to_user_id: int=Body(...), amount: int=Body(...), currency: str=Body('CNY'), current_user=Depends(get_current_user)):
    """向其他用户转账（amount 单位：分）"""
    try:
        result = transfer(str(current_user.id), str(to_user_id), amount, currency)
        return success_response(data={'tx_id': result.tx_id, 'balance_after': result.balance_after}, message='转账成功')
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        log.exception('转账失败')
        return error_response(500, f'转账失败: {e}')

@router.get('/transactions', summary='交易记录', operation_id='list_wallet_transactions', description='Gettransactions (Wallet)。\n\n模块: Wallet\n方法: GET\n路径: /transactions\n\n查询操作，幂等，无副作用。\n\n认证: 需要有效 JWT (get_current_user)')
def transactions(current_user=Depends(get_current_user)):
    """查询交易记录"""
    try:
        txs = get_transactions(str(current_user.id))
        return success_response(data=txs, message=f'共 {len(txs)} 条交易记录')
    except Exception as e:
        log.exception('查询交易记录失败')
        return error_response(500, f'查询失败: {e}')


@router.get(
    '/monthly-stats',
    summary='本月钱包聚合',
    operation_id='get_wallet_monthly_stats',
    description=(
        'Get monthly-stats (Wallet)。\n\n模块: Wallet\n方法: GET\n路径: /monthly-stats\n\n'
        '查询操作，幂等，无副作用。金额单位：元。data_source=memory|redis，非 PG ledger。\n\n'
        '认证: 需要有效 JWT (get_current_user)'
    ),
)
def monthly_stats(current_user=Depends(get_current_user)):
    """当前自然月充值/消费/提现聚合（来自内存流水，空月诚实 0）。"""
    try:
        raw = get_monthly_stats(str(current_user.id))
        return success_response(
            data={
                'year_month': raw['year_month'],
                'deposit': raw['deposit'] / 100.0,
                'consume': raw['consume'] / 100.0,
                'withdraw': raw['withdraw'] / 100.0,
                'data_source': raw['data_source'],
            },
            message='本月钱包统计',
        )
    except Exception as e:
        log.exception('查询钱包月统计失败')
        return error_response(500, f'查询失败: {e}')