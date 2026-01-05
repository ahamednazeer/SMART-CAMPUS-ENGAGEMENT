"""
WebSocket endpoints for real-time features.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Set
import json
import asyncio

from app.core.database import get_db, async_session_maker
from app.services.study_circle_service import StudyCircleService


router = APIRouter(prefix="/ws", tags=["WebSocket"])


# Connection managers for different features
class CircleConnectionManager:
    """Manages WebSocket connections for Study Circles."""
    
    def __init__(self):
        # channel_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel_id: int):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = set()
        self.active_connections[channel_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel_id: int):
        if channel_id in self.active_connections:
            self.active_connections[channel_id].discard(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]
    
    async def broadcast_to_channel(self, channel_id: int, message: dict, exclude: WebSocket = None):
        if channel_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[channel_id].discard(conn)


class WhiteboardConnectionManager:
    """Manages WebSocket connections for Whiteboard sessions."""
    
    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # session_id -> canvas state
        self.canvas_states: Dict[int, dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        
        # Send current canvas state to new connection
        if session_id in self.canvas_states:
            await websocket.send_json({
                "type": "canvas_state",
                "data": self.canvas_states[session_id]
            })
    
    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def broadcast_to_session(self, session_id: int, message: dict, exclude: WebSocket = None):
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        disconnected.append(connection)
            
            for conn in disconnected:
                self.active_connections[session_id].discard(conn)
    
    def update_canvas_state(self, session_id: int, state: dict):
        self.canvas_states[session_id] = state


# Initialize managers
circle_manager = CircleConnectionManager()
whiteboard_manager = WhiteboardConnectionManager()


@router.websocket("/circles/{circle_id}/channels/{channel_id}")
async def websocket_channel(
    websocket: WebSocket,
    circle_id: int,
    channel_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time channel messaging.
    
    Message types:
    - send_message: {type: "send_message", content: str, parent_id?: int}
    - typing: {type: "typing"}
    - stop_typing: {type: "stop_typing"}
    """
    # Simple token validation (in production, decode JWT properly)
    if not token:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    await circle_manager.connect(websocket, channel_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "send_message":
                # Save message to database
                async with async_session_maker() as db:
                    service = StudyCircleService(db)
                    # Get user_id from token (simplified - extract from JWT in production)
                    user_id = data.get("user_id", 1)
                    
                    message = await service.post_message(
                        channel_id=channel_id,
                        user_id=user_id,
                        content=data.get("content", ""),
                        parent_id=data.get("parent_id")
                    )
                    
                    if message:
                        await db.commit()
                        
                        # Broadcast to all connections in channel
                        await circle_manager.broadcast_to_channel(
                            channel_id,
                            {
                                "type": "new_message",
                                "message": {
                                    "id": message.id,
                                    "channel_id": message.channel_id,
                                    "user_id": message.user_id,
                                    "content": message.content,
                                    "parent_id": message.parent_id,
                                    "is_pinned": message.is_pinned,
                                    "created_at": message.created_at.isoformat()
                                }
                            }
                        )
            
            elif msg_type == "typing":
                await circle_manager.broadcast_to_channel(
                    channel_id,
                    {
                        "type": "user_typing",
                        "user_id": data.get("user_id", 1)
                    },
                    exclude=websocket
                )
            
            elif msg_type == "stop_typing":
                await circle_manager.broadcast_to_channel(
                    channel_id,
                    {
                        "type": "user_stop_typing",
                        "user_id": data.get("user_id", 1)
                    },
                    exclude=websocket
                )
    
    except WebSocketDisconnect:
        circle_manager.disconnect(websocket, channel_id)
        await circle_manager.broadcast_to_channel(
            channel_id,
            {"type": "user_left", "user_id": data.get("user_id", 1) if 'data' in dir() else 0}
        )


@router.websocket("/whiteboard/{session_id}")
async def websocket_whiteboard(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time whiteboard collaboration.
    
    Message types:
    - draw: {type: "draw", object: fabric.Object}
    - modify: {type: "modify", object_id: str, changes: dict}
    - delete: {type: "delete", object_id: str}
    - cursor_move: {type: "cursor_move", x: int, y: int}
    - full_canvas: {type: "full_canvas", objects: list}
    """
    if not token:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    await whiteboard_manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "draw":
                # Broadcast drawing action to all participants
                await whiteboard_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "object_added",
                        "object": data.get("object"),
                        "user_id": data.get("user_id")
                    },
                    exclude=websocket
                )
            
            elif msg_type == "modify":
                await whiteboard_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "object_modified",
                        "object_id": data.get("object_id"),
                        "changes": data.get("changes"),
                        "user_id": data.get("user_id")
                    },
                    exclude=websocket
                )
            
            elif msg_type == "delete":
                await whiteboard_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "object_deleted",
                        "object_id": data.get("object_id"),
                        "user_id": data.get("user_id")
                    },
                    exclude=websocket
                )
            
            elif msg_type == "cursor_move":
                await whiteboard_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "cursor_update",
                        "user_id": data.get("user_id"),
                        "x": data.get("x"),
                        "y": data.get("y"),
                        "color": data.get("color")
                    },
                    exclude=websocket
                )
            
            elif msg_type == "full_canvas":
                # Update stored canvas state
                whiteboard_manager.update_canvas_state(session_id, data.get("objects", []))
                await whiteboard_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "canvas_sync",
                        "objects": data.get("objects", [])
                    },
                    exclude=websocket
                )
    
    except WebSocketDisconnect:
        whiteboard_manager.disconnect(websocket, session_id)
        await whiteboard_manager.broadcast_to_session(
            session_id,
            {"type": "user_left", "user_id": data.get("user_id", 0) if 'data' in dir() else 0}
        )
