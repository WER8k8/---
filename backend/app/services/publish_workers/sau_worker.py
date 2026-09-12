"""social-auto-upload CLI Worker — 抖音/快手/B站/小红书/视频号。"""

from __future__ import annotations

import asyncio
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.publish_workers.verify import extract_bvid_from_text, extract_post_url_from_text

PLATFORM_TO_SAU: dict[str, str] = {
    "抖音": "douyin",
    "快手": "kuaishou",
    "哔哩哔哩": "bilibili",
    "小红书": "xiaohongshu",
    "微信视频号": "tencent",
    "TikTok": "tiktok",
    "TikTok / 抖音国际版": "tiktok",
}

SAU_NOTE_PLATFORMS = frozenset({"抖音", "快手", "小红书"})
SAU_SUPPORTED = frozenset(PLATFORM_TO_SAU.keys())


def sau_cli_path() -> str:
    """实现 sauclipath 的功能。
    
    :return: 返回 str 结果
    """
    custom = (settings.SAU_CLI_PATH or "").strip()
    if custom:
        return custom
    for name in ("sau", "sau.exe"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def _sidecar_ready() -> bool:
    """实现 sidecarready 的功能。
    
    :return: 返回 bool 结果
    """
    try:
        from app.services.publish_workers.sau_sidecar import sau_sidecar_enabled, sau_sidecar_health
        if not sau_sidecar_enabled():
            return False
        health = sau_sidecar_health()
        return bool(health.get("ok"))
    except Exception:
        return False


def sau_enabled() -> bool:
    """实现 sauenabled 的功能。
    
    :return: 返回 bool 结果
    """
    if not settings.SAU_ENABLED:
        return False
    if _sidecar_ready():
        return True
    return bool(sau_cli_path())


def sau_account_name(*, tenant_id: str | None, platform_name: str) -> str:
    """实现 sau账户名称 的功能。
    
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param platform_name: 参数 platform_name（类型: str）
    :return: 返回 str 结果
    """
    prefix = (settings.SAU_ACCOUNT_PREFIX or "youding").strip() or "youding"
    tid = re.sub(r"[^\w-]", "_", (tenant_id or "default")[:32])
    plat = PLATFORM_TO_SAU.get(platform_name, platform_name)[:16]
    return f"{prefix}_{tid}_{plat}"


def sau_bind_hint(*, platform_name: str, tenant_id: str | None) -> dict[str, Any] | None:
    """实现 saubindhint 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    if platform_name not in SAU_SUPPORTED or not settings.SAU_ENABLED:
        return None
    sau_plat = PLATFORM_TO_SAU[platform_name]
    account = sau_account_name(tenant_id=tenant_id, platform_name=platform_name)
    via = "sidecar" if _sidecar_ready() else "local_cli"
    return {
        "account": account,
        "platform_cli": sau_plat,
        "login_command": f"sau {sau_plat} login --account {account}",
        "check_command": f"sau {sau_plat} check --account {account}",
        "cookie_home": (settings.SAU_HOME or "").strip() or None,
        "execution": via,
    }


def format_sau_schedule(scheduled_at: datetime | int | None) -> str | None:
    """实现 格式化sau调度 的功能。
    
    :param scheduled_at: 参数 scheduled_at（类型: datetime | int | None）
    :return: 返回 str | None 结果
    """
    if scheduled_at is None:
        return None
    if isinstance(scheduled_at, int):
        ts = scheduled_at / 1000 if scheduled_at > 1_000_000_000_000 else scheduled_at
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        dt = scheduled_at if scheduled_at.tzinfo else scheduled_at.replace(tzinfo=timezone.utc)
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


async def _run_sau(args: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
    """实现 执行sau 的功能。
    
    :param args: 参数 args（类型: list[str]）
    :param timeout: 参数 timeout（类型: int | None）
    :return: 返回 tuple[int, str, str] 结果
    :raises RuntimeError: 当操作失败时抛出 RuntimeError 异常
    """
    cli = sau_cli_path()
    if not cli:
        raise RuntimeError("未找到 sau CLI，请安装 social-auto-upload 或配置 SAU_SIDECAR_URL")
    cmd = [cli, *args]
    env = None
    home = (settings.SAU_HOME or "").strip()
    if home:
        import os
        env = os.environ.copy()
        env["SAU_HOME"] = home

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    tout = timeout or settings.PUBLISH_WORKER_TIMEOUT_SEC
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=tout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"sau 命令超时（>{tout}s）")
    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")
    return proc.returncode or 0, stdout, stderr


async def sau_check_account(*, platform_name: str, account: str) -> dict[str, Any]:
    """实现 sau检查账户 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param account: 参数 account（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    sau_plat = PLATFORM_TO_SAU.get(platform_name)
    if not sau_plat:
        return {"ok": False, "reason": f"{platform_name} 不在 SAU 支持列表"}
    if _sidecar_ready():
        from app.services.publish_workers.sau_sidecar import sau_check_via_sidecar
        return await sau_check_via_sidecar(platform_name=platform_name, account=account)
    code, out, err = await _run_sau([sau_plat, "check", "--account", account], timeout=60)
    merged = f"{out}\n{err}"
    ok = code == 0 and ("有效" in merged or "valid" in merged.lower() or "cookie" in merged.lower())
    return {"ok": ok, "exit_code": code, "output": merged[:500]}


async def sau_check_tenant_platforms(
    *,
    tenant_id: str | None,
    platform_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """实现 sau检查租户平台 的功能。
    
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param platform_names: 参数 platform_names（类型: list[str] | None）
    :return: 返回 list[dict[str, Any]] 结果
    """
    names = platform_names or sorted(SAU_SUPPORTED)
    rows: list[dict[str, Any]] = []
    for name in names:
        if name not in SAU_SUPPORTED:
            continue
        account = sau_account_name(tenant_id=tenant_id, platform_name=name)
        check = await sau_check_account(platform_name=name, account=account)
        rows.append(
            {
                "platform_name": name,
                "account": account,
                "cookie_ok": bool(check.get("ok")),
                "detail": check,
            }
        )
    return rows


def _finalize_sau_outcome(
    *,
    code: int,
    out: str,
    err: str,
    account: str,
    schedule_str: str | None,
) -> dict[str, Any]:
    """实现 finalizesauoutcome 的功能。
    
    :param code: 参数 code（类型: int）
    :param out: 参数 out（类型: str）
    :param err: 参数 err（类型: str）
    :param account: 参数 account（类型: str）
    :param schedule_str: 参数 schedule_str（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    merged = f"{out}\n{err}"
    post_url = extract_post_url_from_text(merged)
    bvid = extract_bvid_from_text(merged)
    if bvid and not post_url:
        post_url = f"https://www.bilibili.com/video/{bvid}"

    outcome: dict[str, Any] = {
        "via": "sau",
        "account": account,
        "exit_code": code,
        "raw_output": merged[:4000],
        "platform_post_url": post_url,
        "platform_post_id": bvid or "",
        "success": False,
    }
    if code != 0:
        outcome["error_message"] = (err or out or "sau 上传失败")[:500]
    elif schedule_str and not post_url and not bvid:
        outcome["pending"] = True
        outcome["publish_state"] = "scheduled"
        outcome["scheduled_at"] = schedule_str
        outcome["error_message"] = (
            f"已提交平台定时发布（{schedule_str}），待平台侧生成作品链接后再验真"
        )
    return outcome


async def publish_via_sau(
    *,
    platform_name: str,
    local_video: Path,
    title: str,
    desc: str,
    tags: list[str] | None,
    tenant_id: str | None,
    bilibili_tid: int | None = None,
    scheduled_at: datetime | int | None = None,
    cover_path: Path | None = None,
    video_url: str = "",
    cover_url: str = "",
) -> dict[str, Any]:
    """实现 发布viasau 的功能。
    
    :param platform_name: 参数 platform_name（类型: str）
    :param local_video: 参数 local_video（类型: Path）
    :param title: 参数 title（类型: str）
    :param desc: 参数 desc（类型: str）
    :param tags: 参数 tags（类型: list[str] | None）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param bilibili_tid: 参数 bilibili_tid（类型: int | None）
    :param scheduled_at: 参数 scheduled_at（类型: datetime | int | None）
    :param cover_path: 参数 cover_path（类型: Path | None）
    :param video_url: 参数 video_url（类型: str）
    :param cover_url: 参数 cover_url（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    sau_plat = PLATFORM_TO_SAU.get(platform_name)
    if not sau_plat:
        return {
            "success": False,
            "via": "sau",
            "error_message": f"{platform_name} 未映射 SAU 子命令",
        }

    account = sau_account_name(tenant_id=tenant_id, platform_name=platform_name)
    check = await sau_check_account(platform_name=platform_name, account=account)
    if not check.get("ok"):
        return {
            "success": False,
            "via": "sau",
            "error_message": (
                f"SAU 账号 {account} 未登录或 Cookie 失效；"
                f"请执行: sau {sau_plat} login --account {account}"
            ),
            "setup_hint": check.get("output"),
        }

    schedule_str = format_sau_schedule(scheduled_at)
    if _sidecar_ready():
        from app.services.publish_workers.sau_sidecar import publish_via_sau_sidecar
        return await publish_via_sau_sidecar(
            platform_name=platform_name,
            tenant_id=tenant_id,
            title=title,
            desc=desc,
            tags=tags,
            local_video=local_video,
            cover_path=cover_path,
            scheduled_at=scheduled_at,
            bilibili_tid=bilibili_tid,
            mode="video",
            video_url=video_url,
            cover_url=cover_url,
        )

    args = [
        sau_plat,
        "upload-video",
        "--account",
        account,
        "--file",
        str(local_video),
        "--title",
        title[:120] or "视频",
        "--desc",
        (desc or title)[:500],
    ]
    if tags:
        args.extend(["--tags", ",".join(tags[:10])])
    if schedule_str:
        args.extend(["--schedule", schedule_str])
    if cover_path and cover_path.exists():
        args.extend(["--thumbnail", str(cover_path)])
    if sau_plat == "bilibili":
        tid = bilibili_tid or settings.SAU_BILIBILI_TID
        args.extend(["--tid", str(tid)])

    code, out, err = await _run_sau(args)
    return _finalize_sau_outcome(
        code=code, out=out, err=err, account=account, schedule_str=schedule_str
    )


async def publish_via_sau_note(
    *,
    platform_name: str,
    local_images: list[Path],
    title: str,
    note: str,
    tags: list[str] | None,
    tenant_id: str | None,
    scheduled_at: datetime | int | None = None,
) -> dict[str, Any]:
    """图文 upload-note（抖音/快手/小红书）。"""
    if platform_name not in SAU_NOTE_PLATFORMS:
        return {
            "success": False,
            "via": "sau",
            "error_message": f"{platform_name} 不支持 SAU 图文模式",
        }
    sau_plat = PLATFORM_TO_SAU[platform_name]
    account = sau_account_name(tenant_id=tenant_id, platform_name=platform_name)
    check = await sau_check_account(platform_name=platform_name, account=account)
    if not check.get("ok"):
        return {
            "success": False,
            "via": "sau",
            "error_message": f"SAU 账号 {account} 未登录或 Cookie 失效",
            "setup_hint": check.get("output"),
        }
    if not local_images:
        return {"success": False, "via": "sau", "error_message": "图文发布至少 1 张图片"}

    schedule_str = format_sau_schedule(scheduled_at)
    if _sidecar_ready():
        from app.services.publish_workers.sau_sidecar import publish_via_sau_sidecar
        return await publish_via_sau_sidecar(
            platform_name=platform_name,
            tenant_id=tenant_id,
            title=title,
            desc=note,
            tags=tags,
            local_images=local_images,
            scheduled_at=scheduled_at,
            mode="note",
        )

    args = [sau_plat, "upload-note", "--account", account, "--title", title[:120] or "图文"]
    for img in local_images[:9]:
        args.extend(["--images", str(img)])
    args.extend(["--note", (note or title)[:2000]])
    if tags:
        args.extend(["--tags", ",".join(tags[:10])])
    if schedule_str:
        args.extend(["--schedule", schedule_str])

    code, out, err = await _run_sau(args)
    return _finalize_sau_outcome(
        code=code, out=out, err=err, account=account, schedule_str=schedule_str
    )
