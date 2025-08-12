import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.comment import Comment
from backend.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_comment_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test successful comment creation."""
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test poll
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Login
    login_response = await async_client.post("/api/token", data={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # Create comment
    comment_data = {"body": "This is a test comment"}
    response = await async_client.post(
        f"/api/polls/{poll.id}/comments",
        json=comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "This is a test comment"
    assert data["user"]["username"] == "testuser"
    assert data["poll_id"] == str(poll.id)


@pytest.mark.asyncio
async def test_create_comment_validation(async_client: AsyncClient, db_session: AsyncSession):
    """Test comment validation."""
    
    # Create test user and poll
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Login
    login_response = await async_client.post("/api/token", data={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # Test empty comment
    response = await async_client.post(
        f"/api/polls/{poll.id}/comments",
        json={"body": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test whitespace-only comment
    response = await async_client.post(
        f"/api/polls/{poll.id}/comments",
        json={"body": "   "},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test comment too long
    long_comment = "x" * 2001
    response = await async_client.post(
        f"/api/polls/{poll.id}/comments",
        json={"body": long_comment},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_comments_pagination(async_client: AsyncClient, db_session: AsyncSession):
    """Test comment listing with pagination."""
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test poll
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Create multiple comments
    for i in range(25):
        comment = Comment(
            poll_id=poll.id,
            user_id=user.id,
            body=f"Comment {i}"
        )
        db_session.add(comment)
    await db_session.commit()
    
    # Test default pagination (limit=20)
    response = await async_client.get(f"/api/polls/{poll.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data["comments"]) == 20
    assert data["total"] == 25
    assert data["has_more"] == True
    assert data["limit"] == 20
    assert data["offset"] == 0
    
    # Test custom limit
    response = await async_client.get(f"/api/polls/{poll.id}/comments?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["comments"]) == 5
    assert data["has_more"] == True
    
    # Test offset
    response = await async_client.get(f"/api/polls/{poll.id}/comments?limit=5&offset=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["comments"]) == 5
    assert data["has_more"] == False


@pytest.mark.asyncio
async def test_delete_comment_permissions(async_client: AsyncClient, db_session: AsyncSession):
    """Test comment deletion permissions."""
    
    # Create two users
    user1 = User(
        username="user1",
        email="user1@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    user2 = User(
        username="user2",
        email="user2@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Create test poll
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user1.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Create comment by user1
    comment = Comment(
        poll_id=poll.id,
        user_id=user1.id,
        body="Test comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    
    # Login as user1 (comment author)
    login_response = await async_client.post("/api/token", data={
        "username": "user1",
        "password": "password123"
    })
    token1 = login_response.json()["access_token"]
    
    # User1 should be able to delete their own comment
    response = await async_client.delete(
        f"/api/polls/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 204
    
    # Verify comment is soft deleted
    result = await db_session.execute(
        "SELECT is_deleted FROM comments WHERE id = :comment_id",
        {"comment_id": comment.id}
    )
    is_deleted = result.scalar()
    assert is_deleted == True
    
    # Create another comment
    comment2 = Comment(
        poll_id=poll.id,
        user_id=user1.id,
        body="Another test comment"
    )
    db_session.add(comment2)
    await db_session.commit()
    await db_session.refresh(comment2)
    
    # Login as user2 (not comment author)
    login_response = await async_client.post("/api/token", data={
        "username": "user2",
        "password": "password123"
    })
    token2 = login_response.json()["access_token"]
    
    # User2 should not be able to delete user1's comment
    response = await async_client.delete(
        f"/api/polls/comments/{comment2.id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_comments_public_access(async_client: AsyncClient, db_session: AsyncSession):
    """Test that comment listing is publicly accessible."""
    
    # Create test user and poll
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Create a comment
    comment = Comment(
        poll_id=poll.id,
        user_id=user.id,
        body="Public comment"
    )
    db_session.add(comment)
    await db_session.commit()
    
    # Test public access (no authentication required)
    response = await async_client.get(f"/api/polls/{poll.id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data["comments"]) == 1
    assert data["comments"][0]["body"] == "Public comment"


@pytest.mark.asyncio
async def test_create_comment_requires_auth(async_client: AsyncClient, db_session: AsyncSession):
    """Test that comment creation requires authentication."""
    
    # Create test poll
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    poll = Poll(
        title="Test Poll",
        description="A test poll",
        created_by=user.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Try to create comment without authentication
    response = await async_client.post(
        f"/api/polls/{poll.id}/comments",
        json={"body": "Unauthorized comment"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_comment_not_found(async_client: AsyncClient, db_session: AsyncSession):
    """Test deleting a non-existent comment."""
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Login
    login_response = await async_client.post("/api/token", data={
        "username": "testuser",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # Try to delete non-existent comment
    import uuid
    fake_comment_id = uuid.uuid4()
    response = await async_client.delete(
        f"/api/polls/comments/{fake_comment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
