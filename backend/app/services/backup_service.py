# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""自动备份服务"""
import glob
import os
import shutil
from datetime import datetime


class BackupService:
    """SQLite数据库备份与恢复服务"""
    @staticmethod
    def backup_database():
        """备份数据库到backups/目录"""
        db_paths = ["youding_dev.db", "app.db"]
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for db in db_paths:
            if os.path.exists(db):
                dest = f"{backup_dir}/backup_{timestamp}.db"
                shutil.copy2(db, dest)
                return {"success": True, "path": dest, "size": os.path.getsize(dest)}
        return {"success": False, "error": "No database file found"}

    @staticmethod
    def list_backups():
        """列出所有备份文件"""
        files = sorted(glob.glob("backups/backup_*.db"), reverse=True)
        return [
            {
                "name": os.path.basename(f),
                "size": os.path.getsize(f),
                "time": os.path.getmtime(f),
            }
            for f in files[:20]
        ]

    @staticmethod
    def restore_backup(filename: str):
        """从备份文件恢复数据库"""
        src = f"backups/{filename}"
        if not os.path.exists(src):
            return {"success": False, "error": f"Backup file not found: {filename}"}
        shutil.copy2(src, "youding_dev.db")
        return {"success": True, "restored_from": filename}
