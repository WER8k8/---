"""组件版本管理器测试。"""
import json
import pytest
from unittest.mock import patch
from app.services.component_version_manager import (
    ComponentVersionManager,
    ComponentVersion,
    _SNAPSHOT_PATH,
)


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    ComponentVersionManager._versions = {}
    monkeypatch.setattr(
        "app.services.component_version_manager._SNAPSHOT_PATH",
        tmp_path / "test_versions.json",
    )


class TestRegister:
    def test_register_and_current(self):
        cv = ComponentVersionManager.register("app.services.hermes", "1.0.0", "abc123")
        assert cv.module == "app.services.hermes"
        assert cv.version == "1.0.0"
        assert cv.hash == "abc123"
        assert ComponentVersionManager.current("app.services.hermes") == cv

    def test_register_multiple_versions(self):
        ComponentVersionManager.register("mod_a", "1.0.0")
        ComponentVersionManager.register("mod_a", "1.1.0")
        assert ComponentVersionManager.current("mod_a").version == "1.1.0"
        assert len(ComponentVersionManager.history("mod_a")) == 2


class TestHotReload:
    def test_reload_unknown_module(self):
        assert ComponentVersionManager.hot_reload("nonexistent.module") is False

    def test_reload_loaded_module(self):
        import os
        ComponentVersionManager.register("os", "1.0.0")
        assert ComponentVersionManager.hot_reload("os") is True


class TestRollback:
    def test_rollback_no_history(self):
        ComponentVersionManager.register("mod_x", "1.0.0")
        assert ComponentVersionManager.rollback("mod_x") is False

    def test_rollback_to_previous(self):
        import os
        ComponentVersionManager.register("os", "1.0.0")
        ComponentVersionManager.register("os", "2.0.0")
        assert ComponentVersionManager.rollback("os") is True

    def test_rollback_to_specific_version(self):
        import os
        ComponentVersionManager.register("os", "1.0.0")
        ComponentVersionManager.register("os", "2.0.0")
        ComponentVersionManager.register("os", "3.0.0")
        assert ComponentVersionManager.rollback("os", "1.0.0") is True


class TestPersistence:
    def test_persist_and_load(self, tmp_path, monkeypatch):
        path = tmp_path / "cv.json"
        monkeypatch.setattr("app.services.component_version_manager._SNAPSHOT_PATH", path)
        ComponentVersionManager.register("mod_p", "1.0.0", "hash1")
        assert path.exists()
        data = json.loads(path.read_text())
        assert "mod_p" in data
        assert data["mod_p"][0]["version"] == "1.0.0"

    def test_load_snapshot(self, tmp_path, monkeypatch):
        path = tmp_path / "cv2.json"
        monkeypatch.setattr("app.services.component_version_manager._SNAPSHOT_PATH", path)
        path.write_text(json.dumps({"mod_q": [{"module": "mod_q", "version": "0.9.0", "loaded_at": 0, "hash": "", "status": "active"}]}))
        ComponentVersionManager.load_snapshot()
        assert ComponentVersionManager.current("mod_q").version == "0.9.0"


class TestListAll:
    def test_list_all(self):
        ComponentVersionManager.register("a", "1.0")
        ComponentVersionManager.register("b", "2.0")
        result = ComponentVersionManager.list_all()
        assert set(result.keys()) == {"a", "b"}
