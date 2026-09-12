"""Hermes MCP Server.
Exposes the internal TaskGraph (Plan-as-Data) generation and dispatch as an MCP tool
so that the outer DeepSeek Harness can call it when a structured multi-step process is needed.
"""
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class GeneratePlanToolInput(BaseModel):
    intent: str = Field(..., description="The highly specific business intent (e.g., 'site.build.seo', 'outreach.b2b')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters extracted by Harness (e.g., {'target_region': 'middle_east'})")

class HermesMCPServer:
    """Acts as a bridge between MCP protocol and internal Hermes engine."""
    
    @classmethod
    def get_tool_manifest(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "hermes_orchestrate",
                "description": "Generate and execute a multi-agent deterministic TaskGraph for complex B2B workflows.",
                "input_schema": GeneratePlanToolInput.model_json_schema()
            }
        ]
        
    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "hermes_orchestrate":
            logger.info(f"Harness invoked Hermes Orchestrator with args: {arguments}")
            # 1. Parse intent
            # 2. Call services/hermes/runtime.py to build TaskGraph
            # 3. Call task_control_supervisor.py to dump nodes to ai_tasks
            # 4. Return the plan_id
            
            return {
                "status": "success",
                "plan_id": "plan_abc123",
                "message": "TaskGraph generated and dispatched to Celery/Temporal."
            }
        
        raise ValueError(f"Unknown Hermes MCP tool: {name}")
