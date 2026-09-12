"""MCP SSE Transport Route for Hermes Brain.
This exposes the Hermes Orchestrator via standard Server-Sent Events (SSE)
so that external systems like DeepSeek Harness can connect as an MCP Client.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from sqlalchemy.orm import Session
from app.api import deps
from app.services.hermes.hermes_mcp_server import HermesMCPServer

router = APIRouter()
logger = logging.getLogger(__name__)

# Mocked event bus channel for SSE
mcp_clients = []

@router.get("/sse")
async def mcp_sse_connection(request: Request):
    """Establishes an SSE connection for the MCP protocol."""
    
    async def event_generator():
        client_id = id(request)
        logger.info(f"New MCP Client Connected: {client_id}")
        # Send initial endpoint definition
        yield f"event: endpoint\ndata: /api/v1/mcp/messages?client_id={client_id}\n\n"
        
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"MCP Client Disconnected: {client_id}")
                    break
                await asyncio.sleep(1) # Keep-alive heartbeat
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/messages")
async def mcp_messages(request: Request, client_id: str, db: Session = Depends(deps.get_db)):
    """Receives JSON-RPC messages from the MCP client."""
    payload = await request.json()
    logger.info(f"Received MCP Message from {client_id}: {payload}")
    
    # 1. Handle tool requests
    if payload.get("method") == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "result": {
                "tools": HermesMCPServer.get_tool_manifest()
            }
        }
        
    elif payload.get("method") == "tools/call":
        params = payload.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        try:
            result = await HermesMCPServer.call_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": False
                }
            }
        except Exception as e:
            logger.error(f"MCP Tool Execution Failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {
                    "content": [{"type": "text", "text": str(e)}],
                    "isError": True
                }
            }
            
    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}}
