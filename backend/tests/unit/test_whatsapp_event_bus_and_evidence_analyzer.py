# -*- coding: utf-8 -*-
"""WhatsApp 入站事件总线 + Browser 证据自动分析 单元测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.core.event_bus import EventTypes
from app.services.browser_runtime.evidence import EvidenceRecord
from app.services.browser_runtime.evidence_analyzer import (
    SEVERITY_CRITICAL,
    SEVERITY_WARN,
    EvidenceAnalyzer,
)
from app.services.whatsapp_event_bus import (
    WhatsAppInboundEventBus,
    normalize_inbound_payload,
    verify_inbound_token,
)


class TestWhatsAppNormalize:
    def test_normalize_common_fields(self):
        norm = normalize_inbound_payload(
            {
                "phone": "+86 138-0000-0000",
                "body": "hello RFQ",
                "msg_id": "m1",
                "tenant_id": "t1",
                "lead_id": "L1",
            }
        )
        assert norm["phone"] == "+8613800000000"
        assert norm["body"] == "hello RFQ"
        assert norm["msg_id"] == "m1"
        assert norm["tenant_id"] == "t1"
        assert norm["lead_id"] == "L1"

    def test_normalize_baileys_shape(self):
        norm = normalize_inbound_payload(
            {
                "key": {"remoteJid": "15551234567@s.whatsapp.net", "id": "BAI1"},
                "message": {"conversation": "price please"},
                "pushName": "Buyer",
            }
        )
        assert norm["phone"] == "15551234567"
        assert norm["body"] == "price please"
        assert norm["msg_id"] == "BAI1"
        assert norm["from_name"] == "Buyer"

    def test_normalize_cloud_api_shape(self):
        norm = normalize_inbound_payload(
            {
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "447700900000",
                                            "id": "WAMID.1",
                                            "type": "text",
                                            "text": {"body": "need PI"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        )
        assert norm["phone"] == "447700900000"
        assert norm["body"] == "need PI"
        assert norm["msg_id"] == "WAMID.1"


class TestWhatsAppInboundEventBus:
    def test_token_open_when_unconfigured(self, monkeypatch):
        monkeypatch.delenv("WHATSAPP_INBOUND_TOKEN", raising=False)
        assert verify_inbound_token(None) is True
        assert verify_inbound_token("anything") is True

    def test_token_enforced_when_configured(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_INBOUND_TOKEN", "secret")
        assert verify_inbound_token("secret") is True
        assert verify_inbound_token("bad") is False
        assert verify_inbound_token(None) is False

    def test_publish_inbound_emits_event(self, monkeypatch):
        bus = WhatsAppInboundEventBus()
        emitted = []

        def _capture(event):
            emitted.append(event)

        monkeypatch.setattr(
            "app.services.whatsapp_event_bus.event_bus.emit_sync",
            _capture,
            raising=False,
        )
        # emit_sync may not exist; patch emit as fallback by ensuring hasattr path
        # Re-run with explicit emit patch if needed
        import app.services.whatsapp_event_bus as mod

        if not hasattr(mod.event_bus, "emit_sync"):
            monkeypatch.setattr(mod.event_bus, "emit", _capture)

        result = bus.publish_inbound(
            {"phone": "+8613800000001", "body": "inbound hello", "tenant_id": "t-1"},
            db=None,
            persist=False,
        )
        assert result["accepted"] is True
        assert result["emitted"] is True
        assert result["event_id"]
        assert result["normalized"]["phone"] == "+8613800000001"
        assert emitted, "event should be published"
        assert emitted[0].event_type == EventTypes.WHATSAPP_MESSAGE_RECEIVED
        assert emitted[0].data["body"] == "inbound hello"
        assert bus.stats["received"] == 1
        assert bus.stats["emitted"] == 1

    def test_publish_inbound_empty_rejected(self):
        bus = WhatsAppInboundEventBus()
        result = bus.publish_inbound({}, db=None, persist=False)
        assert result["accepted"] is False
        assert result["error"] == "empty_inbound_payload"

    def test_publish_inbound_persist_calls_store(self, monkeypatch):
        bus = WhatsAppInboundEventBus()
        captured = {}

        def _fake_persist(db, **kwargs):
            captured.update(kwargs)
            return {"persisted": True, "id": "row-1", "status": "received"}

        monkeypatch.setattr(
            "app.services.trade_fulfillment_store.persist_whatsapp_message",
            _fake_persist,
        )
        monkeypatch.setattr(
            "app.services.whatsapp_event_bus.event_bus.emit",
            lambda e: None,
        )
        monkeypatch.setattr(
            "app.services.whatsapp_event_bus.event_bus.emit_sync",
            lambda e: None,
            raising=False,
        )
        import app.services.whatsapp_event_bus as mod

        # Force emit path
        monkeypatch.setattr(mod.event_bus, "emit", lambda e: None, raising=False)

        db = MagicMock()
        result = bus.publish_inbound(
            {"phone": "15550001111", "body": "persist me", "inquiry_id": "inq-1"},
            db=db,
            persist=True,
        )
        assert result["accepted"] is True
        assert result["persisted"]["persisted"] is True
        assert captured.get("direction") == "inbound"
        assert captured.get("phone_e164") == "15550001111"
        assert captured.get("inquiry_id") == "inq-1"
        assert bus.stats["persisted"] == 1

    def test_publish_ack_failed_maps_to_failed_event(self, monkeypatch):
        bus = WhatsAppInboundEventBus()
        events = []
        monkeypatch.setattr(
            "app.services.whatsapp_event_bus.event_bus.emit",
            lambda e: events.append(e),
        )
        # publish_ack 优先走 emit_sync（无事件循环时会回退），两处都要拦截
        monkeypatch.setattr(
            "app.services.whatsapp_event_bus.event_bus.emit_sync",
            lambda e: events.append(e),
            raising=False,
        )
        result = bus.publish_ack(phone="1555", msg_id="m1", ack_type="failed")
        assert result["event_type"] == EventTypes.WHATSAPP_MESSAGE_FAILED
        assert events and events[0].event_type == EventTypes.WHATSAPP_MESSAGE_FAILED


class TestEvidenceAnalyzer:
    def _record(self, **kwargs) -> EvidenceRecord:
        rec = EvidenceRecord(actor="test", action="navigate")
        rec.status = "success"
        for k, v in kwargs.items():
            setattr(rec, k, v)
        return rec

    def test_analyze_failed_execution(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        rec = self._record(action="extract", status="failed", error_code="TIMEOUT")
        rec.error_message = "nav timeout"
        findings = analyzer.analyze_one(rec)
        codes = {f.code for f in findings}
        assert "EXEC_FAILED" in codes

    def test_analyze_policy_blocked_critical(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        rec = self._record(action="submit", status="blocked")
        rec.policy_verdict = {"verdict": "deny", "reason": "not_allowlisted"}
        findings = analyzer.analyze_one(rec)
        assert any(f.code == "POLICY_BLOCKED" and f.severity == SEVERITY_CRITICAL for f in findings)

    def test_analyze_submit_without_approval(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        rec = self._record(action="submit", status="success", submit_auto=True, submit_approval_id=None)
        findings = analyzer.analyze_one(rec)
        assert any(f.code == "SUBMIT_WITHOUT_APPROVAL" for f in findings)

    def test_analyze_slow_execution(self):
        analyzer = EvidenceAnalyzer(emit_events=False, slow_ms=1000)
        rec = self._record(action="navigate", status="success", duration_ms=5000)
        findings = analyzer.analyze_one(rec)
        assert any(f.code == "SLOW_EXECUTION" for f in findings)

    def test_analyze_sensitive_without_screenshot(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        rec = self._record(action="submit", status="success", submit_auto=False, submit_approval_id="a1")
        findings = analyzer.analyze_one(rec)
        assert any(f.code == "SENSITIVE_WITHOUT_SCREENSHOT" for f in findings)

    def test_batch_report_metrics(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        records = [
            self._record(action="navigate", status="success"),
            self._record(action="extract", status="failed", error_code="X"),
            self._record(action="submit", status="blocked", policy_verdict={"verdict": "deny"}),
            self._record(action="click", status="degraded", error_code="NOOP"),
        ]
        report = analyzer.analyze_batch(records)
        assert report.total == 4
        assert report.success_count == 1
        assert report.failed_count == 1
        assert report.blocked_count == 1
        assert report.degraded_count == 1
        assert report.has_anomaly is True
        assert report.max_severity == SEVERITY_CRITICAL
        assert report.compliance_ok is False

    def test_analyze_and_emit_publishes_events(self, monkeypatch):
        analyzer = EvidenceAnalyzer(emit_events=True)
        events = []
        monkeypatch.setattr(
            "app.services.browser_runtime.evidence_analyzer.event_bus.emit_sync",
            lambda e: events.append(e),
            raising=False,
        )
        monkeypatch.setattr(
            "app.services.browser_runtime.evidence_analyzer.event_bus.emit",
            lambda e: events.append(e),
        )
        rec = self._record(action="submit", status="blocked", policy_verdict={"verdict": "deny"})
        result = analyzer.analyze_and_emit(rec, tenant_id="t-9")
        assert result["has_anomaly"] is True
        types = {e.event_type for e in events}
        assert EventTypes.EVIDENCE_ANALYZED in types
        assert EventTypes.EVIDENCE_ANOMALY in types

    def test_clean_record_no_anomaly(self):
        analyzer = EvidenceAnalyzer(emit_events=False)
        rec = self._record(
            action="navigate",
            status="success",
            duration_ms=120,
            target_url="https://example.com/pricing",
        )
        findings = analyzer.analyze_one(rec)
        assert findings == []


class TestPersistEvidenceAutoAnalyze:
    def test_persist_evidence_includes_analysis_field(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BROWSER_EVIDENCE_DIR", str(tmp_path))
        monkeypatch.setenv("EVIDENCE_AUTO_ANALYZE", "1")
        from app.services.browser_runtime.evidence import persist_evidence

        rec = EvidenceRecord(actor="t", action="navigate", status="success")
        rec.target_url = "https://ok.example"
        rec.duration_ms = 50
        result = persist_evidence(rec, db=None)
        assert result["disk"] is True
        assert "analysis" in result
        assert result["analysis"]["has_anomaly"] is False
