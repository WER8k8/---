# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""文件扫描任务登记 CRUD（path/label + 可选本地 os.walk 统计）。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.admin_kv_store import (
    load_items,
    log_admin_write,
    new_id,
    now_iso,
    save_items,
)

ROUTE_PREFIX = "/file-scans"
ROUTE_TAGS = ["文件管理"]

router = APIRouter()

KEY = "admin_file_scans"
_WALK_MAX_FILES = 5000


class FileScanCreate(BaseModel):
    path: str = Field(..., min_length=1, max_length=1000)
    label: str = ""
    severity: str = "info"
    note: str = ""


def _local_scan_stats(path_str: str) -> dict[str, Any]:
    """本地路径存在时做有限 os.walk 统计；不存在则诚实返回 unavailable。"""
    root = Path(path_str)
    if not root.exists():
        return {"available": False, "reason": "path_not_found"}
    if root.is_file():
        try:
            st = root.stat()
            return {
                "available": True,
                "kind": "file",
                "file_count": 1,
                "dir_count": 0,
                "total_bytes": st.st_size,
                "truncated": False,
            }
        except OSError as exc:
            return {"available": False, "reason": str(exc)}
    file_count = 0
    dir_count = 0
    total_bytes = 0
    truncated = False
    try:
        for dirpath, dirnames, filenames in os.walk(path_str):
            dir_count += len(dirnames)
            for name in filenames:
                file_count += 1
                try:
                    total_bytes += (Path(dirpath) / name).stat().st_size
                except OSError:
                    pass
                if file_count >= _WALK_MAX_FILES:
                    truncated = True
                    break
            if truncated:
                break
    except OSError as exc:
        return {"available": False, "reason": str(exc)}
    return {
        "available": True,
        "kind": "dir",
        "file_count": file_count,
        "dir_count": dir_count,
        "total_bytes": total_bytes,
        "truncated": truncated,
    }


@router.get("")
@router.get("/")
def list_file_scans(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    return success_response(data={"items": items, "total": len(items)})


@router.post("")
@router.post("/")
def create_file_scan(
    body: FileScanCreate,
    with_stats: bool = Query(True),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    path = body.path.strip()
    if not path:
        raise HTTPException(status_code=422, detail="path 不能为空")
    items = load_items(db, KEY)
    now = now_iso()
    item = {
        "id": new_id(),
        "path": path,
        "label": (body.label or "").strip(),
        "severity": body.severity or "info",
        "note": (body.note or "").strip(),
        "stats": _local_scan_stats(path) if with_stats else {"available": False, "reason": "skipped"},
        "created_at": now,
        "updated_at": now,
    }
    items.insert(0, item)
    save_items(db, KEY, items, "file scan registrations")
    log_admin_write(
        db,
        admin=admin,
        action="CREATE",
        resource_type="file_scan",
        resource_id=item["id"],
        detail={"path": path, "label": item["label"]},
    )
    return success_response(data=item, message="扫描任务已登记")


@router.delete("/{item_id}")
def delete_file_scan(
    item_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    items = load_items(db, KEY)
    before = len(items)
    items = [x for x in items if x.get("id") != item_id]
    if len(items) == before:
        raise HTTPException(status_code=404, detail="扫描任务不存在")
    save_items(db, KEY, items, "file scan registrations")
    log_admin_write(
        db,
        admin=admin,
        action="DELETE",
        resource_type="file_scan",
        resource_id=item_id,
    )
    return success_response(message="已删除")
