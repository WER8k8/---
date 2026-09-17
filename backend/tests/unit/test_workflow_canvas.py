import pytest
import asyncio
from app.services.workflow_canvas_service import WorkflowCanvasService
from app.api.v1.routes.workflow_canvas import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.core.security import require_admin
from app.models.user import User

app = FastAPI()
app.include_router(router)
app.dependency_overrides[require_admin] = lambda: User(id="admin_test", role="admin", is_active=True)
client = TestClient(app)

def test_workflow_service_execution():
    service = WorkflowCanvasService()
    workflow_data = {
        "nodes": [
            {"id": "n1", "type": "start", "data": {}},
            {"id": "n2", "type": "llm", "data": {"prompt": "test"}},
            {"id": "n3", "type": "end", "data": {}}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
    }
    result = asyncio.run(service.execute_workflow(workflow_data))
    assert result["status"] == "success"
    assert result["execution_trace"] == ["n1", "n2", "n3"]
    assert "llm_output" in result["context"]

def test_workflow_service_no_start():
    service = WorkflowCanvasService()
    workflow_data = {
        "nodes": [
            {"id": "n2", "type": "llm", "data": {"prompt": "test"}}
        ],
        "edges": []
    }
    with pytest.raises(ValueError, match="Workflow must have at least one 'start' node."):
        asyncio.run(service.execute_workflow(workflow_data))

def test_workflow_api_execute():
    payload = {
        "nodes": [
            {"id": "n1", "type": "start", "data": {}},
            {"id": "n2", "type": "llm", "data": {"prompt": "test"}},
            {"id": "n3", "type": "end", "data": {}}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
    }
    response = client.post("/workflow/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["execution_trace"] == ["n1", "n2", "n3"]

def test_workflow_api_execute_error():
    payload = {
        "nodes": [
            {"id": "n2", "type": "llm", "data": {"prompt": "test"}}
        ],
        "edges": []
    }
    response = client.post("/workflow/execute", json=payload)
    assert response.status_code == 400
    assert "start" in response.json()["detail"]
