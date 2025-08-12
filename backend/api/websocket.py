import json
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.core.websocket import manager
from backend.core.auth import get_current_user_from_token
from backend.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authenticated connections")
):
    """WebSocket endpoint for real-time updates.
    
    Supports room-based subscriptions:
    - activity_feed: Global activity updates
    - proposal:{id}: Proposal-specific updates (votes, comments)
    
    Authentication is optional - guests can subscribe to public rooms.
    """
    connection_id = str(uuid.uuid4())
    user_id = None
    
    try:
        # Try to authenticate if token provided
        if token:
            try:
                user = await get_current_user_from_token(token)
                user_id = str(user.id)
                logger.info(f"Authenticated WebSocket connection", extra={
                    "connection_id": connection_id,
                    "user_id": user_id
                })
            except Exception as e:
                logger.warning(f"Invalid token for WebSocket connection", extra={
                    "connection_id": connection_id,
                    "error": str(e)
                })
        
        # Accept the connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Auto-join activity_feed room
        await manager.join_room(connection_id, "activity_feed")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "join_room":
                    room = message.get("room")
                    if room:
                        await manager.join_room(connection_id, room)
                
                elif message.get("type") == "leave_room":
                    room = message.get("room")
                    if room:
                        await manager.leave_room(connection_id, room)
                
                elif message.get("type") == "ping":
                    # Respond to client ping
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, connection_id)
                
                else:
                    logger.warning(f"Unknown message type", extra={
                        "connection_id": connection_id,
                        "message_type": message.get("type")
                    })
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected", extra={
                    "connection_id": connection_id
                })
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received", extra={
                    "connection_id": connection_id
                })
                continue
            except Exception as e:
                logger.error(f"Error handling WebSocket message", extra={
                    "connection_id": connection_id,
                    "error": str(e)
                })
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during connection", extra={
            "connection_id": connection_id
        })
    except Exception as e:
        logger.error(f"WebSocket connection error", extra={
            "connection_id": connection_id,
            "error": str(e)
        })
    finally:
        # Clean up connection
        manager.disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return manager.get_connection_stats()
