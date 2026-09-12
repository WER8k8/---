"""智能代理工作流 API — 进程监控/管理 + MCP Bridge"""

import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User

router = APIRouter()

# 代理进程注册表
AGENT_REGISTRY = {
    "lingma_assist": {
        "name": "Lingma 助手",
        "exe": "Lingma-Assist.exe",
        "icon": "🤖",
        "description": "AI 编程助手代理",
        "port": None,
    },
    "local_dashboard": {
        "name": "本地仪表盘",
        "exe": "Local-Dashboard.exe",
        "icon": "📊",
        "description": "本地运行状态展示",
        "port": None,
    },
    "qq_bot": {
        "name": "QQ 机器人",
        "exe": "QQ-Bot.exe",
        "icon": "🐧",
        "description": "QQ 消息自动回复",
        "port": None,
    },
    "scheduler": {
        "name": "任务调度器",
        "exe": "Scheduler.exe",
        "icon": "⏰",
        "description": "定时任务调度引擎",
        "port": None,
    },
    "trae_core": {
        "name": "TRAE 核心",
        "exe": "TRAE-Core.exe",
        "icon": "🧠",
        "description": "Trae 推理引擎",
        "port": None,
    },
    "smart_agent": {
        "name": "智能代理工作流",
        "exe": "SmartAgent-Workflow.exe",
        "icon": "🔄",
        "description": "多代理协同编排",
        "port": None,
    },
}


def _find_agent_process(exe_name: str) -> Optional[dict]:
    """查找代理进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            if proc.info['name'] and exe_name.lower() in proc.info['name'].lower():
                return {
                    "pid": proc.info['pid'],
                    "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                    "memory_mb": round((proc.info['memory_info'] or 0) and proc.info['memory_info'].rss / 1024 / 1024, 1),
                    "running_since": datetime.fromtimestamp(proc.info['create_time'], tz=timezone.utc).isoformat() if proc.info['create_time'] else None,
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


@router.get("/status")
def agent_status(
    user: User = Depends(get_current_super_admin),
):
    """获取所有代理进程状态"""
    agents = []
    for key, info in AGENT_REGISTRY.items():
        proc = _find_agent_process(info["exe"])
        agents.append({
            "id": key,
            "name": info["name"],
            "icon": info["icon"],
            "description": info["description"],
            "running": proc is not None,
            "pid": proc["pid"] if proc else None,
            "cpu_percent": proc["cpu_percent"] if proc else 0,
            "memory_mb": proc["memory_mb"] if proc else 0,
            "running_since": proc["running_since"] if proc else None,
        })

    return success_response(data=agents)


@router.post("/{agent_id}/start")
def start_agent(
    agent_id: str,
    user: User = Depends(get_current_super_admin),
):
    """启动代理进程（Windows）"""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="未知代理")

    info = AGENT_REGISTRY[agent_id]
    existing = _find_agent_process(info["exe"])
    if existing:
        return success_response(data={"pid": existing["pid"]}, message="已在运行中")

    if sys.platform != "win32":
        raise HTTPException(status_code=400, detail="仅支持 Windows 平台启动代理")

    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "smart_agent_workflow",
    )
    exe_path = os.path.join(base_dir, info["exe"])
    if not os.path.exists(exe_path):
        raise HTTPException(status_code=404, detail=f"可执行文件不存在: {exe_path}")

    try:
        proc = subprocess.Popen(
            [exe_path],
            cwd=base_dir,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return success_response(data={"pid": proc.pid}, message=f"{info['name']} 已启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/stop")
def stop_agent(
    agent_id: str,
    user: User = Depends(get_current_super_admin),
):
    """停止代理进程"""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="未知代理")

    info = AGENT_REGISTRY[agent_id]
    proc = _find_agent_process(info["exe"])
    if not proc:
        return success_response(message="进程未在运行")

    try:
        p = psutil.Process(proc["pid"])
        p.terminate()
        p.wait(timeout=10)
        return success_response(message=f"{info['name']} 已停止")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/resources")
def system_resources(
    user: User = Depends(get_current_super_admin),
):
    """系统资源概览"""
    cpu = psutil.cpu_percent(interval=0.5, percpu=True)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return success_response(data={
        "cpu": {
            "total_percent": psutil.cpu_percent(interval=0.1),
            "per_core": cpu,
            "cores": psutil.cpu_count(),
        },
        "memory": {
            "total_gb": round(mem.total / 1024**3, 1),
            "used_gb": round(mem.used / 1024**3, 1),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "percent": disk.percent,
        },
        "network": {
            "sent_mb": round(net.bytes_sent / 1024**2, 1),
            "recv_mb": round(net.bytes_recv / 1024**2, 1),
        },
        "process_count": len(psutil.pids()),
    })


# === MCP Bridge ===
class MCPConfigUpdate(BaseModel):
    server_name: str
    command: str = ""
    args: list = []
    env: dict = {}
    enabled: bool = True


@router.get("/mcp/config")
def get_mcp_config(
    user: User = Depends(get_current_super_admin),
):
    """获取 MCP 服务器配置"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        ".cursor", "mcp.json",
    )
    if os.path.exists(config_path):
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            return success_response(data=json.load(f))
    return success_response(data={"mcpServers": {}})


@router.post("/mcp/config")
def update_mcp_config(
    body: MCPConfigUpdate,
    user: User = Depends(get_current_super_admin),
):
    """更新 MCP 服务器配置"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        ".cursor", "mcp.json",
    )
    import json
    config = {"mcpServers": {}}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    config["mcpServers"][body.server_name] = {
        "command": body.command,
        "args": body.args,
        "env": body.env,
        "enabled": body.enabled,
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return success_response(message="MCP 配置已更新")
