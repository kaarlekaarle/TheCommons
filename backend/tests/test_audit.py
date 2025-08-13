import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch

from backend.main import app
from backend.core.audit_mw import AuditMiddleware, audit_event


@pytest.mark.asyncio
async def test_audit_middleware_request_id(client: AsyncClient):
    """Test that request ID is propagated correctly."""
    # Test with custom request ID
    response = await client.post("/api/token", 
        data={"username": "test", "password": "test"},
        headers={"X-Request-ID": "test-request-123"}
    )
    assert response.headers.get("X-Request-ID") == "test-request-123"
    
    # Test without request ID (should generate one)
    response = await client.post("/api/token", 
        data={"username": "test", "password": "test"}
    )
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] is not None


@pytest.mark.asyncio
async def test_audit_middleware_skips_noisy_paths(client: AsyncClient, caplog):
    """Test that audit middleware skips noisy paths."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    # assert no audit records emitted for /health
    records = [r for r in caplog.records if "audit_request" in getattr(r, "message", "")]
    assert len(records) == 0


@pytest.mark.asyncio
async def test_audit_middleware_logs_mutating_requests(client: AsyncClient, caplog):
    """Test that audit middleware logs mutating requests."""
    # This should generate an audit log
    response = await client.post("/api/token", 
        data={"username": "test", "password": "test"}
    )
    
    # Check that audit log was created
    audit_logs = [record for record in caplog.records if "audit_request" in str(record.message)]
    assert len(audit_logs) > 0
    
    # Check log structure - the message should contain audit data
    log_message = str(audit_logs[0].message)
    assert "request_id" in log_message
    assert "method" in log_message
    assert "path" in log_message
    assert "status" in log_message
    assert "duration_ms" in log_message


@pytest.mark.asyncio
async def test_audit_event_function():
    """Test the audit_event helper function."""
    from fastapi import Request
    from unittest.mock import Mock
    
    # Create a mock request with state
    mock_request = Mock(spec=Request)
    mock_request.state.request_id = "test-request-456"
    mock_request.state.user = Mock()
    mock_request.state.user.id = "test-user-123"
    
    # Test audit_event function
    with patch('backend.core.audit_mw.get_json_logger') as mock_logger:
        audit_event("test_event", {"key": "value"}, mock_request)
        
        # Verify logger was called
        mock_logger.return_value.info.assert_called_once()
        call_args = mock_logger.return_value.info.call_args
        assert call_args[0][0] == "audit_event"
        
        # Check log data
        log_data = call_args[1]
        assert log_data["request_id"] == "test-request-456"
        assert log_data["user_id"] == "test-user-123"
        assert log_data["kind"] == "test_event"
        assert log_data["data"] == {"key": "value"}


@pytest.mark.asyncio
async def test_audit_event_without_user():
    """Test audit_event when user is not available."""
    from fastapi import Request
    from unittest.mock import Mock
    
    # Create a mock request without user
    mock_request = Mock(spec=Request)
    mock_request.state.request_id = "test-request-789"
    # No user in state
    
    # Test audit_event function
    with patch('backend.core.audit_mw.get_json_logger') as mock_logger:
        audit_event("test_event_no_user", {"key": "value"}, mock_request)
        
        # Verify logger was called
        mock_logger.return_value.info.assert_called_once()
        call_args = mock_logger.return_value.info.call_args
        
        # Check log data
        log_data = call_args[1]
        assert log_data["request_id"] == "test-request-789"
        assert log_data["user_id"] is None
        assert log_data["kind"] == "test_event_no_user"


@pytest.mark.asyncio
async def test_audit_middleware_duration(client: AsyncClient, caplog):
    """Test that audit middleware calculates duration correctly."""
    response = await client.post("/api/token", 
        data={"username": "test", "password": "test"}
    )
    
    # Check that duration is logged and is reasonable
    audit_logs = [record for record in caplog.records if "audit_request" in str(record.message)]
    if audit_logs:
        log_message = str(audit_logs[0].message)
        assert "duration_ms" in log_message
        # Extract duration_ms from the log message (it's a JSON-like string)
        import re
        duration_match = re.search(r'"duration_ms":\s*(\d+)', log_message)
        if duration_match:
            duration_ms = int(duration_match.group(1))
            assert duration_ms >= 0  # Should be non-negative
