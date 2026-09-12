"""调用上游 UserActionAnalyzePlatform Spark 作业（vendor 目录内 Maven 工程）。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def vendor_root() -> Path:
    env = (os.getenv("USER_ACTION_ANALYTICS_REPO") or "").strip()
    if env:
        return Path(env)
    # compose 默认挂载
    return Path("/opt/UserActionAnalyzePlatform")


def jar_path() -> Path | None:
    root = vendor_root()
    target = root / "target"
    if not target.is_dir():
        return None
    jars = sorted(target.glob("*jar-with-dependencies.jar"), key=lambda p: p.stat().st_mtime, reverse=True)
    if jars:
        return jars[0]
    jars = sorted(target.glob("*.jar"), key=lambda p: p.stat().st_mtime, reverse=True)
    return jars[0] if jars else None


def write_conf_properties(mysql_host: str, mysql_port: int, mysql_db: str, user: str, password: str) -> Path:
    root = vendor_root()
    resources = root / "src" / "main" / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    conf = resources / "conf.properties"
    jdbc_url = f"jdbc:mysql://{mysql_host}:{mysql_port}/{mysql_db}?useUnicode=true&characterEncoding=utf8"
    conf.write_text(
        "\n".join(
            [
                "jdbc.driver=com.mysql.jdbc.Driver",
                f"jdbc.url={jdbc_url}",
                f"jdbc.username={user}",
                f"jdbc.password={password}",
                "jdbc.active=true",
                "spark_local=true",
            ]
        ),
        encoding="utf-8",
    )
    return conf


def build_vendor() -> tuple[bool, str]:
    root = vendor_root()
    pom = root / "pom.xml"
    if not pom.is_file():
        return False, f"未找到上游工程：{root}（请运行 scripts/install-user-action-analytics-vendor.ps1）"
    try:
        proc = subprocess.run(
            ["mvn", "-q", "package", "-DskipTests"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "mvn package failed")[:500]
        return True, "built"
    except FileNotFoundError:
        return False, "未安装 Maven；请在 Sidecar 镜像内预构建 jar 或挂载 target/"


def run_session_spark_job(task_id: int) -> tuple[bool, str]:
    """运行 cn.edu.hust.session.UserVisitAnalyze（上游 session 模块）。"""
    root = vendor_root()
    jp = jar_path()
    if jp is None:
        ok, msg = build_vendor()
        if not ok:
            return False, msg
        jp = jar_path()
    if jp is None:
        return False, "未找到 Spark jar，请先 mvn package"

    # 同步 MySQL 配置到上游 conf.properties
    from mysql_repo import _mysql_config

    cfg = _mysql_config()
    write_conf_properties(cfg["host"], int(cfg["port"]), cfg["database"], cfg["user"], cfg["password"])

    cmd = [
        "java",
        "-cp",
        str(jp),
        "cn.edu.hust.session.UserVisitAnalyze",
        str(task_id),
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=int(os.getenv("USER_ACTION_SPARK_TIMEOUT_SEC", "900")),
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "")[:800]
            return False, err or f"exit {proc.returncode}"
        return True, str(jp)
    except subprocess.TimeoutExpired:
        return False, "Spark 作业超时"
    except Exception as exc:
        return False, str(exc)[:300]
