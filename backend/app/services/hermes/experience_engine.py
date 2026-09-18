# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""经验沉淀自进化引擎（Experience Engine）。

反哺外层 DSH 和内层 Hermes：从每次执行中提取经验，统计成功率与耗时，
生成改进建议，辅助后续任务校验与意图识别。
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json, hashlib, os, tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
RECORDS_FILE = DATA_DIR / "experience_records.json"


@dataclass
class ExperienceRecord:
    task_type: str
    success: bool
    duration: float
    error_type: Optional[str] = None
    solution_summary: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


_MAX_RECORDS = 10000


class ExperienceEngine:
    def __init__(self):
        self._records: List[ExperienceRecord] = []
        self._load()

    def _load(self):
        if not RECORDS_FILE.exists():
            return
        try:
            raw = json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
            records_data = raw["records"] if isinstance(raw, dict) and "records" in raw else raw
            self._records = [ExperienceRecord(**r) for r in records_data]
        except Exception as e:
            logger.warning("加载经验记录失败: %s", e)
            self._records = []

    def _save(self):
        try:
            payload = json.dumps({"records": [asdict(r) for r in self._records]}, ensure_ascii=False, indent=2)
            digest = hashlib.sha256(payload.encode()).hexdigest()
            fd, tmp = tempfile.mkstemp(dir=RECORDS_FILE.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(payload)
                os.replace(tmp, RECORDS_FILE)
            except Exception:
                os.unlink(tmp)
                raise
        except Exception as e:
            logger.error("保存经验记录失败: %s", e)

    def record(self, task_type: str, success: bool, duration: float,
               error_type: Optional[str] = None, solution: Optional[str] = None):
        """本地 JSON 记录（P2-1：非生产真源）。

        唯一真源 = Evolution PG（EvolutionEngine / ExperienceStore）。
        本方法仅作无库兜底；生产链路应走 acquisition.experience_feed / evolution.engine。
        """
        rec = ExperienceRecord(task_type=task_type, success=success, duration=duration, error_type=error_type, solution_summary=solution)
        self._records.append(rec)
        if len(self._records) > _MAX_RECORDS:
            self._records = self._records[-_MAX_RECORDS:]
        self._save()
        pg_persist = {"persisted": False, "reason": "skipped"}
        try:
            # 仅在可快速拿到连接时双写；禁止在请求/执行热路径上无限等连接池
            from sqlalchemy import text

            from app.core.database import SessionLocal
            from app.services.trade_fulfillment_store import persist_experience_record

            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                pg_persist = persist_experience_record(
                    db,
                    title=f"{task_type}:{'ok' if success else 'fail'}",
                    content=solution or error_type,
                    source_type="task",
                    source_id=task_type,
                    experience_type="success_pattern" if success else "failure_pattern",
                    score=1.0 if success else 0.0,
                    status="raw",
                    metadata={
                        "duration": duration,
                        "error_type": error_type,
                        "engine": "hermes_experience_engine",
                    },
                )
            finally:
                db.close()
        except Exception as pg_exc:  # noqa: BLE001
            pg_persist = {"persisted": False, "error": str(pg_exc)}
        return {
            "recorded": True,
            "engine": "hermes_json_fallback",
            "source_of_truth": "evolution_pg",
            "pg_experience_records": pg_persist,
            "note": "JSON 经验非主真源；PG experience_records 为业务侧双写",
        }

    def query(self, task_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        matched = [r for r in self._records if r.task_type == task_type]
        matched.sort(key=lambda r: (r.success, -r.duration), reverse=True)
        return [asdict(r) for r in matched[:top_k]]

    def evolve(self) -> List[Dict[str, Any]]:
        stats = self.get_stats()
        alerts = []
        for task_type, s in stats.items():
            if s["success_rate"] < 0.5:
                alerts.append({
                    "task_type": task_type,
                    "success_rate": s["success_rate"],
                    "avg_duration": s["avg_duration"],
                    "alert": f"成功率低于50%（{s['success_rate']:.1%}），建议审查该任务类型"
                })
        return alerts

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        by_type: Dict[str, List[ExperienceRecord]] = {}
        for r in self._records:
            by_type.setdefault(r.task_type, []).append(r)

        stats = {}
        for task_type, records in by_type.items():
            total = len(records)
            success = sum(1 for r in records if r.success)
            avg_dur = sum(r.duration for r in records) / total if total else 0
            stats[task_type] = {
                "total": total,
                "success": success,
                "failed": total - success,
                "success_rate": success / total if total else 0,
                "avg_duration": avg_dur
            }
        return stats


_engine: Optional[ExperienceEngine] = None


def get_engine() -> ExperienceEngine:
    global _engine
    if _engine is None:
        _engine = ExperienceEngine()
    return _engine
