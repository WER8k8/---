"""自动备份服务 — 每日凌晨3点执行，保留最近7天"""

import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("uj-admin.backup")

BACKUP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups"
)


class AutoBackup:
    _instance = None
    _running = False
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """_init。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.last_run = None
        self.backup_count = 0
        self.errors = []
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def start(self):
        """start。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("Auto-backup started (daily at 03:00)")
        return {"status": "started", "backup_dir": BACKUP_DIR}

    def _loop(self):
        """_loop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        while self._running:
            now = datetime.now()
            # 计算到凌晨3点的等待时间
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait = (next_run - now).total_seconds()
            time.sleep(wait)
            if self._running:
                try:
                    self.run_backup()
                except Exception as e:
                    logger.error(f"Backup failed: {e}")

    def run_backup(self) -> dict:
        """执行一次备份"""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"auto_backup_{ts}"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            # 1. 复制 SQLite 数据库
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "youding_dev.db",
            )
            if os.path.exists(db_path):
                shutil.copy2(db_path, os.path.join(backup_path, "database.db"))

            # 2. 导出配置快照
            config_snapshot = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "backup_name": backup_name,
            }
            with open(os.path.join(backup_path, "snapshot.json"), "w") as f:
                json.dump(config_snapshot, f, indent=2, ensure_ascii=False)

            # 3. 清理超过7天的旧备份
            cutoff = datetime.now() - timedelta(days=7)
            for item in os.listdir(BACKUP_DIR):
                item_path = os.path.join(BACKUP_DIR, item)
                if os.path.isdir(item_path) and item.startswith("auto_backup_"):
                    try:
                        item_time = datetime.fromtimestamp(os.path.getmtime(item_path))
                        if item_time < cutoff:
                            shutil.rmtree(item_path)
                            logger.info(f"Removed old backup: {item}")
                    except Exception:
                        pass

            self.last_run = datetime.now(timezone.utc).isoformat()
            self.backup_count += 1
            logger.info(f"Backup completed: {backup_name}")
            return {"backup_name": backup_name, "path": backup_path}
        except Exception as e:
            self.errors.append(str(e))
            raise

    def get_status(self) -> dict:
        """get_status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        backups = []
        if os.path.exists(BACKUP_DIR):
            for item in sorted(os.listdir(BACKUP_DIR), reverse=True):
                item_path = os.path.join(BACKUP_DIR, item)
                if os.path.isdir(item_path) and item.startswith("auto_backup_"):
                    backups.append({
                        "name": item,
                        "time": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat(),
                        "size": _dir_size(item_path),
                    })

        return {
            "running": self._running,
            "last_run": self.last_run,
            "backup_count": self.backup_count,
            "backup_dir": BACKUP_DIR,
            "recent_backups": backups[:7],
            "errors_recent": self.errors[-5:],
        }


def _dir_size(path: str) -> str:
    """_dir_size。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    if total > 1024 * 1024:
        return f"{total / 1024 / 1024:.1f}MB"
    return f"{total / 1024:.0f}KB"


backup_service = AutoBackup()
