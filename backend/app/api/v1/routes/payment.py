"""支付路由 - 支付订单创建、查询、回调、套餐查询"""
import json
import logging
import os
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant, TenantPlan
from app.models.user import User
from app.services.payment_service import PaymentService
from app.core.config import settings

# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/payment"
ROUTE_TAGS = ["支付管理"]

router = APIRouter(tags=['支付管理'])
log = logging.getLogger(__name__)

def _emit_payment_success_event(order) -> None:
    """支付成功后发布事件（不影响主流程）。"""
    try:
        from app.core.payment_events import emit_payment_event
        emit_payment_event(event_type='payment.success', order_id=str(order.id), user_id=str(getattr(order, 'user_id', '')), tenant_id=str(getattr(order, 'tenant_id', '')), amount=order.amount, currency=getattr(order, 'currency', 'CNY'), channel=order.channel or 'unknown')
    except Exception as exc:
        log.debug('[Payment] 事件发布失败（不影响主流程）: %s', exc)
PAYMENT_ACCESS_ROLES = frozenset({'admin', 'super_admin', 'tenant_admin', 'agent', 'l2', 'l3', 'editor', 'sales', 'viewer'})
PAYMENT_OPS_ADMIN_ROLES = frozenset({'admin', 'super_admin'})

def _payment_allowed(user: User):
    """执行 payment_allowed 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if user.role not in PAYMENT_ACCESS_ROLES:
        return error_response(403, '权限不足')
    return None

def _payment_ops_allowed(user: User):
    """执行 payment_ops_allowed 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if user.role not in PAYMENT_OPS_ADMIN_ROLES:
        return error_response(403, '需平台管理员权限')
    return None

class CreatePaymentRequest(BaseModel):
    tenant_id: str
    subscription_id: str
    amount: int
    channel: str
    subject: str
    currency: str = 'CNY'

class CreateNativePaymentRequest(BaseModel):
    """创建 Native 扫码支付（微信 / 支付宝）"""
    tenant_id: str
    plan_id: str
    billing_cycle: str = 'monthly'
    channel: str = Field('wechat', pattern='^(wechat|alipay)$')

class NotifyRequest(BaseModel):
    channel: str
    data: dict
    signature: str = Field(default='', description='网关签名；生产环境 PAYMENT_STRICT_VERIFY=1 时必填')

class MockPayRequest(BaseModel):
    order_id: str

class AlipayProbeRequest(BaseModel):
    amount_yuan: float = Field(0.01, gt=0, le=99999)
    subject: str = Field('支付运维探针', max_length=128)
    run_precreate: bool = True

class WechatProbeRequest(BaseModel):
    amount_yuan: float = Field(0.01, gt=0, le=99999)
    subject: str = Field('支付运维探针', max_length=128)
    run_precreate: bool = True

class CreateEgressAddonRequest(BaseModel):
    tenant_id: str
    slots: int = 1
    channel: str = 'wechat'

class CreateTokenPackRequest(BaseModel):
    tenant_id: str
    provider_id: str = Field(..., min_length=2, max_length=32, description='大模型平台 ID')
    channel: str = 'wechat'
    pack_id: Optional[str] = Field(None, pattern='^pack_')
    amount_yuan: Optional[float] = Field(None, gt=0, description='自定义充值金额（元），与 pack_id 二选一')
    @model_validator(mode='after')
    def pack_or_custom_amount(self):
        """执行 pack_or_custom_amount 相关逻辑处理。
        
        :param self: 参数 self
        :return: 返回处理结果。
        :raises: ValueError 等异常在错误时抛出。
        """
        if self.pack_id and self.amount_yuan is not None:
            raise ValueError('pack_id 与 amount_yuan 只能二选一')
        if not self.pack_id and self.amount_yuan is None:
            raise ValueError('请指定固定流量包 pack_id 或自定义金额 amount_yuan')
        return self

def _mock_pay_allowed() -> bool:
    """mock-pay 默认关闭；仅显式 PAYMENT_ALLOW_MOCK=1 时允许（且响应须 stamp mock）。"""
    return os.getenv('PAYMENT_ALLOW_MOCK', '0').lower() in ('1', 'true', 'yes')


def _notify_strict_enabled() -> bool:
    """回调验签开关（委托单一权威判定 is_payment_strict，禁止各模块自行重算）。"""
    from app.services.payment_pkg.verify_flags import is_payment_strict
    return is_payment_strict()


@router.get('/channels/status', operation_id='payment_get_channels_status', response_model=APIResponse, summary='获取支付渠道配置与在线状态', description='查询微信支付与支付宝渠道配置就绪状态、真实商户连接状态及Mock模式状态。需要有效JWT管理员权限。')
def payment_channels_status(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """处理 GET /channels/status 请求，payment相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in PAYMENT_OPS_ADMIN_ROLES:
        return error_response(403, '权限不足')
    from app.services.alipay_client import load_alipay_config, AlipayClient
    from app.services.wechat_pay_v3 import load_wechat_pay_v3_config, payment_mock_allowed
    svc = PaymentService(db)
    wx_cfg = load_wechat_pay_v3_config(appid=svc.wechat.appid, mchid=svc.wechat.mchid, api_v3_key=svc.wechat.api_v3_key, serial_no=svc.wechat.serial_no, notify_url=svc.wechat.notify_url)
    ali = AlipayClient(load_alipay_config())
    return success_response(data={'wechat': {'configured': wx_cfg.is_live or svc.wechat.is_configured, 'v3_live': wx_cfg.is_live, 'mock_allowed': payment_mock_allowed()}, 'alipay': {'configured': ali.is_live, 'mock_allowed': payment_mock_allowed()}})

@router.get('/ops/status', operation_id='payment_get_ops_status', response_model=APIResponse, summary='支付运维快照', description='支付运维快照：渠道配置状态 + 微信平台证书缓存。需要 admin/super_admin 角色。')
def payment_ops_status(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """支付运维快照：渠道配置 + 微信平台证书缓存（admin/super_admin）。"""
    if current_user.role not in PAYMENT_OPS_ADMIN_ROLES:
        return error_response(403, '权限不足')
    from app.services.payment_ops_service import get_payment_ops_status
    return success_response(data=get_payment_ops_status(db))

@router.post('/ops/wechat/refresh-certs', operation_id='payment_post_ops_wechat_refresh_certs', response_model=APIResponse, summary='刷新微信平台证书', description='强制刷新微信平台证书缓存（super_admin，需有效 JWT）。', dependencies=[])
def payment_ops_refresh_wechat_certs(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """强制刷新微信平台证书缓存（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_REFRESH_CERTS, log_payment_ops_action
    from app.services.payment_ops_service import refresh_wechat_platform_certs
    result = refresh_wechat_platform_certs()
    log_payment_ops_action(db, action=OPS_ACTION_REFRESH_CERTS, result=result, actor_user_id=str(current_user.id), ok=bool(result.get('refreshed')))
    return success_response(data=result)

@router.post('/ops/alipay/probe', operation_id='payment_post_ops_alipay_probe', response_model=APIResponse, summary='支付宝连通性探针', description='支付宝沙箱/生产连通性探针（super_admin，不落库）。')
def payment_ops_alipay_probe(req: AlipayProbeRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """支付宝沙箱/生产连通性探针（super_admin，不落库）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_ALIPAY_PROBE, log_payment_ops_action
    from app.services.payment_ops_service import probe_alipay_sandbox
    result = probe_alipay_sandbox(amount_yuan=req.amount_yuan, subject=req.subject, run_precreate=req.run_precreate)
    log_payment_ops_action(db, action=OPS_ACTION_ALIPAY_PROBE, result=result, actor_user_id=str(current_user.id))
    return success_response(data=result)

@router.post('/ops/wechat/probe', operation_id='payment_post_ops_wechat_probe', response_model=APIResponse, summary='微信连通性探针', description='微信 Native 支付连通性探针（super_admin，不落库）。')
def payment_ops_wechat_probe(req: WechatProbeRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """微信 Native 连通性探针（super_admin，不落库）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_WECHAT_PROBE, log_payment_ops_action
    from app.services.payment_ops_service import probe_wechat_native
    result = probe_wechat_native(amount_yuan=req.amount_yuan, subject=req.subject, run_precreate=req.run_precreate)
    log_payment_ops_action(db, action=OPS_ACTION_WECHAT_PROBE, result=result, actor_user_id=str(current_user.id))
    return success_response(data=result)

@router.post('/ops/staging/self-check', operation_id='payment_post_ops_staging_self_check', response_model=APIResponse, summary='Staging 支付自检', description='Staging 支付自检：证书 + 进程内 notify 闭环验证（super_admin）。')
def payment_ops_staging_self_check(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """Staging 支付自检：证书 + 进程内 notify 闭环（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_STAGING_SELF_CHECK, log_payment_ops_action
    from app.services.payment_ops_service import run_staging_payment_self_check
    result = run_staging_payment_self_check(db)
    log_payment_ops_action(db, action=OPS_ACTION_STAGING_SELF_CHECK, result=result, actor_user_id=str(current_user.id))
    return success_response(data=result)

@router.get('/ops/staging/public-reachability', operation_id='payment_get_ops_staging_public_reachability', response_model=APIResponse, summary='公网可达性探测', description='探测 ngrok 公网 /health 与支付回调 notify URL 的可达性（super_admin）。', dependencies=[])
def payment_ops_public_reachability(public_url: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """探测 ngrok 公网 /health 与 notify URL（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_PUBLIC_REACHABILITY, log_payment_ops_action
    from app.services.payment_ops_service import run_public_reachability_check
    result = run_public_reachability_check(public_url or '')
    log_payment_ops_action(db, action=OPS_ACTION_PUBLIC_REACHABILITY, result=result, actor_user_id=str(current_user.id))
    return success_response(data=result)

@router.post('/ops/staging/public-notify-check', operation_id='payment_post_ops_staging_public_notify_check', response_model=APIResponse, summary='公网回调端到端检查', description='经 ngrok 公网 URL 端到端 POST 支付回调 notify，验证回调链路（super_admin）。', dependencies=[])
def payment_ops_public_notify_check(public_url: Optional[str]=Query(None), discover_ngrok: bool=Query(False), try_signed: bool=Query(False, description='严验签时尝试签名正向验收'), db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """经 ngrok 公网 URL 端到端 POST notify（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import OPS_ACTION_PUBLIC_NOTIFY, log_payment_ops_action
    from app.services.payment_ops_service import run_public_notify_e2e_check
    result = run_public_notify_e2e_check(db, public_url=public_url or '', discover_ngrok=discover_ngrok, try_signed=try_signed)
    log_payment_ops_action(db, action=OPS_ACTION_PUBLIC_NOTIFY, result=result, actor_user_id=str(current_user.id))
    return success_response(data=result)

@router.get('/ops/audit', operation_id='payment_get_ops_audit', response_model=APIResponse, summary='运维操作历史', description='支付运维操作审计历史，支持分页与 action/时间过滤（super_admin）。')
def payment_ops_audit_list(page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100), action: Optional[str]=Query(None), start_at: Optional[str]=Query(None, description='起始时间 ISO 或 YYYY-MM-DD'), end_at: Optional[str]=Query(None, description='结束时间 ISO 或 YYYY-MM-DD'), db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """支付运维操作历史（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.inquiry_assignment_audit_service import parse_audit_datetime
    from app.services.payment_ops_audit_service import list_payment_ops_audit_page
    try:
        start_dt = parse_audit_datetime(start_at, end_of_day=False)
        end_dt = parse_audit_datetime(end_at, end_of_day=True)
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=list_payment_ops_audit_page(db, action=action, start_at=start_dt, end_at=end_dt, page=page, page_size=page_size))

@router.get('/ops/audit/actions', operation_id='payment_get_ops_audit_actions', response_model=APIResponse, summary='运维审计操作类型', description='返回运维审计可筛选的操作类型列表（super_admin）。')
def payment_ops_audit_actions(current_user: User=Depends(get_current_user)):
    """运维审计可筛选的操作类型（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import list_ops_audit_action_types
    return success_response(data=list_ops_audit_action_types())

@router.get('/ops/audit/export', operation_id='payment_get_ops_audit_export', response_model=APIResponse, summary='导出运维审计 CSV', description='导出支付运维审计 CSV，支持 action/时间范围过滤（super_admin）。', dependencies=[])
def payment_ops_audit_export(action: Optional[str]=Query(None), start_at: Optional[str]=Query(None), end_at: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """导出支付运维审计 CSV（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from fastapi.responses import StreamingResponse
    from app.services.inquiry_assignment_audit_service import parse_audit_datetime
    from app.services.payment_ops_audit_service import build_payment_ops_audit_csv, query_payment_ops_audit_rows
    try:
        start_dt = parse_audit_datetime(start_at, end_of_day=False)
        end_dt = parse_audit_datetime(end_at, end_of_day=True)
    except ValueError as exc:
        return error_response(400, str(exc))
    rows = query_payment_ops_audit_rows(db, action=action, start_at=start_dt, end_at=end_dt)
    csv_text = build_payment_ops_audit_csv(rows)
    return StreamingResponse(iter([csv_text]), media_type='text/csv; charset=utf-8-sig', headers={'Content-Disposition': 'attachment; filename="payment_ops_audit.csv"'})

@router.get('/ops/audit/{audit_id}', operation_id='payment_get_ops_audit_audit_id', response_model=APIResponse, summary='运维审计详情', description='查询单条支付运维审计记录详情（super_admin）。')
def payment_ops_audit_detail(audit_id: str, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """单条运维审计详情（super_admin）。"""
    denied = _payment_ops_allowed(current_user)
    if denied:
        return denied
    from app.services.payment_ops_audit_service import get_payment_ops_audit
    row = get_payment_ops_audit(db, audit_id)
    if not row:
        return error_response(404, '审计记录不存在')
    return success_response(data=row)

@router.get('/plans', operation_id='payment_get_plans', summary='套餐列表', description='查询所有可用套餐及价格（需有效 JWT）。')
def list_plans(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """查询所有可用套餐及价格"""
    if (err := _payment_allowed(current_user)):
        return err
    plans = db.query(TenantPlan).filter(TenantPlan.is_active.is_(True)).order_by(TenantPlan.price_monthly).all()
    return success_response(data=[{'id': p.id, 'name': p.name, 'code': p.code, 'price_monthly': p.price_monthly, 'price_yearly': p.price_yearly, 'max_users': p.max_users, 'max_sites': p.max_sites, 'max_products': p.max_products, 'max_ai_quota': p.max_ai_quota, 'features': p.features} for p in plans], message='查询成功')

@router.post('/create', operation_id='payment_post_create', summary='创建支付订单', description='创建支付订单（需有效 JWT）。')
def create_payment(req: CreatePaymentRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """创建支付订单"""
    if (err := _payment_allowed(current_user)):
        return err
    if req.channel not in ('wechat', 'alipay', 'stripe'):
        return error_response(400, f'不支持的支付渠道: {req.channel}')
    service = PaymentService(db)
    order = service.create_payment_order(tenant_id=req.tenant_id, subscription_id=req.subscription_id, amount=req.amount, channel=req.channel, subject=req.subject, currency=req.currency)
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'amount': order.amount, 'channel': order.channel, 'status': order.status, 'created_at': order.created_at.isoformat()}, message='支付订单创建成功')

@router.post('/create-native', operation_id='payment_post_create_native', response_model=APIResponse, summary='创建扫码支付订单', description='创建 Native 扫码支付订单，返回二维码 URL（微信 / 支付宝，需有效 JWT）。')
def create_native_payment(req: CreateNativePaymentRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """创建 Native 扫码支付订单，返回二维码 URL（微信 / 支付宝）"""
    if (err := _payment_allowed(current_user)):
        return err
    if req.billing_cycle not in ('monthly', 'yearly'):
        return error_response(400, 'billing_cycle 必须为 monthly 或 yearly')
    service = PaymentService(db)
    try:
        result = service.create_native_payment(tenant_id=req.tenant_id, plan_id=req.plan_id, billing_cycle=req.billing_cycle, current_user_id=current_user.id, channel=req.channel)
    except ValueError as e:
        return error_response(400, str(e))
    order = result['order']
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'amount': order.amount, 'subject': order.subject, 'status': order.status, 'channel': order.channel, 'code_url': result['code_url'], 'mock': result.get('mock', False), 'created_at': order.created_at.isoformat()}, message='支付订单创建成功')

@router.post('/notify', operation_id='payment_post_notify', response_model=APIResponse, summary='支付回调 Webhook', description='支付回调 webhook。不校验身份，由支付网关直接回调；按幂等键去重后入账。')
def payment_notify(req: NotifyRequest, db: Session=Depends(get_db)):
    """支付回调 webhook（不校验身份，由支付网关直接回调）"""
    log.warning(
        "[Payment] 遗留通用 /notify 端点被调用，建议迁移至 /notify/wechat 与 /notify/alipay。"
        "该端点仅在配置 PAYMENT_WEBHOOK_SECRET 且严验签通过时放行；严验模式下无可信签名直接拒绝（B-P0 F4）。"
    )
    service = PaymentService(db)
    strict = _notify_strict_enabled()
    if strict and (not service.verify_notify(req.data, req.signature, channel=req.channel)):
        return error_response(403, '支付回调验签失败')
    if req.channel == 'wechat':
        order = service.process_wechat_notify(req.data)
    elif req.channel == 'alipay':
        order = service.process_alipay_notify(req.data)
    else:
        return error_response(400, f'不支持的支付渠道: {req.channel}')
    if not order:
        return error_response(404, '订单不存在或已处理')
    _emit_payment_success_event(order)
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'status': order.status}, message='回调处理成功')

@router.post('/notify/alipay', operation_id='payment_post_notify_alipay', response_model=APIResponse, summary='支付宝异步通知', description='支付宝异步通知（application/x-www-form-urlencoded，响应纯文本 success/failure）。')
async def alipay_payment_notify(request: Request, db: Session=Depends(get_db)):
    """支付宝异步通知（application/x-www-form-urlencoded，响应纯文本 success/failure）。"""
    form = await request.form()
    data = {k: form.get(k) for k in form.keys()}
    service = PaymentService(db)
    strict = _notify_strict_enabled()
    sign = str(data.get('sign') or '')
    if strict and (not service.alipay.verify_notify(data, sign)):
        return PlainTextResponse('failure')
    order = service.process_alipay_notify(data)
    if not order:
        return PlainTextResponse('failure')
    _emit_payment_success_event(order)
    return PlainTextResponse('success')

@router.post('/notify/wechat', operation_id='payment_post_notify_wechat', response_model=APIResponse, summary='微信支付异步通知', description='微信支付 v3 异步通知（原始 JSON body，响应 {"code":"SUCCESS"}）。')
async def wechat_payment_notify(request: Request, db: Session=Depends(get_db)):
    """微信支付 v3 异步通知（原始 JSON body，响应 {"code":"SUCCESS"}）。"""
    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8') if body_bytes else '{}'
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={'code': 'FAIL', 'message': 'invalid json'})
    headers = {k.lower(): v for k, v in request.headers.items()}
    service = PaymentService(db)
    strict = _notify_strict_enabled()
    if strict and (not service.wechat.verify_v3_notify(body_text, headers)):
        return JSONResponse(status_code=403, content={'code': 'FAIL', 'message': 'signature verification failed'})
    order = service.process_wechat_notify(data)
    if not order:
        return JSONResponse(content={'code': 'FAIL', 'message': 'order not found'})
    _emit_payment_success_event(order)
    return JSONResponse(content={'code': 'SUCCESS', 'message': '成功'})

@router.post('/addon/egress-ip', operation_id='payment_post_addon_egress_ip', response_model=APIResponse, summary='购买出口 IP 加购', description='购买额外出口 IP 槽位：支付成功后增加 egress_ip_quota 并尝试分配。')
def create_egress_ip_addon(req: CreateEgressAddonRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """购买额外 IP 槽位（支付成功后增加 egress_ip_quota 并尝试分配）。"""
    if current_user.role not in ['admin', 'super_admin', 'tenant_admin']:
        return error_response(403, '权限不足')
    if req.slots < 1 or req.slots > 20:
        return error_response(400, 'slots 须在 1～20 之间')
    if req.channel not in ('wechat', 'alipay'):
        return error_response(400, '加购仅支持 wechat / alipay')
    service = PaymentService(db)
    try:
        result = service.create_egress_addon_native(tenant_id=req.tenant_id, slots=req.slots, channel=req.channel)
    except ValueError as e:
        return error_response(400, str(e))
    order = result['order']
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'amount': order.amount, 'subject': order.subject, 'status': order.status, 'channel': order.channel, 'code_url': result.get('code_url'), 'mock': result.get('mock', False), 'slots': req.slots}, message='IP 槽位加购订单已创建，请扫码支付')

@router.get('/addon/token-packs', operation_id='payment_get_addon_token_packs', response_model=APIResponse, summary='AI 流量包目录', description='AI 流量加购：可选大模型平台 + 流量包目录（需有效 JWT）。')
def list_token_packs(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """AI 流量加购：可选大模型平台 + 流量包目录。"""
    if (err := _payment_allowed(current_user)):
        return err
    from app.services.ai_traffic_provider_service import get_tenant_ai_traffic_provider, list_providers_for_client
    from app.services.order_addon_service import TOKEN_PACK_CATALOG, custom_recharge_config_for_client
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    packs = [{'pack_id': pid, 'tokens': spec['tokens'], 'price_cents': spec['price_cents'], 'label': spec['label'], 'price_yuan': round(spec['price_cents'] / 100, 2)} for pid, spec in TOKEN_PACK_CATALOG.items()]
    current_provider_id = None
    tid = resolve_tenant_id_for_user(db, current_user)
    if tid:
        tenant = db.query(Tenant).filter(Tenant.id == tid).first()
        if tenant:
            current_provider_id = get_tenant_ai_traffic_provider(tenant)
    return success_response(data={'providers': list_providers_for_client(), 'packs': packs, 'current_provider_id': current_provider_id, 'custom_recharge': custom_recharge_config_for_client()})

@router.get('/addon/token-pack/quote', operation_id='payment_get_addon_token_pack_quote', response_model=APIResponse, summary='自定义充值预估', description='按自定义充值金额预估到账流量，折算规则与下单一致（需有效 JWT）。')
def quote_token_pack_custom(amount_yuan: float=Query(..., gt=0, description='自定义充值金额（元）'), db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """预估自定义充值到账流量（与下单折算规则一致）。"""
    if (err := _payment_allowed(current_user)):
        return err
    from app.services.order_addon_service import quote_custom_token_recharge
    try:
        quote = quote_custom_token_recharge(amount_yuan)
    except ValueError as e:
        return error_response(400, str(e))
    return success_response(data=quote)

@router.post('/addon/token-pack', operation_id='payment_post_addon_token_pack', response_model=APIResponse, summary='购买流量包', description='创建 AI 流量包支付订单（需有效 JWT）。')
def create_token_pack_payment(req: CreateTokenPackRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """购买 Token 包（支付成功后自动充值）。"""
    if (err := _payment_allowed(current_user)):
        return err
    service = PaymentService(db)
    try:
        result = service.create_token_pack_native(tenant_id=req.tenant_id, channel=req.channel, provider_id=req.provider_id, pack_id=req.pack_id, amount_yuan=req.amount_yuan)
    except ValueError as e:
        return error_response(400, str(e))
    order = result['order']
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'amount': order.amount, 'subject': order.subject, 'status': order.status, 'code_url': result.get('code_url'), 'mock': result.get('mock', False), 'pack_id': req.pack_id, 'amount_yuan': req.amount_yuan, 'provider_id': req.provider_id, 'tokens': result.get('tokens')}, message='AI 流量充值订单已创建，请完成支付')

@router.post('/mock-pay', operation_id='payment_post_mock_pay', response_model=APIResponse, summary='模拟支付', description='开发环境模拟支付回调，走与真实回调一致的入账链路（需有效 JWT）。')
def mock_pay(req: MockPayRequest, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """Dev-only mock pay. Forbidden unless PAYMENT_ALLOW_MOCK=1; never treat as real settlement."""
    if not _mock_pay_allowed():
        return error_response(403, 'mock-pay 已禁用：禁止假支付到账，请使用真实支付回调')
    if (err := _payment_allowed(current_user)):
        return err
    service = PaymentService(db)
    order = service.mock_pay_order(req.order_id)
    if not order:
        return error_response(404, '订单不存在或无法支付')
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'status': order.status, 'paid_at': order.paid_at.isoformat() if order.paid_at else None}, message='模拟支付成功')

@router.get('/orders', operation_id='payment_get_orders', summary='支付订单列表', description='查询当前用户支付订单列表，支持分页（需有效 JWT）。')
def list_payment_orders(tenant_id: str=None, status: str=None, page: int=1, page_size: int=20, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """支付订单列表"""
    if current_user.role not in ['admin', 'super_admin', 'tenant_admin']:
        return error_response(403, '权限不足')
    service = PaymentService(db)
    items, total = service.list_orders(tenant_id=tenant_id, status=status, page=page, page_size=page_size)
    tenant_names: dict[str, str] = {}
    if items:
        tids = list({str(o.tenant_id) for o in items})
        rows = db.query(Tenant.id, Tenant.name).filter(Tenant.id.in_(tids)).all()
        tenant_names = {str(r[0]): r[1] or str(r[0])[:8] for r in rows}
    return success_response(data=[{'id': o.id, 'order_no': o.order_no, 'tenant_id': o.tenant_id, 'tenant_name': tenant_names.get(str(o.tenant_id), str(o.tenant_id)[:8]), 'amount': o.amount, 'channel': o.channel, 'subject': o.subject, 'status': o.status, 'paid_at': o.paid_at.isoformat() if o.paid_at else None, 'created_at': o.created_at.isoformat()} for o in items], message='查询成功', total=total, page=page, page_size=page_size)

class OrderQueryParams(BaseModel):
    order_id: str = None
    order_no: str = None

@router.get('/orders/{order_id}', operation_id='payment_get_orders_order_id', response_model=APIResponse, summary='支付订单详情', description='查询单个支付订单详情（需有效 JWT）。')
def get_payment_order(order_id: str, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    """查询单笔支付订单"""
    if current_user.role not in ['admin', 'super_admin', 'tenant_admin']:
        return error_response(403, '权限不足')
    service = PaymentService(db)
    order = service.get_order(order_id)
    if not order:
        return error_response(404, '订单不存在')
    return success_response(data={'id': order.id, 'order_no': order.order_no, 'amount': order.amount, 'channel': order.channel, 'subject': order.subject, 'status': order.status, 'paid_at': order.paid_at.isoformat() if order.paid_at else None, 'created_at': order.created_at.isoformat()}, message='查询成功')

@router.post('/stripe/create-session', summary='创建 Stripe 支付会话', operation_id='create_stripe_session', response_model=APIResponse, description='创建 Stripe Checkout Session，进入订阅/一次性支付流程（需有效 JWT）。')
def create_stripe_session(plan_id: int=Body(...), billing_cycle: str=Body('monthly'), current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    """创建 Stripe 支付会话。

    BUG-06 配套修复：先落 PaymentOrder（pending）并把 order_no 写入 session metadata，
    保证 webhook checkout.session.completed 能找到订单并完成发放闭环。
    """
    try:
        from app.services.stripe_service import create_checkout_session
        plan = db.query(TenantPlan).filter(TenantPlan.id == plan_id).first()
        if not plan:
            return error_response(404, '套餐不存在')
        price = plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly
        # 先建支付订单，供 webhook 回来时对账发放
        from app.services.payment_pkg.payment_service_impl import PaymentService
        svc = PaymentService(db)
        created = svc.create_payment_order(
            tenant_id=str(current_user.tenant_id),
            subscription_id=None,
            amount=price,
            channel='stripe',
            subject=f'Stripe订阅:{plan.name}({billing_cycle})',
        )
        order = created['order'] if isinstance(created, dict) else created
        result = create_checkout_session(
            line_items=[{'price_data': {'currency': 'usd', 'product_data': {'name': plan.name}, 'unit_amount': price}, 'quantity': 1}],
            mode='payment',
            success_url=f'{settings.SITE_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{settings.SITE_URL}/payment/cancel',
            tenant_id=str(current_user.tenant_id),
            metadata={'order_no': str(order.order_no)},
        )
        return success_response(data={**(result if isinstance(result, dict) else {}), 'order_no': str(order.order_no)}, message='Stripe Session 创建成功')
    except Exception as e:
        log.error('[Payment] Stripe Session 创建失败: %s', e)
        return error_response(500, f'Stripe Session 创建失败: {e}')

@router.post('/stripe/webhook', summary='Stripe Webhook 回调', operation_id='stripe_webhook', response_model=APIResponse, description='处理 Stripe Webhook 事件：验签 + event_id 幂等去重 + 入账发放（公开接口，由 Stripe 直接回调）。')
async def stripe_webhook(request: Request, db: Session=Depends(get_db)):
    """处理 Stripe Webhook 事件。

    BUG-06 修复：原实现验签后只打一行日志就返回「处理成功」，
    导致 Stripe 停止重试、钱到账但订单永远 pending、权益不发放。
    现在对 checkout.session.completed 走与微信/支付宝一致的
    _mark_paid_and_provision 发放链路，并按 event_id 做事件去重。
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature', '')
        from app.services.stripe_service import verify_webhook_signature, parse_webhook_event
        if not verify_webhook_signature(payload=payload, sig_header=sig_header):
            return error_response(403, 'Webhook 签名验证失败')
        event = parse_webhook_event(payload=payload)
        event_type = event.get('event_type') or event.get('raw_type') or ''
        event_id = str(event.get('event_id') or '')
        # 事件级幂等去重：同一 event 重复投递直接确认
        from app.core.cache import redis_client
        dedup_key = f'stripe:webhook:processed:{event_id}'
        if event_id and redis_client:
            try:
                if redis_client.get(dedup_key):
                    return success_response(data={'deduplicated': True, 'event_id': event_id}, message='事件已处理')
                redis_client.setex(dedup_key, 86400 * 7, '1')
            except Exception:
                log.warning('[Payment] Stripe 事件去重缓存读写失败，继续处理 event=%s', event_id)

        if event_type != 'checkout.session.completed':
            # 非支付完成事件（如 checkout.session.expired）确认收到即可
            return success_response(data={'ignored': True, 'event_type': event_type}, message='Webhook 处理成功')

        session = event.get('data') or {}
        if not isinstance(session, dict):
            return error_response(400, '事件数据格式异常')
        metadata = session.get('metadata') or {}
        order_no = (metadata.get('order_no') if isinstance(metadata, dict) else None) or ''
        if not order_no:
            log.error('[Payment] Stripe Webhook 缺少 metadata.order_no，无法对账 event=%s', event_id)
            return error_response(400, 'missing metadata.order_no')

        from app.services.payment_pkg.payment_service_impl import PaymentService
        svc = PaymentService(db)
        order = svc._mark_paid_and_provision(order_no, sync_data={
            'business_order_id': None,
            'out_trade_no': order_no,
            'mode': 'stripe',
        })
        if not order:
            return error_response(404, '订单不存在或已处理')
        _emit_payment_success_event(order)
        return success_response(data={'order_no': order.order_no, 'status': order.status, 'event_id': event_id}, message='Webhook 处理成功')
    except Exception as e:
        log.exception('[Payment] Stripe Webhook 处理失败: %s', e)
        return error_response(500, f'Webhook 处理失败: {e}')

@router.post('/refund', summary='发起退款', operation_id='create_payment_refund', response_model=APIResponse, description='对指定订单发起退款申请（需有效 JWT）。')
def create_refund(order_no: str=Body(...), refund_amount: float=Body(...), reason: str=Body(''), current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    """发起退款申请"""
    try:
        from app.services.refund_service import RefundService
        svc = RefundService(db)
        result = svc.refund_by_order_no(order_no=order_no, amount=refund_amount, reason=reason)
        return success_response(data=result, message='退款申请已提交')
    except Exception as e:
        log.error('[Payment] 退款失败: %s', e)
        return error_response(500, f'退款失败: {e}')

@router.get('/refund/status/{order_no}', summary='查询退款状态', operation_id='get_payment_refund_status', response_model=APIResponse, description='按订单号查询退款处理状态（需有效 JWT）。')
def get_refund_status(order_no: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    """查询退款状态"""
    try:
        from app.services.refund_service import RefundService
        svc = RefundService(db)
        result = svc.get_refund_status(order_no)
        return success_response(data=result)
    except Exception as e:
        return error_response(500, f'查询失败: {e}')

@router.post('/balance/pay', summary='余额支付', operation_id='balance_pay_order', response_model=APIResponse, description='使用账户余额支付订单（需有效 JWT）。')
def balance_payment(order_no: str=Body(...), current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    """使用余额支付订单。

    BUG-03 修复：
    1. 金额改为服务端取订单金额，不再信任客户端 amount（原来传 1 即"支付成功"）；
    2. 增加租户越权校验（原来任意用户可支付任意租户订单）；
    3. 扣款成功后走与渠道回调一致的 _mark_paid_and_provision 链路
       （置 paid + 记财务台账 + 发放权益），发放失败自动回滚 pending 并补偿退回余额。
    """
    try:
        order = db.query(PaymentOrder).filter(PaymentOrder.order_no == order_no).first()
        if not order:
            return error_response(404, '订单不存在')
        if order.status != 'pending':
            return error_response(400, f'订单当前状态 {order.status}，无需支付')
        # 越权校验：订单必须属于当前用户租户（平台管理员豁免）
        user_tenant = str(getattr(current_user, 'tenant_id', '') or '')
        if str(order.tenant_id) != user_tenant and current_user.role not in ('admin', 'super_admin'):
            return error_response(403, '无权支付该订单')
        # 服务端定价：金额一律取订单金额（分），拒绝客户端传参
        amount = int(order.amount)
        from app.services.payment_balance_service import pay_order_with_balance
        result = pay_order_with_balance(user_id=str(current_user.id), order_id=str(order.id), amount=amount, currency=getattr(order, 'currency', 'CNY'), tenant_id=str(order.tenant_id))
        if not result or not getattr(result, 'success', False):
            return error_response(400, (getattr(result, 'error', None) if result else None) or '余额支付失败')
        # 复用回调一致的发放链路：原子置 paid + 收入 + 权益
        try:
            from app.services.payment_pkg.payment_service_impl import PaymentService
            svc = PaymentService(db)
            paid = svc._mark_paid_and_provision(order.order_no)
            if not paid:
                # 并发下已被其它请求支付：补偿退回刚扣的余额
                _refund_balance_after_failed_pay(current_user, amount, order)
                return error_response(409, '订单已被支付，余额已退回')
        except Exception:
            log.exception('[Payment] 余额支付后发放权益失败，补偿退回余额: order=%s', order_no)
            _refund_balance_after_failed_pay(current_user, amount, order)
            return error_response(500, '权益发放失败，余额已退回，请稍后重试')
        return success_response(data=result.to_dict(), message='余额支付成功')
    except Exception as e:
        log.error('[Payment] 余额支付失败: %s', e)
        return error_response(500, f'余额支付失败: {e}')


def _refund_balance_after_failed_pay(user: User, amount: int, order) -> None:
    """BUG-03 配套：权益发放失败时把已扣余额退回钱包（补偿事务）。"""
    try:
        from app.services import user_wallet_service
        user_wallet_service.deposit(
            user_id=str(user.id),
            amount=amount,
            currency=getattr(order, 'currency', 'CNY') or 'CNY',
            ref_type='balance_pay_compensate',
            ref_id=str(order.order_no),
        )
    except Exception:
        log.exception('[Payment] 余额补偿退回失败，需人工介入: user=%s order=%s amount=%s', user.id, order.order_no, amount)