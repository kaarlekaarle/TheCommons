"""Tests for comment reactions functionality."""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.comment import Comment
from backend.models.comment_reaction import CommentReaction, ReactionType
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.option import Option


@pytest.fixture
async def sample_poll(db_session: AsyncSession) -> Poll:
    """Create a sample poll for testing."""
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        description="Test poll for reactions",
        created_by=uuid4(),
        is_active=True
    )
    db_session.add(poll)
    await db_session.commit()
    return poll


@pytest.fixture
async def sample_comment(db_session: AsyncSession, sample_poll: Poll, test_user: User) -> Comment:
    """Create a sample comment for testing."""
    comment = Comment(
        id=uuid4(),
        poll_id=sample_poll.id,
        user_id=test_user.id,
        body="Test comment for reactions"
    )
    db_session.add(comment)
    await db_session.commit()
    return comment


@pytest.fixture
async def another_user(db_session: AsyncSession) -> User:
    """Create another user for testing."""
    user = User(
        id=uuid4(),
        username="another_user",
        email="another@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    return user


class TestCommentReactions:
    """Test comment reactions functionality."""

    async def test_set_reaction_none_to_up(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test setting reaction from none to up."""
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 1
        assert data["down_count"] == 0
        assert data["my_reaction"] == "up"

    async def test_set_reaction_none_to_down(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test setting reaction from none to down."""
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "down"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 0
        assert data["down_count"] == 1
        assert data["my_reaction"] == "down"

    async def test_toggle_reaction_up_to_off(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test toggling reaction from up to off."""
        # First set up reaction
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        # Then toggle off
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 0
        assert data["down_count"] == 0
        assert data["my_reaction"] is None

    async def test_change_reaction_up_to_down(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test changing reaction from up to down."""
        # First set up reaction
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        # Then change to down
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "down"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 0
        assert data["down_count"] == 1
        assert data["my_reaction"] == "down"

    async def test_change_reaction_down_to_up(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test changing reaction from down to up."""
        # First set down reaction
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "down"},
            headers=auth_headers
        )
        
        # Then change to up
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 1
        assert data["down_count"] == 0
        assert data["my_reaction"] == "up"

    async def test_clear_reaction(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test clearing a reaction."""
        # First set a reaction
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        # Then clear it
        response = client.delete(
            f"/api/comments/{sample_comment.id}/reactions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 0
        assert data["down_count"] == 0
        assert data["my_reaction"] is None

    async def test_multiple_users_reactions(self, client: TestClient, test_user: User, another_user: User, sample_comment: Comment, auth_headers: dict):
        """Test reactions from multiple users."""
        # First user sets up reaction
        response1 = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Second user sets down reaction
        # Create auth headers for second user
        another_user_token = create_test_token(another_user.id)
        another_user_headers = {"Authorization": f"Bearer {another_user_token}"}
        
        response2 = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "down"},
            headers=another_user_headers
        )
        assert response2.status_code == 200
        
        # Check final counts
        response3 = client.get(f"/api/comments/{sample_comment.id}/reactions/summary")
        assert response3.status_code == 200
        data = response3.json()
        assert data["up_count"] == 1
        assert data["down_count"] == 1

    async def test_reaction_summary_public_access(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test that reaction summary is publicly accessible."""
        # Set a reaction first
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        # Get summary without auth
        response = client.get(f"/api/comments/{sample_comment.id}/reactions/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["up_count"] == 1
        assert data["down_count"] == 0

    async def test_reaction_auth_required(self, client: TestClient, sample_comment: Comment):
        """Test that setting reactions requires authentication."""
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"}
        )
        assert response.status_code == 401

    async def test_reaction_comment_not_found(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test reaction on non-existent comment."""
        fake_comment_id = str(uuid4())
        response = client.post(
            f"/api/comments/{fake_comment_id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_reaction_invalid_type(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test reaction with invalid type."""
        response = client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "invalid"},
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_comments_include_reaction_data(self, client: TestClient, test_user: User, sample_comment: Comment, auth_headers: dict):
        """Test that comment listing includes reaction data."""
        # Set a reaction first
        client.post(
            f"/api/comments/{sample_comment.id}/reactions",
            json={"type": "up"},
            headers=auth_headers
        )
        
        # Get comments list
        response = client.get(f"/api/polls/{sample_comment.poll_id}/comments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["comments"]) == 1
        comment = data["comments"][0]
        assert "up_count" in comment
        assert "down_count" in comment
        assert "my_reaction" in comment
        assert comment["up_count"] == 1
        assert comment["down_count"] == 0
        assert comment["my_reaction"] == "up"

    async def test_reaction_unique_constraint(self, db_session: AsyncSession, test_user: User, sample_comment: Comment):
        """Test that only one reaction per user per comment is allowed."""
        # Create first reaction
        reaction1 = CommentReaction(
            comment_id=sample_comment.id,
            user_id=test_user.id,
            type=ReactionType.UP
        )
        db_session.add(reaction1)
        await db_session.commit()
        
        # Try to create second reaction (should fail)
        reaction2 = CommentReaction(
            comment_id=sample_comment.id,
            user_id=test_user.id,
            type=ReactionType.DOWN
        )
        db_session.add(reaction2)
        
        with pytest.raises(Exception):  # Should raise unique constraint violation
            await db_session.commit()


def create_test_token(user_id: str) -> str:
    """Helper function to create test JWT token."""
    from backend.core.auth import create_access_token
    return create_access_token({"sub": str(user_id)})
