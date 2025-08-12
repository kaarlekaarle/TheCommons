import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.poll import Poll
from backend.models.user import User
from backend.models.option import Option
from backend.models.vote import Vote
from backend.core.auth import create_access_token


@pytest.fixture
def test_poll(db_session: AsyncSession, test_user: User) -> Poll:
    """Create a test poll."""
    poll = Poll(
        id=uuid4(),
        title="Test Poll for Detail",
        description="A test poll for testing the detail endpoint",
        created_by=test_user.id,
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    return poll


@pytest.fixture
def test_options(db_session: AsyncSession, test_poll: Poll) -> list[Option]:
    """Create test options for the poll."""
    options = [
        Option(
            id=uuid4(),
            poll_id=test_poll.id,
            text="Yes",
        ),
        Option(
            id=uuid4(),
            poll_id=test_poll.id,
            text="No",
        ),
    ]
    for option in options:
        db_session.add(option)
    db_session.commit()
    for option in options:
        db_session.refresh(option)
    return options


@pytest.fixture
def test_vote(db_session: AsyncSession, test_user: User, test_poll: Poll, test_options: list[Option]) -> Vote:
    """Create a test vote."""
    vote = Vote(
        id=uuid4(),
        user_id=test_user.id,
        poll_id=test_poll.id,
        option_id=test_options[0].id,  # Vote for "Yes"
    )
    db_session.add(vote)
    db_session.commit()
    db_session.refresh(vote)
    return vote


@pytest.fixture
def another_user(db_session: AsyncSession) -> User:
    """Create another test user."""
    user = User(
        id=uuid4(),
        username="another_user",
        email="another@example.com",
        hashed_password="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestPollDetail:
    """Test cases for the poll detail endpoint."""

    async def test_get_poll_detail_authenticated_user_who_voted(
        self,
        client: TestClient,
        test_user: User,
        test_poll: Poll,
        test_vote: Vote,
    ):
        """Test GET /api/polls/{id} as authenticated user who voted."""
        # Create access token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request
        response = client.get(f"/api/polls/{test_poll.id}", headers=headers)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        # Check basic poll data
        assert data["id"] == str(test_poll.id)
        assert data["title"] == test_poll.title
        assert data["description"] == test_poll.description
        assert data["created_by"] == str(test_poll.created_by)
        
        # Check vote status
        assert data["your_vote_status"] is not None
        assert data["your_vote_status"]["status"] == "voted"
        assert data["your_vote_status"]["final_delegatee_id"] == str(test_user.id)
        assert len(data["your_vote_status"]["resolved_vote_path"]) >= 1
        assert str(test_user.id) in data["your_vote_status"]["resolved_vote_path"]

    async def test_get_poll_detail_authenticated_user_who_didnt_vote(
        self,
        client: TestClient,
        another_user: User,
        test_poll: Poll,
    ):
        """Test GET /api/polls/{id} as authenticated user who didn't vote."""
        # Create access token for another user
        token = create_access_token(data={"sub": str(another_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request
        response = client.get(f"/api/polls/{test_poll.id}", headers=headers)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        # Check basic poll data
        assert data["id"] == str(test_poll.id)
        assert data["title"] == test_poll.title
        assert data["description"] == test_poll.description
        assert data["created_by"] == str(test_poll.created_by)
        
        # Check vote status
        assert data["your_vote_status"] is not None
        assert data["your_vote_status"]["status"] == "none"
        assert data["your_vote_status"]["final_delegatee_id"] == str(another_user.id)
        assert len(data["your_vote_status"]["resolved_vote_path"]) >= 1
        assert str(another_user.id) in data["your_vote_status"]["resolved_vote_path"]

    async def test_get_poll_detail_unauthenticated(
        self,
        client: TestClient,
        test_poll: Poll,
    ):
        """Test GET /api/polls/{id} as unauthenticated user."""
        # Make request without authentication
        response = client.get(f"/api/polls/{test_poll.id}")
        
        # Should return 401 Unauthorized since authentication is required
        assert response.status_code == 401

    async def test_get_poll_detail_not_found(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test GET /api/polls/{id} with non-existent poll ID."""
        # Create access token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request with non-existent poll ID
        non_existent_id = uuid4()
        response = client.get(f"/api/polls/{non_existent_id}", headers=headers)
        
        # Should return 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_poll_detail_invalid_uuid(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test GET /api/polls/{id} with invalid UUID."""
        # Create access token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request with invalid UUID
        response = client.get("/api/polls/invalid-uuid", headers=headers)
        
        # Should return 422 Validation Error
        assert response.status_code == 422

    async def test_get_poll_detail_with_delegation(
        self,
        client: TestClient,
        test_user: User,
        another_user: User,
        test_poll: Poll,
        db_session: AsyncSession,
    ):
        """Test GET /api/polls/{id} when user has a delegation."""
        from backend.models.delegation import Delegation
        
        # Create a delegation from test_user to another_user
        delegation = Delegation(
            id=uuid4(),
            delegator_id=test_user.id,
            delegate_id=another_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        
        # Create access token for test_user
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request
        response = client.get(f"/api/polls/{test_poll.id}", headers=headers)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        # Check vote status shows delegation
        assert data["your_vote_status"] is not None
        assert data["your_vote_status"]["status"] == "delegated"
        assert data["your_vote_status"]["final_delegatee_id"] == str(another_user.id)
        assert len(data["your_vote_status"]["resolved_vote_path"]) >= 2
        assert str(test_user.id) in data["your_vote_status"]["resolved_vote_path"]
        assert str(another_user.id) in data["your_vote_status"]["resolved_vote_path"]

    async def test_get_poll_detail_schema_validation(
        self,
        client: TestClient,
        test_user: User,
        test_poll: Poll,
    ):
        """Test that the response schema matches the expected structure."""
        # Create access token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request
        response = client.get(f"/api/polls/{test_poll.id}", headers=headers)
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields are present
        required_fields = ["id", "title", "description", "created_by", "created_at", "your_vote_status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check vote status structure
        vote_status = data["your_vote_status"]
        assert "status" in vote_status
        assert "resolved_vote_path" in vote_status
        assert "final_delegatee_id" in vote_status
        assert isinstance(vote_status["resolved_vote_path"], list)
        assert isinstance(vote_status["status"], str)
        assert vote_status["final_delegatee_id"] is None or isinstance(vote_status["final_delegatee_id"], str)
