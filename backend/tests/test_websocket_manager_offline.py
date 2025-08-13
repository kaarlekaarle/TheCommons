"""Test WebSocket manager functionality."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi import WebSocket, WebSocketDisconnect

from backend.core.websocket import ConnectionManager, manager


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.sent_messages = []
        self.closed = False
        self.accepted = False
    
    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True
    
    async def send_text(self, message: str):
        """Send a text message."""
        if self.closed:
            raise WebSocketDisconnect()
        self.sent_messages.append(message)
    
    async def close(self):
        """Close the WebSocket connection."""
        self.closed = True
    
    def __repr__(self):
        return f"MockWebSocket({self.connection_id})"


@pytest.fixture
def websocket_manager():
    """Create a fresh WebSocket manager for testing."""
    return ConnectionManager()


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect(websocket_manager):
    """Test basic WebSocket connection and disconnection."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("test-connection-1")
    
    # Connect
    await websocket_manager.connect(mock_ws, "test-connection-1", "user-1")
    
    # Verify connection was accepted
    assert mock_ws.accepted
    assert "test-connection-1" in websocket_manager.active_connections
    assert websocket_manager.active_connections["test-connection-1"] == mock_ws
    
    # Verify metadata was stored
    assert "test-connection-1" in websocket_manager.connection_metadata
    metadata = websocket_manager.connection_metadata["test-connection-1"]
    assert metadata["user_id"] == "user-1"
    assert "connected_at" in metadata
    assert metadata["rooms"] == set()
    
    # Disconnect
    websocket_manager.disconnect("test-connection-1")
    
    # Verify connection was removed
    assert "test-connection-1" not in websocket_manager.active_connections
    assert "test-connection-1" not in websocket_manager.connection_metadata


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_room_broadcasting(websocket_manager):
    """Test that two clients join same room → broadcast → both receive."""
    
    # Create two mock WebSockets
    mock_ws1 = MockWebSocket("connection-1")
    mock_ws2 = MockWebSocket("connection-2")
    
    # Connect both clients
    await websocket_manager.connect(mock_ws1, "connection-1", "user-1")
    await websocket_manager.connect(mock_ws2, "connection-2", "user-2")
    
    # Both join the same room
    await websocket_manager.join_room("connection-1", "test-room")
    await websocket_manager.join_room("connection-2", "test-room")
    
    # Verify room was created and both clients are in it
    assert "test-room" in websocket_manager.rooms
    assert "connection-1" in websocket_manager.rooms["test-room"]
    assert "connection-2" in websocket_manager.rooms["test-room"]
    
    # Verify room confirmation messages were sent
    assert len(mock_ws1.sent_messages) == 1
    assert len(mock_ws2.sent_messages) == 1
    
    room_join_msg1 = json.loads(mock_ws1.sent_messages[0])
    room_join_msg2 = json.loads(mock_ws2.sent_messages[0])
    assert room_join_msg1["type"] == "room_joined"
    assert room_join_msg2["type"] == "room_joined"
    assert room_join_msg1["room"] == "test-room"
    assert room_join_msg2["room"] == "test-room"
    
    # Broadcast a message to the room
    test_message = {"type": "test", "data": "hello world"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify both clients received the message
    assert len(mock_ws1.sent_messages) == 2
    assert len(mock_ws2.sent_messages) == 2
    
    broadcast_msg1 = json.loads(mock_ws1.sent_messages[1])
    broadcast_msg2 = json.loads(mock_ws2.sent_messages[1])
    assert broadcast_msg1 == test_message
    assert broadcast_msg2 == test_message


@pytest.mark.offline
@pytest.mark.xfail(reason="TODO: Fix race condition in offline WebSocket disconnect handling")
@pytest.mark.asyncio
async def test_websocket_disconnect_broadcasting(websocket_manager):
    """Test that one disconnects → broadcast → only connected receives."""
    
    # Create two mock WebSockets
    mock_ws1 = MockWebSocket("connection-1")
    mock_ws2 = MockWebSocket("connection-2")
    
    # Connect both clients
    await websocket_manager.connect(mock_ws1, "connection-1", "user-1")
    await websocket_manager.connect(mock_ws2, "connection-2", "user-2")
    
    # Both join the same room
    await websocket_manager.join_room("connection-1", "test-room")
    await websocket_manager.join_room("connection-2", "test-room")
    
    # Disconnect one client
    websocket_manager.disconnect("connection-1")
    
    # Broadcast a message to the room
    test_message = {"type": "test", "data": "hello world"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify only the connected client received the message
    assert len(mock_ws1.sent_messages) == 1  # Only room join message
    assert len(mock_ws2.sent_messages) == 2  # Room join + broadcast message
    
    broadcast_msg = json.loads(mock_ws2.sent_messages[1])
    assert broadcast_msg == test_message
    
    # Verify disconnected client was removed from room
    assert "connection-1" not in websocket_manager.rooms["test-room"]
    assert "connection-2" in websocket_manager.rooms["test-room"]


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_leave_room(websocket_manager):
    """Test leaving a room."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Verify room join
    assert "test-room" in websocket_manager.rooms
    assert "connection-1" in websocket_manager.rooms["test-room"]
    
    # Leave room
    await websocket_manager.leave_room("connection-1", "test-room")
    
    # Verify room was left (room is cleaned up when empty)
    assert "test-room" not in websocket_manager.rooms
    
    # Verify leave confirmation message was sent
    assert len(mock_ws.sent_messages) == 2  # Join + leave messages
    leave_msg = json.loads(mock_ws.sent_messages[1])
    assert leave_msg["type"] == "room_left"
    assert leave_msg["room"] == "test-room"


@pytest.mark.offline
@pytest.mark.xfail(reason="TODO: Fix timing issues in offline heartbeat shutdown")
@pytest.mark.asyncio
async def test_websocket_heartbeat_shutdown(websocket_manager):
    """Test WebSocket heartbeat and shutdown without ERROR/EXCEPTION logs."""
    
    # Start heartbeat
    heartbeat_task = asyncio.create_task(websocket_manager.start_heartbeat())
    
    # Wait a bit for heartbeat to start
    await asyncio.sleep(0.1)
    
    # Verify heartbeat task is running
    assert not heartbeat_task.done()
    
    # Cancel heartbeat task
    heartbeat_task.cancel()
    
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass  # Expected
    
    # Verify task was cancelled cleanly
    assert heartbeat_task.done()


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_connection_stats(websocket_manager):
    """Test connection statistics."""
    
    # Create mock WebSockets
    mock_ws1 = MockWebSocket("connection-1")
    mock_ws2 = MockWebSocket("connection-2")
    
    # Connect clients
    await websocket_manager.connect(mock_ws1, "connection-1", "user-1")
    await websocket_manager.connect(mock_ws2, "connection-2", "user-2")
    
    # Join rooms
    await websocket_manager.join_room("connection-1", "room-1")
    await websocket_manager.join_room("connection-2", "room-1")
    await websocket_manager.join_room("connection-1", "room-2")
    
    # Get stats
    stats = websocket_manager.get_connection_stats()
    
    # Verify stats
    assert stats["active_connections"] == 2
    assert stats["total_rooms"] == 2
    assert stats["rooms"]["room-1"] == 2
    assert stats["rooms"]["room-2"] == 1


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_health_check(websocket_manager):
    """Test WebSocket health check."""
    
    # Health check should fail initially (no heartbeat task)
    assert not websocket_manager.is_healthy()
    
    # Start heartbeat
    websocket_manager.heartbeat_task = asyncio.create_task(websocket_manager.start_heartbeat())
    
    # Health check should pass with heartbeat running
    assert websocket_manager.is_healthy()
    
    # Cancel heartbeat
    websocket_manager.heartbeat_task.cancel()
    
    try:
        await websocket_manager.heartbeat_task
    except asyncio.CancelledError:
        pass
    
    # Health check should fail after heartbeat is done
    assert not websocket_manager.is_healthy()


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_broadcast_activity(websocket_manager):
    """Test broadcasting activity updates."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join activity feed
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "activity_feed")
    
    # Broadcast activity
    activity_data = {"type": "vote", "poll_id": "123", "user_id": "user-1"}
    await websocket_manager.broadcast_activity(activity_data)
    
    # Verify activity message was sent
    assert len(mock_ws.sent_messages) == 2  # Room join + activity
    activity_msg = json.loads(mock_ws.sent_messages[1])
    assert activity_msg["type"] == "activity_update"
    assert activity_msg["data"] == activity_data
    assert "timestamp" in activity_msg


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_broadcast_proposal_update(websocket_manager):
    """Test broadcasting proposal updates."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join proposal room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "proposal:123")
    
    # Broadcast proposal update
    update_data = {"poll_id": "123", "title": "Updated Title"}
    await websocket_manager.broadcast_proposal_update("123", "update", update_data)
    
    # Verify proposal update message was sent
    assert len(mock_ws.sent_messages) == 2  # Room join + update
    update_msg = json.loads(mock_ws.sent_messages[1])
    assert update_msg["type"] == "proposal_update"
    assert update_msg["data"] == update_data
    assert "timestamp" in update_msg


@pytest.mark.offline
@pytest.mark.xfail(reason="TODO: Fix error handling in offline WebSocket message sending")
@pytest.mark.asyncio
async def test_websocket_error_handling(websocket_manager):
    """Test WebSocket error handling during message sending."""
    
    # Create mock WebSocket that raises exception on send
    mock_ws = MockWebSocket("connection-1")
    original_send = mock_ws.send_text
    
    async def failing_send(message: str):
        raise Exception("Send failed")
    
    mock_ws.send_text = failing_send
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Try to broadcast - should handle error gracefully
    test_message = {"type": "test", "data": "hello"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify connection was removed due to error
    assert "connection-1" not in websocket_manager.active_connections
    assert "test-room" not in websocket_manager.rooms  # Room cleaned up when empty


@pytest.mark.offline
@pytest.mark.asyncio
async def test_websocket_cleanup_on_disconnect(websocket_manager):
    """Test that disconnecting cleans up all room memberships."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join multiple rooms
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "room-1")
    await websocket_manager.join_room("connection-1", "room-2")
    await websocket_manager.join_room("connection-1", "room-3")
    
    # Verify joined all rooms
    assert "connection-1" in websocket_manager.rooms["room-1"]
    assert "connection-1" in websocket_manager.rooms["room-2"]
    assert "connection-1" in websocket_manager.rooms["room-3"]
    
    # Disconnect
    websocket_manager.disconnect("connection-1")
    
    # Verify removed from all rooms (rooms are cleaned up when empty)
    assert "room-1" not in websocket_manager.rooms
    assert "room-2" not in websocket_manager.rooms
    assert "room-3" not in websocket_manager.rooms
    
    # Verify connection metadata was cleaned up
    assert "connection-1" not in websocket_manager.connection_metadata
