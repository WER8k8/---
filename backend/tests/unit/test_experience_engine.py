"""经验引擎单元测试。"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch
from app.services.hermes.experience_engine import ExperienceEngine, ExperienceRecord


@pytest.fixture
def temp_data_dir(tmp_path):
    with patch("app.services.hermes.experience_engine.DATA_DIR", tmp_path), \
         patch("app.services.hermes.experience_engine.RECORDS_FILE", tmp_path / "test_records.json"):
        yield tmp_path


def test_record_creates_entry(temp_data_dir):
    engine = ExperienceEngine()
    engine.record("test_task", True, 1.5, solution="固定方案")

    assert len(engine._records) == 1
    rec = engine._records[0]
    assert rec.task_type == "test_task"
    assert rec.success is True
    assert rec.duration == 1.5
    assert rec.solution_summary == "固定方案"


def test_query_returns_sorted_results(temp_data_dir):
    engine = ExperienceEngine()
    engine.record("task_a", False, 2.0)
    engine.record("task_a", True, 1.0)
    engine.record("task_a", True, 3.0)
    engine.record("task_b", True, 0.5)

    results = engine.query("task_a", top_k=2)
    assert len(results) == 2
    assert all(r["task_type"] == "task_a" for r in results)
    assert results[0]["success"] is True


def test_query_empty_for_unknown_type(temp_data_dir):
    engine = ExperienceEngine()
    results = engine.query("unknown_task")
    assert results == []


def test_evolve_generates_alerts(temp_data_dir):
    engine = ExperienceEngine()
    engine.record("good_task", True, 1.0)
    engine.record("good_task", True, 1.0)
    engine.record("bad_task", False, 2.0)
    engine.record("bad_task", False, 2.0)
    engine.record("bad_task", True, 1.5)

    alerts = engine.evolve()
    assert len(alerts) == 1
    assert alerts[0]["task_type"] == "bad_task"
    assert alerts[0]["success_rate"] < 0.5
    assert "成功率低于50%" in alerts[0]["alert"]


def test_evolve_no_alerts_when_all_good(temp_data_dir):
    engine = ExperienceEngine()
    engine.record("task", True, 1.0)
    engine.record("task", True, 1.0)

    alerts = engine.evolve()
    assert alerts == []


def test_get_stats_calculates_correctly(temp_data_dir):
    engine = ExperienceEngine()
    engine.record("task_a", True, 1.0)
    engine.record("task_a", True, 2.0)
    engine.record("task_a", False, 3.0)
    engine.record("task_b", True, 0.5)

    stats = engine.get_stats()
    assert "task_a" in stats
    assert "task_b" in stats

    a_stats = stats["task_a"]
    assert a_stats["total"] == 3
    assert a_stats["success"] == 2
    assert a_stats["failed"] == 1
    assert abs(a_stats["success_rate"] - 2/3) < 0.01
    assert abs(a_stats["avg_duration"] - 2.0) < 0.01

    b_stats = stats["task_b"]
    assert b_stats["total"] == 1
    assert b_stats["success_rate"] == 1.0


def test_json_persistence(temp_data_dir):
    engine1 = ExperienceEngine()
    engine1.record("persist_task", True, 1.5, error_type="timeout", solution="重试")

    records_file = temp_data_dir / "test_records.json"
    assert records_file.exists()

    data = json.loads(records_file.read_text(encoding="utf-8"))
    records = data["records"] if isinstance(data, dict) and "records" in data else data
    assert len(records) == 1
    assert records[0]["task_type"] == "persist_task"

    engine2 = ExperienceEngine()
    assert len(engine2._records) == 1
    assert engine2._records[0].task_type == "persist_task"
    assert engine2._records[0].solution_summary == "重试"


def test_experience_record_dataclass():
    rec = ExperienceRecord("test", True, 1.0, error_type="err", solution_summary="sol")
    assert rec.task_type == "test"
    assert rec.success is True
    assert rec.duration == 1.0
    assert rec.error_type == "err"
    assert rec.solution_summary == "sol"
    assert rec.timestamp is not None
