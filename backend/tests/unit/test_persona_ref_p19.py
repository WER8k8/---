"""P1-9: persona_ref must survive TaskNode round-trip and resolve at runtime.

Locks in the two parts of the persona_ref fix:
  1. TaskNode now declares persona_ref (no more Pydantic v2 silent-drop).
  2. role_loader.resolve_persona_ref resolves a real role / returns None for
     missing input, and never fabricates a default persona.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.schemas.hermes_orchestration import TaskNode  # noqa: E402
from app.services.hermes.agency.role_loader import (  # noqa: E402
    list_roles,
    resolve_persona_ref,
)


def test_tasknode_has_persona_ref_field() -> None:
    assert "persona_ref" in TaskNode.model_fields
    # default is None (backward compatible: old graphs without persona_ref still validate)
    n = TaskNode.model_validate(
        {"id": "n1", "executor": "site_builder", "capability": "build", "input": {}}
    )
    assert n.persona_ref is None


def test_tasknode_persona_ref_round_trip_not_dropped() -> None:
    n = TaskNode.model_validate(
        {
            "id": "n1",
            "executor": "accio",
            "capability": "default",
            "persona_ref": "marketing/marketing-seo-specialist",
            "input": {},
        }
    )
    assert n.persona_ref == "marketing/marketing-seo-specialist"
    # and re-serializing keeps it
    dumped = n.model_dump()
    assert dumped.get("persona_ref") == "marketing/marketing-seo-specialist"


def test_resolve_persona_ref_none_input_returns_none() -> None:
    assert resolve_persona_ref(None) is None
    assert resolve_persona_ref("") is None
    assert resolve_persona_ref("   ") is None


def test_resolve_persona_ref_unknown_id_returns_none_no_fabrication() -> None:
    # a persona_ref that does not map to any AgencyZH role must resolve to None,
    # never a fabricated default persona (no-fake-delivery rule).
    assert resolve_persona_ref("does/not/exist-xyz") is None


def test_resolve_persona_ref_resolves_a_real_role_if_any() -> None:
    roles = list_roles()
    if not roles:
        # no roles dir in this env: the resolver must be safe to call and return None
        assert resolve_persona_ref(None) is None
        return
    target = roles[0]["role_id"]
    resolved = resolve_persona_ref(target)
    assert resolved is not None
    assert resolved["role_id"] == target
    assert "system_prompt" in resolved
