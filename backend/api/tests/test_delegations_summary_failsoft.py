from unittest.mock import MagicMock, patch

"""Test that /api/delegations/summary returns fail-soft payload on exceptions."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.delegations import router


@pytest.fixture
def client():
    """Create a test client for the delegations router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestDelegationsSummaryFailSoft:
    """Test that /api/delegations/summary returns fail-soft payload on exceptions."""

    @patch("backend.api.delegations.SafeDelegationSummaryService")
    def test_summary_endpoint_fail_soft_on_exception(self, mock_service_class, client):
        """Test that the endpoint returns 200 with fail-soft payload when service throws exception."""
        # Mock the service to raise an exception
        mock_service = MagicMock()
        mock_service.get_safe_summary.side_effect = Exception("Internal service error")
        mock_service_class.return_value = mock_service

        # Make request to the endpoint
        response = client.get("/api/delegations/summary")

        # Assert we get HTTP 200 (not 500)
        assert response.status_code == 200

        # Parse the response
        data = response.json()

        # Assert fail-soft payload structure
        assert data["ok"] is False
        assert data["counts"]["mine"] == 0
        assert data["counts"]["inbound"] == 0
        assert "meta" in data
        assert "errors" in data["meta"]
        assert "generated_at" in data["meta"]
        assert "trace_id" in data["meta"]

        # Assert error message contains the exception
        assert len(data["meta"]["errors"]) > 0
        assert any(
            "Internal service error" in error for error in data["meta"]["errors"]
        )

    @patch("backend.api.delegations.SafeDelegationSummaryService")
    def test_summary_endpoint_fail_soft_on_database_error(
        self, mock_service_class, client
    ):
        """Test that the endpoint returns 200 with fail-soft payload on database errors."""
        # Mock the service to raise a database-related exception
        mock_service = MagicMock()
        mock_service.get_safe_summary.side_effect = Exception(
            "Database connection failed"
        )
        mock_service_class.return_value = mock_service

        # Make request to the endpoint
        response = client.get("/api/delegations/summary")

        # Assert we get HTTP 200 (not 500)
        assert response.status_code == 200

        # Parse the response
        data = response.json()

        # Assert fail-soft payload structure
        assert data["ok"] is False
        assert data["counts"]["mine"] == 0
        assert data["counts"]["inbound"] == 0
        assert "meta" in data
        assert "errors" in data["meta"]

        # Assert error message contains the database error
        assert len(data["meta"]["errors"]) > 0
        assert any(
            "Database connection failed" in error for error in data["meta"]["errors"]
        )

    @patch("backend.api.delegations.SafeDelegationSummaryService")
    def test_summary_endpoint_fail_soft_on_validation_error(
        self, mock_service_class, client
    ):
        """Test that the endpoint returns 200 with fail-soft payload on validation errors."""
        # Mock the service to raise a validation-related exception
        mock_service = MagicMock()
        mock_service.get_safe_summary.side_effect = ValueError("Invalid user data")
        mock_service_class.return_value = mock_service

        # Make request to the endpoint
        response = client.get("/api/delegations/summary")

        # Assert we get HTTP 200 (not 500)
        assert response.status_code == 200

        # Parse the response
        data = response.json()

        # Assert fail-soft payload structure
        assert data["ok"] is False
        assert data["counts"]["mine"] == 0
        assert data["counts"]["inbound"] == 0
        assert "meta" in data
        assert "errors" in data["meta"]

        # Assert error message contains the validation error
        assert len(data["meta"]["errors"]) > 0
        assert any("Invalid user data" in error for error in data["meta"]["errors"])
