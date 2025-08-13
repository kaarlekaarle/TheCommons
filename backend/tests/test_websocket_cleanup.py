"""Test WebSocket room cleanup functionality."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi import WebSocket, WebSocketDisconnect

from backend.core.websocket import ConnectionManager


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, connection_id: str, fail_on_send=False):
        self.connection_id = connection_id
        self.sent_messages = []
        self.closed = False
        self.accepted = False
        self.fail_on_send = fail_on_send
    
    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True
    
    async def send_text(self, message: str):
        """Send a text message."""
        if self.closed or self.fail_on_send:
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


@pytest.mark.asyncio
async def test_connect_disconnect_cleanup_rooms_empty(websocket_manager):
    """Test: connect -> subscribe -> disconnect -> rooms are empty."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("test-connection-1")
    
    # Connect
    await websocket_manager.connect(mock_ws, "test-connection-1", "user-1")
    
    # Join multiple rooms
    await websocket_manager.join_room("test-connection-1", "room-1")
    await websocket_manager.join_room("test-connection-1", "room-2")
    await websocket_manager.join_room("test-connection-1", "room-3")
    
    # Verify joined all rooms
    assert "test-connection-1" in websocket_manager.rooms["room-1"]
    assert "test-connection-1" in websocket_manager.rooms["room-2"]
    assert "test-connection-1" in websocket_manager.rooms["room-3"]
    
    # Disconnect
    websocket_manager.disconnect("test-connection-1")
    
    # Verify removed from all rooms (rooms are cleaned up when empty)
    assert "room-1" not in websocket_manager.rooms
    assert "room-2" not in websocket_manager.rooms
    assert "room-3" not in websocket_manager.rooms
    
    # Verify connection metadata was cleaned up
    assert "test-connection-1" not in websocket_manager.connection_metadata
    assert "test-connection-1" not in websocket_manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_after_disconnect_no_exception(websocket_manager):
    """Test: broadcast after disconnect does not throw."""
    
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
    
    # Broadcast a message to the room - should not throw
    test_message = {"type": "test", "data": "hello world"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify only the connected client received the message
    assert len(mock_ws1.sent_messages) == 1  # Only room join message
    assert len(mock_ws2.sent_messages) == 2  # Room join + broadcast message
    
    broadcast_msg = json.loads(mock_ws2.sent_messages[1])
    assert broadcast_msg == test_message


@pytest.mark.asyncio
async def test_leave_room_idempotent(websocket_manager):
    """Test that leave_room is idempotent."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Verify room join
    assert "connection-1" in websocket_manager.rooms["test-room"]
    
    # Leave room first time
    await websocket_manager.leave_room("connection-1", "test-room")
    
    # Verify room was left (room is cleaned up when empty)
    assert "test-room" not in websocket_manager.rooms
    
    # Leave room second time - should not throw
    await websocket_manager.leave_room("connection-1", "test-room")
    
    # Verify room is still empty
    assert "test-room" not in websocket_manager.rooms


@pytest.mark.asyncio
async def test_leave_all_rooms_idempotent(websocket_manager):
    """Test that leave_all_rooms is idempotent."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join multiple rooms
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "room-1")
    await websocket_manager.join_room("connection-1", "room-2")
    
    # Verify joined rooms
    assert "connection-1" in websocket_manager.rooms["room-1"]
    assert "connection-1" in websocket_manager.rooms["room-2"]
    
    # Leave all rooms first time
    await websocket_manager.leave_all_rooms("connection-1")
    
    # Verify left all rooms (rooms are cleaned up when empty)
    assert "room-1" not in websocket_manager.rooms
    assert "room-2" not in websocket_manager.rooms
    
    # Leave all rooms second time - should not throw
    await websocket_manager.leave_all_rooms("connection-1")
    
    # Verify rooms are still empty
    assert "room-1" not in websocket_manager.rooms
    assert "room-2" not in websocket_manager.rooms


@pytest.mark.asyncio
async def test_disconnect_idempotent(websocket_manager):
    """Test that disconnect is idempotent."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Disconnect first time
    websocket_manager.disconnect("connection-1")
    
    # Verify disconnected
    assert "connection-1" not in websocket_manager.active_connections
    assert "test-room" not in websocket_manager.rooms  # Room cleaned up when empty
    
    # Disconnect second time - should not throw
    websocket_manager.disconnect("connection-1")
    
    # Verify still disconnected
    assert "connection-1" not in websocket_manager.active_connections
    assert "test-room" not in websocket_manager.rooms


@pytest.mark.asyncio
async def test_broadcast_with_stale_connections(websocket_manager):
    """Test broadcast handles stale connections gracefully."""
    
    # Create mock WebSocket that will fail on send
    mock_ws = MockWebSocket("connection-1", fail_on_send=True)
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Broadcast message - should handle failure gracefully
    test_message = {"type": "test", "data": "hello"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify connection was removed due to failure
    assert "connection-1" not in websocket_manager.active_connections
    assert "test-room" not in websocket_manager.rooms  # Room cleaned up when empty


@pytest.mark.asyncio
async def test_broadcast_with_mixed_connections(websocket_manager):
    """Test broadcast with mix of working and failing connections."""
    
    # Create two mock WebSockets - one working, one failing
    mock_ws1 = MockWebSocket("connection-1", fail_on_send=True)
    mock_ws2 = MockWebSocket("connection-2", fail_on_send=False)
    
    # Connect both clients
    await websocket_manager.connect(mock_ws1, "connection-1", "user-1")
    await websocket_manager.connect(mock_ws2, "connection-2", "user-2")
    
    # Both join the same room
    await websocket_manager.join_room("connection-1", "test-room")
    await websocket_manager.join_room("connection-2", "test-room")
    
    # Broadcast message
    test_message = {"type": "test", "data": "hello"}
    await websocket_manager.broadcast_to_room(test_message, "test-room")
    
    # Verify failing connection was removed
    assert "connection-1" not in websocket_manager.active_connections
    assert "connection-1" not in websocket_manager.rooms["test-room"]
    
    # Verify working connection received message
    assert len(mock_ws2.sent_messages) == 2  # Room join + broadcast
    broadcast_msg = json.loads(mock_ws2.sent_messages[1])
    assert broadcast_msg == test_message


@pytest.mark.asyncio
async def test_heartbeat_cleanup_stale_connections(websocket_manager):
    """Test heartbeat cleanup of stale connections."""
    
    # Create mock WebSocket that will fail on send
    mock_ws = MockWebSocket("connection-1", fail_on_send=True)
    
    # Connect
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    
    # Start heartbeat
    heartbeat_task = asyncio.create_task(websocket_manager.start_heartbeat())
    
    # Wait a bit for heartbeat to run
    await asyncio.sleep(0.1)
    
    # Verify connection was removed by heartbeat
    assert "connection-1" not in websocket_manager.active_connections
    
    # Cancel heartbeat
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_shutdown_cleanup_all_connections(websocket_manager):
    """Test shutdown cleans up all connections."""
    
    # Create multiple mock WebSockets
    mock_ws1 = MockWebSocket("connection-1")
    mock_ws2 = MockWebSocket("connection-2")
    mock_ws3 = MockWebSocket("connection-3")
    
    # Connect all clients
    await websocket_manager.connect(mock_ws1, "connection-1", "user-1")
    await websocket_manager.connect(mock_ws2, "connection-2", "user-2")
    await websocket_manager.connect(mock_ws3, "connection-3", "user-3")
    
    # Join various rooms
    await websocket_manager.join_room("connection-1", "room-1")
    await websocket_manager.join_room("connection-2", "room-1")
    await websocket_manager.join_room("connection-2", "room-2")
    await websocket_manager.join_room("connection-3", "room-2")
    
    # Verify all connected
    assert len(websocket_manager.active_connections) == 3
    assert len(websocket_manager.rooms) == 2
    
    # Shutdown
    await websocket_manager.shutdown()
    
    # Verify all connections cleaned up
    assert len(websocket_manager.active_connections) == 0
    assert len(websocket_manager.rooms) == 0
    assert len(websocket_manager.connection_metadata) == 0


@pytest.mark.asyncio
async def test_join_room_nonexistent_connection(websocket_manager):
    """Test joining room with nonexistent connection."""
    
    # Try to join room with nonexistent connection
    await websocket_manager.join_room("nonexistent", "test-room")
    
    # Verify no room was created
    assert "test-room" not in websocket_manager.rooms


@pytest.mark.asyncio
async def test_send_personal_message_nonexistent_connection(websocket_manager):
    """Test sending personal message to nonexistent connection."""
    
    # Try to send personal message to nonexistent connection
    test_message = {"type": "test", "data": "hello"}
    await websocket_manager.send_personal_message(test_message, "nonexistent")
    
    # Should not throw and should not create any connections


@pytest.mark.asyncio
async def test_broadcast_to_nonexistent_room(websocket_manager):
    """Test broadcasting to nonexistent room."""
    
    # Try to broadcast to nonexistent room
    test_message = {"type": "test", "data": "hello"}
    await websocket_manager.broadcast_to_room(test_message, "nonexistent")
    
    # Should not throw


@pytest.mark.asyncio
async def test_connection_metadata_cleanup(websocket_manager):
    """Test that connection metadata is properly cleaned up."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Verify metadata exists
    assert "connection-1" in websocket_manager.connection_metadata
    metadata = websocket_manager.connection_metadata["connection-1"]
    assert metadata["user_id"] == "user-1"
    assert "test-room" in metadata["rooms"]
    
    # Disconnect
    websocket_manager.disconnect("connection-1")
    
    # Verify metadata cleaned up
    assert "connection-1" not in websocket_manager.connection_metadata


@pytest.mark.asyncio
async def test_empty_room_cleanup(websocket_manager):
    """Test that empty rooms are cleaned up."""
    
    # Create mock WebSocket
    mock_ws = MockWebSocket("connection-1")
    
    # Connect and join room
    await websocket_manager.connect(mock_ws, "connection-1", "user-1")
    await websocket_manager.join_room("connection-1", "test-room")
    
    # Verify room exists
    assert "test-room" in websocket_manager.rooms
    assert "connection-1" in websocket_manager.rooms["test-room"]
    
    # Leave room
    await websocket_manager.leave_room("connection-1", "test-room")
    
    # Verify room was cleaned up
    assert "test-room" not in websocket_manager.rooms
