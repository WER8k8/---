"""断点残留回归：境内 IM 文案/链路 + 经验注入 + 调度器停机日志。"""

from __future__ import annotations


class TestImLocaleDomesticChannels:
    def test_channel_labels_include_cn_channels(self):
        from app.services.im_locale_service import CHANNEL_LABELS

        for key in ("wechat", "qq", "phone", "wecom_inquiry", "douyin_inquiry", "form"):
            assert key in CHANNEL_LABELS, f"CHANNEL_LABELS missing {key}"
            assert CHANNEL_LABELS[key].get("zh"), f"{key} missing zh label"

    def test_localized_label_not_fallback_contact_us_for_wechat(self):
        from app.services.im_locale_service import localized_channel_label

        assert localized_channel_label("wechat", "zh") == "微信咨询"
        assert localized_channel_label("qq", "zh") == "QQ 咨询"
        assert localized_channel_label("phone", "zh") == "电话咨询"
        assert localized_channel_label("wechat", "en") == "Chat on WeChat"

    def test_generate_im_link_cn_channels(self):
        from app.services.im_locale_service import generate_im_link

        assert generate_im_link("wechat", "youding-builder").startswith("weixin://")
        assert generate_im_link("qq", "123456").startswith("tencent://")
        assert generate_im_link("phone", "13800138000") == "tel:13800138000"
        assert generate_im_link("wechat", "") == "#inquiry-form"
        assert generate_im_link("wecom_inquiry", "") == "#inquiry-form"
        assert generate_im_link("douyin_inquiry", "") == "#inquiry-form"

    def test_cn_fallback_never_empty(self, monkeypatch):
        from app.services import im_locale_service as svc

        class _FakeDB:
            def query(self, *_a, **_k):
                class _Q:
                    def filter(self, *a, **k):
                        return self

                    def order_by(self, *a, **k):
                        return self

                    def all(self):
                        return []

                return _Q()

        channels = svc.resolve_im_channels(
            _FakeDB(), merchant_id=1, country_code="CN", language="zh"
        )
        assert channels, "CN resolve must never return empty"
        types = {c.channel_type for c in channels}
        assert "form" in types or "phone" in types


class TestExperienceHintsWiring:
    def test_get_experience_suggestions_callable(self):
        from app.services.deepseek_harness.client import get_experience_suggestions

        result = get_experience_suggestions("intent:test", top_k=3)
        assert isinstance(result, list)

    def test_record_intent_result_callable(self):
        from app.services.deepseek_harness.client import record_intent_result

        record_intent_result(intent="unit-test-intent", success=True)

    def test_planner_enrich_uses_local_engine(self, monkeypatch):
        from app.services.hermes import planner_service as ps

        class _Evt:
            intent = "unit.intent"
            scene_type = "unit.intent"
            event_id = "evt-1"
            tenant_id = "t1"
            payload = {"tenant_id": "t1"}

        monkeypatch.setattr(
            "app.services.deepseek_harness.client.get_experience_suggestions",
            lambda task_type, top_k=5: [
                {"key": "k1", "summary": "s1", "score": 0.9, "type": "hint"}
            ],
        )
        payload = ps._enrich_with_experience(_Evt(), db=None)
        hints = payload.get("_experience_hints") or []
        assert any(h.get("source") == "deepseek_local_engine" for h in hints)


class TestSchedulerStopLogging:
    def test_stop_helper_logs_not_silent(self):
        import inspect

        from app import main as main_mod

        src = inspect.getsource(main_mod)
        assert "_stop_schedulers_logged" in src
        # 停机路径不得再出现裸 except: pass
        assert "scheduler.stop()\n        except Exception:\n            pass" not in src
