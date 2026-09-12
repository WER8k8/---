"""Hermes TaskGraph and Intent Orchestration Schemas (Plan-as-Data)."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

class ReplyToConfig(BaseModel):
    channel: str = Field(..., description="e.g., 'n8n', 'web', 'api', 'email'")
    webhook: Optional[str] = Field(None, description="Callback URL for completion")

class IntentEvent(BaseModel):
    event_id: str = Field(..., description="Unique ID for this orchestration event")
    tenant_id: str = Field(..., description="Tenant ID")
    channel: str = Field(..., description="Trigger channel (n8n, web, heartbeat)")
    intent: str = Field(..., description="The high-level intent, e.g., 'generate_site', 'find_leads'")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Business parameters from the user")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context, language, quota hints, etc.")
    reply_to: Optional[ReplyToConfig] = None

class TaskBudget(BaseModel):
    max_tokens: Optional[int] = None
    max_seconds: Optional[int] = 600

class TaskRetryPolicy(BaseModel):
    max: int = 2
    backoff: Literal["linear", "exp"] = "exp"

class TaskNode(BaseModel):
    id: str = Field(..., description="Unique node ID in the graph")
    executor: str = Field(..., description="Which executor to use: 'deerflow', 'accio', 'ai_engine', 'n8n', etc.")
    capability: str = Field(..., description="Specific capability required, e.g., 'media.upload', 'site.generate'")
    depends_on: List[str] = Field(default_factory=list, description="IDs of nodes that must complete first")
    input: Dict[str, Any] = Field(default_factory=dict, description="Static inputs")
    input_from: Dict[str, str] = Field(default_factory=dict, description="Dynamic inputs mapped from other nodes' outputs (e.g., 'product_images': 'n1.output.urls')")
    sop_ref: Optional[str] = Field(None, description="ECC knowledge/SOP injection point")
    persona_ref: Optional[str] = Field(None, description="AgencyZH role/persona injection point; resolved at runtime by the executor (never fabricated)")
    model_hint: Optional[str] = Field(None, description="e.g., 'glm', 'deepseek'")
    retry: TaskRetryPolicy = Field(default_factory=TaskRetryPolicy)
    budget: TaskBudget = Field(default_factory=TaskBudget)
    on_fail: str = Field(default="abort", description="'abort', 'skip', or 'degrade:<fallback_node_id>'")
    compensation_action: Optional[str] = Field(None, description="Saga pattern rollback action (e.g., 'site.draft.delete', 'budget.refund')")

class GraphPolicies(BaseModel):
    max_parallel: int = 3
    budget_cap: Optional[Dict[str, int]] = None
    approval_required: List[str] = Field(default_factory=list, description="Regex/wildcards for nodes requiring human approval")
    degradation: Optional[str] = None

class TaskGraph(BaseModel):
    plan_id: str = Field(..., description="Unique ID for this graph execution")
    event_id: str = Field(..., description="Corresponds to IntentEvent.event_id")
    strategy: str = Field(default="standard", description="'deep', 'fast', 'cheap'")
    nodes: List[TaskNode] = Field(..., description="The DAG of tasks to execute")
    policies: GraphPolicies = Field(default_factory=GraphPolicies)

class ExecutorResult(BaseModel):
    node_id: str
    status: Literal["succeeded", "failed", "skipped", "degraded", "aborted"]
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    evidence_id: Optional[str] = None
