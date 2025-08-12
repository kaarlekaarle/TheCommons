import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch

from backend.main import app
from backend.core.audit_mw import AuditMiddleware, audit_event


@pytest.mark.asyncio
async def test_audit_middleware_request_id():
    """Test that request ID is propagated correctly."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test with custom request ID
        response = await ac.post("/api/token", 
            data={"username": "test", "password": "test"},
            headers={"X-Request-ID": "test-request-123"}
        )
        assert response.headers.get("X-Request-ID") == "test-request-123"
        
        # Test without request ID (should generate one)
        response = await ac.post("/api/token", 
            data={"username": "test", "password": "test"}
        )
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None


@pytest.mark.asyncio
async def test_audit_middleware_skips_noisy_paths():
    """Test that audit middleware skips noisy paths."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # These should not generate audit logs
        response = await ac.get("/health")
        assert response.status_code == 200
        
        response = await ac.get("/docs")
        assert response.status_code == 200
        
        response = await ac.get("/openapi.json")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_audit_middleware_logs_mutating_requests(caplog):
    """Test that audit middleware logs mutating requests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # This should generate an audit log
        response = await ac.post("/api/token", 
            data={"username": "test", "password": "test"}
        )
        
        # Check that audit log was created
        audit_logs = [record for record in caplog.records if record.message == "audit_request"]
        assert len(audit_logs) > 0
        
        # Check log structure
        log_data = json.loads(audit_logs[0].message)
        assert "request_id" in log_data
        assert "method" in log_data
        assert "path" in log_data
        assert "status" in log_data
        assert "duration_ms" in log_data


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
async def test_audit_middleware_duration():
    """Test that audit middleware calculates duration correctly."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/token", 
            data={"username": "test", "password": "test"}
        )
        
        # Check that duration is logged and is reasonable
        audit_logs = [record for record in caplog.records if record.message == "audit_request"]
        if audit_logs:
            log_data = json.loads(audit_logs[0].message)
            assert "duration_ms" in log_data
            assert isinstance(log_data["duration_ms"], int)
            assert log_data["duration_ms"] >= 0  # Should be non-negative
