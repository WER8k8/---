# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.core.security import require_admin
from app.models.user import User
from app.services.workflow_canvas_service import WorkflowCanvasService

ROUTE_PREFIX = ""
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
async def execute_workflow(request: WorkflowRequest, _admin: User = Depends(require_admin)):
    try:
        result = await service.execute_workflow(request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
