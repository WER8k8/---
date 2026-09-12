from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.workflow_canvas_service import WorkflowCanvasService

router = APIRouter(prefix="/workflow", tags=["workflow"])
service = WorkflowCanvasService()

class WorkflowNode(BaseModel):
    id: str
    type: str
    data: Dict[str, Any] = {}

class WorkflowEdge(BaseModel):
    source: str
    target: str

class WorkflowRequest(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

@router.post("/execute")
async def execute_workflow(request: WorkflowRequest):
    try:
        result = await service.execute_workflow(request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
