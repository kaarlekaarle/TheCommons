import json
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and room-based broadcasting."""
    
    def __init__(self):
        # Active connections: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Room subscriptions: room_name -> set of connection_ids
        self.rooms: Dict[str, Set[str]] = {}
        
        # Connection metadata: connection_id -> metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Heartbeat task
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "rooms": set()
        }
        
        logger.info(f"WebSocket connected", extra={
            "connection_id": connection_id,
            "user_id": user_id
        })
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection and clean up all associated data."""
        if connection_id not in self.active_connections:
            logger.debug(f"Connection {connection_id} already disconnected")
            return
        
        # Get rooms before removing metadata
        rooms_to_leave = set()
        if connection_id in self.connection_metadata:
            rooms_to_leave = self.connection_metadata[connection_id]["rooms"].copy()
        
        # Remove from all rooms
        for room in rooms_to_leave:
            self._leave_room_internal(connection_id, room)
        
        # Remove connection and metadata
        del self.active_connections[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket disconnected", extra={
            "connection_id": connection_id,
            "rooms_cleaned": len(rooms_to_leave)
        })
    
    def _leave_room_internal(self, connection_id: str, room: str):
        """Internal method to remove a connection from a room without sending messages."""
        if room in self.rooms:
            self.rooms[room].discard(connection_id)
            # Remove empty rooms
            if not self.rooms[room]:
                del self.rooms[room]
                logger.debug(f"Removed empty room: {room}")
        
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["rooms"].discard(room)
    
    async def leave_room(self, connection_id: str, room: str):
        """Remove a connection from a room (idempotent)."""
        if connection_id not in self.active_connections:
            logger.debug(f"Cannot leave room {room}: connection {connection_id} not found")
            return
        
        if room not in self.rooms or connection_id not in self.rooms[room]:
            logger.debug(f"Connection {connection_id} not in room {room}")
            return
        
        # Remove from room
        self._leave_room_internal(connection_id, room)
        
        # Send confirmation to client
        await self.send_personal_message({
            "type": "room_left",
            "room": room
        }, connection_id)
        
        logger.info(f"Left room", extra={
            "connection_id": connection_id,
            "room": room
        })
    
    async def leave_all_rooms(self, connection_id: str):
        """Remove a connection from all rooms (idempotent)."""
        if connection_id not in self.active_connections:
            logger.debug(f"Cannot leave all rooms: connection {connection_id} not found")
            return
        
        if connection_id not in self.connection_metadata:
            return
        
        # Get all rooms before removing
        rooms_to_leave = list(self.connection_metadata[connection_id]["rooms"])
        
        for room in rooms_to_leave:
            await self.leave_room(connection_id, room)
        
        logger.info(f"Left all rooms", extra={
            "connection_id": connection_id,
            "rooms_left": len(rooms_to_leave)
        })
    
    async def join_room(self, connection_id: str, room: str):
        """Add a connection to a room."""
        if connection_id not in self.active_connections:
            logger.warning(f"Cannot join room {room}: connection {connection_id} not found")
            return
        
        if room not in self.rooms:
            self.rooms[room] = set()
        
        self.rooms[room].add(connection_id)
        
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["rooms"].add(room)
        
        # Send confirmation to client
        await self.send_personal_message({
            "type": "room_joined",
            "room": room
        }, connection_id)
        
        logger.info(f"Joined room", extra={
            "connection_id": connection_id,
            "room": room
        })
    
    async def broadcast_to_room(self, message: Dict[str, Any], room: str):
        """Broadcast a message to all connections in a room with robust error handling."""
        if room not in self.rooms:
            logger.debug(f"Room {room} not found for broadcast")
            return
        
        disconnected_connections = []
        successful_sends = 0
        
        # Create a copy of the room connections to avoid modification during iteration
        room_connections = list(self.rooms[room])
        
        for connection_id in room_connections:
            if connection_id not in self.active_connections:
                # Connection was already removed
                disconnected_connections.append(connection_id)
                continue
            
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
                successful_sends += 1
            except WebSocketDisconnect:
                logger.debug(f"WebSocket disconnected during broadcast", extra={
                    "connection_id": connection_id,
                    "room": room
                })
                disconnected_connections.append(connection_id)
            except Exception as e:
                logger.error(f"Failed to send message to connection", extra={
                    "connection_id": connection_id,
                    "room": room,
                    "error": str(e)
                })
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)
        
        logger.info(f"Broadcasted to room", extra={
            "room": room,
            "total_recipients": len(room_connections),
            "successful_sends": successful_sends,
            "disconnected": len(disconnected_connections),
            "message_type": message.get("type")
        })
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific connection with error handling."""
        if connection_id not in self.active_connections:
            logger.debug(f"Cannot send personal message: connection {connection_id} not found")
            return
        
        try:
            await self.active_connections[connection_id].send_text(json.dumps(message))
        except WebSocketDisconnect:
            logger.debug(f"WebSocket disconnected during personal message", extra={
                "connection_id": connection_id
            })
            self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Failed to send personal message", extra={
                "connection_id": connection_id,
                "error": str(e)
            })
            self.disconnect(connection_id)
    
    async def broadcast_activity(self, activity_data: Dict[str, Any]):
        """Broadcast activity to the activity_feed room."""
        message = {
            "type": "activity_update",
            "data": activity_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_room(message, "activity_feed")
    
    async def broadcast_proposal_update(self, proposal_id: str, update_type: str, data: Dict[str, Any]):
        """Broadcast proposal updates to the proposal room."""
        room = f"proposal:{proposal_id}"
        message = {
            "type": f"proposal_{update_type}",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_room(message, room)
    
    async def broadcast_vote_update(self, proposal_id: str, vote_data: Dict[str, Any]):
        """Broadcast vote updates."""
        # Broadcast to proposal room
        await self.broadcast_proposal_update(proposal_id, "vote", vote_data)
        
        # Also broadcast to activity feed
        await self.broadcast_activity({
            "type": "vote",
            "proposal_id": proposal_id,
            "data": vote_data
        })
    
    async def broadcast_comment_update(self, proposal_id: str, comment_data: Dict[str, Any], action: str = "created"):
        """Broadcast comment updates."""
        # Broadcast to proposal room
        await self.broadcast_proposal_update(proposal_id, f"comment_{action}", comment_data)
    
    async def broadcast_proposal_created(self, proposal_data: Dict[str, Any]):
        """Broadcast new proposal to activity feed."""
        await self.broadcast_activity({
            "type": "proposal",
            "data": proposal_data
        })
    
    async def broadcast_delegation_update(self, delegation_data: Dict[str, Any]):
        """Broadcast delegation updates."""
        await self.broadcast_activity({
            "type": "delegation",
            "data": delegation_data
        })
    
    async def start_heartbeat(self):
        """Start heartbeat to keep connections alive."""
        logger.info("Starting WebSocket heartbeat")
        
        while True:
            try:
                # Send ping to all connections
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                disconnected_connections = []
                
                # Create a copy to avoid modification during iteration
                active_connections = list(self.active_connections.items())
                
                for connection_id, websocket in active_connections:
                    try:
                        await websocket.send_text(json.dumps(ping_message))
                    except WebSocketDisconnect:
                        logger.debug(f"Connection lost during heartbeat", extra={
                            "connection_id": connection_id
                        })
                        disconnected_connections.append(connection_id)
                    except Exception as e:
                        logger.warning(f"Connection lost during heartbeat", extra={
                            "connection_id": connection_id,
                            "error": str(e)
                        })
                        disconnected_connections.append(connection_id)
                
                # Clean up disconnected connections
                for connection_id in disconnected_connections:
                    self.disconnect(connection_id)
                
                # Log heartbeat stats
                if self.active_connections:
                    logger.debug(f"Heartbeat sent to {len(self.active_connections)} connections")
                
                # Wait 30 seconds before next heartbeat
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("WebSocket heartbeat cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat error", extra={"error": str(e)})
                # Wait a bit longer on error to avoid spam
                await asyncio.sleep(60)
    
    def is_healthy(self) -> bool:
        """Check if the WebSocket manager is healthy."""
        try:
            # Check if heartbeat task is running
            if not self.heartbeat_task or self.heartbeat_task.done():
                return False
            
            # Check for any obvious issues
            return True
        except Exception as e:
            logger.error(f"Health check failed", extra={"error": str(e)})
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "rooms": {room: len(connections) for room, connections in self.rooms.items()},
            "total_rooms": len(self.rooms)
        }
    
    async def shutdown(self):
        """Gracefully shutdown the WebSocket manager."""
        logger.info("Shutting down WebSocket manager")
        
        # Disconnect all connections
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.leave_all_rooms(connection_id)
            self.disconnect(connection_id)
        
        # Cancel heartbeat task
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"WebSocket manager shutdown complete", extra={
            "connections_cleaned": len(connection_ids)
        })


# Global connection manager instance
manager = ConnectionManager()
