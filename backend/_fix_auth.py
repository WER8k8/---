path = 'app/api/v1/routes/auth.py'
lines = open(path, encoding='utf-8').read().split('\n')
# replace 1-indexed lines 435..546 inclusive (whole third_party_login func)
start, end = 435, 546
new_block = '''@router.post("/third-party-login",
             response_model=APIResponse[ThirdPartyLoginResponse])
def third_party_login(
    request: ThirdPartyLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """第三方登录（QQ / 微信 / 飞书 / 钉钉）。

    流程：
    1. 校验 provider 合法性
    2. 用 code 从平台换取 provider_id + 用户昵称
    3. 查找绑定记录 → 签发 JWT
    4. 开发模式：自动绑定 admin 账号
    5. 生产模式：未绑定则拒绝，引导用户先登录后绑定
    """
    provider = request.provider.lower()
    ip = client_ip_from_request(http_request)

    # ── 限流：第三方登录 5次/分钟/IP（防暴力尝试）──
    blocked = check_login_allowed(ip, f"oauth:{provider}")
    if blocked:
        return error_response(blocked[0], blocked[1])

    if provider not in SUPPORTED_OAUTH_PROVIDERS:
        return error_response(400, "不支持的第三方登录方式")

    # ── code → 身份解析 ──
    try:
        provider_id, nickname_hint = resolve_oauth_identity(provider, request.code)
    except ValueError as e:
        record_login_failure(ip, f"oauth:{provider}")
        key = str(e)
        if key == "oauth_not_configured":
            return error_response(503, "该登录方式尚未配置 OAuth 应用")
        if key == "missing_code":
            return error_response(400, "缺少授权码")
        # 包含平台错误描述的透传
        if ": " in key:
            _, detail = key.split(": ", 1)
            return error_response(401, f"第三方授权失败: {detail}")
        return error_response(401, "第三方授权失败，请重试")

    now = datetime.now(timezone.utc)

    existing = _handle_existing_binding(db, provider, provider_id, ip, now)
    if existing is not None:
        return existing

    dev_resp = _handle_dev_auto_bind(db, provider, provider_id, now, ip)
    if dev_resp is not None:
        return dev_resp

    # 未绑定：拒绝登录
    record_login_failure(ip, f"oauth:{provider}")
    logger.warning(
        "[OAuth Login] 未绑定 %s 账号 %s... 拒绝登录",
        provider, provider_id[:12],
    )
    return error_response(
        403,
        "该第三方账号尚未绑定管理后台用户，请先用用户名密码登录后进入「个人设置→账号绑定」完成关联",
    )


def _handle_existing_binding(
    db: Session,
    provider: str,
    provider_id: str,
    ip: str,
    now,
) -> object:
    """查找已有绑定并直接签发令牌；无绑定返回 None，用户异常时返回错误响应。

    :param db: 数据库会话。
    :param provider: 第三方平台标识。
    :param provider_id: 平台返回的用户唯一标识。
    :param ip: 客户端 IP，用于登录成功记录。
    :param now: 当前 UTC 时间，用于更新绑定记录。
    :return: 命中绑定返回令牌响应；用户异常返回错误响应；未命中返回 None。
    """
    binding = (
        db.query(ThirdPartyLogin)
        .filter(
            ThirdPartyLogin.provider == provider,
            ThirdPartyLogin.provider_id == provider_id,
        )
        .first()
    )
    if not binding:
        return None
    user = db.query(User).filter(User.id == binding.user_id).first()
    if not user or not user.is_active:
        return error_response(401, "用户不存在或已被禁用")
    binding.updated_at = now
    db.commit()
    record_login_success(ip, f"oauth:{provider}")
    logger.info(
        "[OAuth Login] 用户 %s 通过 %s 登录 (provider_id=%s...)",
        user.username[:1] + "***", provider, provider_id[:12],
    )
    return _token_response_for_user(user, new_user=False)


def _handle_dev_auto_bind(
    db: Session,
    provider: str,
    provider_id: str,
    now,
    ip: str,
):
    """开发模式下将 dev_ 前缀身份自动绑定并登录 admin；未命中返回 None。

    :param db: 数据库会话。
    :param provider: 第三方平台标识。
    :param provider_id: 平台返回的用户唯一标识。
    :param now: 当前 UTC 时间。
    :param ip: 客户端 IP，用于登录成功记录。
    :return: 命中开发模式自动绑定时返回令牌响应；否则返回 None。
    """
    admin_link = db.query(User).filter(User.username == "admin").first()
    if (
        admin_link
        and admin_link.is_active
        and provider_id.startswith("dev_")
        and not settings.is_production
        and (
            settings.OAUTH_DEV_BYPASS
            or settings.ENVIRONMENT == "development"
        )
    ):
        db.add(
            ThirdPartyLogin(
                id=str(uuid.uuid4()),
                user_id=admin_link.id,
                provider=provider,
                provider_id=provider_id,
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()
        record_login_success(ip, f"oauth:{provider}")
        logger.info(
            "[OAuth Login] dev 模式自动绑定 admin ← %s",
            provider,
        )
        return _token_response_for_user(admin_link, new_user=False)
    return None'''

new_lines = lines[:start-1] + new_block.split('\n') + lines[end:]
open(path, 'w', encoding='utf-8').write('\n'.join(new_lines))
print("auth.py updated; new line count:", len(new_lines))
