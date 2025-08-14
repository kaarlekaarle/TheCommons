import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.tests.fixtures.seed_minimal import seed_minimal_user, seed_minimal_poll, seed_minimal_label
import asyncio


@pytest.mark.asyncio
async def test_overview_unique_ids(client: AsyncClient, db_session: AsyncSession):
    """Test that overview API returns unique poll IDs."""
    user = await seed_minimal_user(db_session)
    label = await seed_minimal_label(db_session, "Mobility", "mobility")
    
    # Create multiple polls with the same label
    polls = []
    for i in range(5):
        poll = await seed_minimal_poll(db_session, owner_id=str(user.id), decision_type="level_b")
        polls.append(poll)
        
        # Add label to poll
        await db_session.execute(
            text("INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)"),
            {"poll_id": str(poll.id), "label_id": str(label.id)}
        )
    
    await db_session.commit()
    
    # Test with 'mobility' slug
    resp = await client.get(f"/api/labels/mobility/overview")
    assert resp.status_code == 200
    data = resp.json()
    
    # Extract poll IDs
    poll_ids = [item["id"] for item in data["items"]]
    
    # Assert uniqueness
    assert len(poll_ids) == len(set(poll_ids)), f"Duplicate IDs found: {poll_ids}"


@pytest.mark.asyncio
async def test_overview_stable_sort(client: AsyncClient, db_session: AsyncSession):
    """Test that overview API returns stable sort order across multiple calls."""
    user = await seed_minimal_user(db_session)
    label = await seed_minimal_label(db_session, "Test Label", "test-label")
    
    # Create multiple polls with different creation times
    polls = []
    for i in range(3):
        poll = await seed_minimal_poll(db_session, owner_id=str(user.id), decision_type="level_b")
        polls.append(poll)
        
        # Add label to poll
        await db_session.execute(
            text("INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)"),
            {"poll_id": str(poll.id), "label_id": str(label.id)}
        )
    
    await db_session.commit()
    
    # Call API twice
    resp1 = await client.get(f"/api/labels/test-label/overview?sort=newest")
    resp2 = await client.get(f"/api/labels/test-label/overview?sort=newest")
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    
    data1 = resp1.json()
    data2 = resp2.json()
    
    # Extract poll IDs in order
    ids1 = [item["id"] for item in data1["items"]]
    ids2 = [item["id"] for item in data2["items"]]
    
    # Assert identical ordered lists
    assert ids1 == ids2, f"Sort order not stable: {ids1} vs {ids2}"


@pytest.mark.asyncio
async def test_overview_pagination_stable(client: AsyncClient, db_session: AsyncSession):
    """Test that pagination returns stable results for the same page."""
    user = await seed_minimal_user(db_session)
    label = await seed_minimal_label(db_session, "Test Label", "test-label")
    
    # Create enough polls to test pagination
    polls = []
    for i in range(15):  # More than per_page=12
        poll = await seed_minimal_poll(db_session, owner_id=str(user.id), decision_type="level_b")
        polls.append(poll)
        
        # Add label to poll
        await db_session.execute(
            text("INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)"),
            {"poll_id": str(poll.id), "label_id": str(label.id)}
        )
    
    await db_session.commit()
    
    # Call API twice for the same page
    resp1 = await client.get(f"/api/labels/test-label/overview?page=1&per_page=5")
    resp2 = await client.get(f"/api/labels/test-label/overview?page=1&per_page=5")
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    
    data1 = resp1.json()
    data2 = resp2.json()
    
    # Extract poll IDs in order
    ids1 = [item["id"] for item in data1["items"]]
    ids2 = [item["id"] for item in data2["items"]]
    
    # Assert identical ordered lists
    assert ids1 == ids2, f"Pagination not stable: {ids1} vs {ids2}"
    
    # Also verify pagination metadata is consistent
    assert data1["page"]["page"] == data2["page"]["page"]
    assert data1["page"]["per_page"] == data2["page"]["per_page"]
    assert data1["page"]["total"] == data2["page"]["total"]
    assert data1["page"]["total_pages"] == data2["page"]["total_pages"]


@pytest.mark.asyncio
async def test_overview_property_based_unique_stable(client: AsyncClient, db_session: AsyncSession):
    """Property-based test that fabricates label memberships and asserts uniqueness and stability."""
    user = await seed_minimal_user(db_session)
    
    # Test with different configurations
    test_configs = [
        (3, 2, "level_a"),
        (5, 3, "level_b"),
        (2, 1, "level_c"),
    ]
    
    for test_idx, (num_polls, num_labels, decision_type) in enumerate(test_configs):
        # Create labels with unique slugs
        labels = []
        for i in range(num_labels):
            label = await seed_minimal_label(db_session, f"Label {test_idx}-{i}", f"label-{test_idx}-{i}")
            labels.append(label)
        
        # Create polls with overlapping labels
        polls = []
        for i in range(num_polls):
            poll = await seed_minimal_poll(db_session, owner_id=str(user.id), decision_type=decision_type)
            polls.append(poll)
            
            # Add poll to multiple labels (creating potential for duplicates)
            for j in range(min(2, num_labels)):  # Add to up to 2 labels
                label_idx = (i + j) % num_labels
                await db_session.execute(
                    text("INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)"),
                    {"poll_id": str(poll.id), "label_id": str(labels[label_idx].id)}
                )
        
        await db_session.commit()
        
        # Test each label for uniqueness and stability
        for label in labels:
            # Call API twice
            resp1 = await client.get(f"/api/labels/{label.slug}/overview")
            resp2 = await client.get(f"/api/labels/{label.slug}/overview")
            
            assert resp1.status_code == 200
            assert resp2.status_code == 200
            
            data1 = resp1.json()
            data2 = resp2.json()
            
            # Extract poll IDs
            ids1 = [item["id"] for item in data1["items"]]
            ids2 = [item["id"] for item in data2["items"]]
            
            # Assert uniqueness
            assert len(ids1) == len(set(ids1)), f"Duplicate IDs in first call: {ids1}"
            assert len(ids2) == len(set(ids2)), f"Duplicate IDs in second call: {ids2}"
            
            # Assert stability (same order)
            assert ids1 == ids2, f"Sort order not stable for {label.slug}: {ids1} vs {ids2}"


@pytest.mark.asyncio
async def test_overview_sort_order_consistency(client: AsyncClient, db_session: AsyncSession):
    """Test that sort order is consistent with created_at DESC, id DESC."""
    user = await seed_minimal_user(db_session)
    label = await seed_minimal_label(db_session, "Test Label", "test-label")
    
    # Create polls with known creation times
    polls = []
    for i in range(3):
        poll = await seed_minimal_poll(db_session, owner_id=str(user.id), decision_type="level_b")
        polls.append(poll)
        
        # Add label to poll
        await db_session.execute(
            text("INSERT INTO poll_labels (poll_id, label_id) VALUES (:poll_id, :label_id)"),
            {"poll_id": str(poll.id), "label_id": str(label.id)}
        )
    
    await db_session.commit()
    
    # Test newest sort (should be created_at DESC, id DESC)
    resp = await client.get(f"/api/labels/test-label/overview?sort=newest")
    assert resp.status_code == 200
    data = resp.json()
    
    # Extract poll IDs and creation times
    items = data["items"]
    poll_data = [(item["id"], item["created_at"]) for item in items]
    
    # Verify sort order: should be descending by created_at, then by id
    for i in range(len(poll_data) - 1):
        current_time, current_id = poll_data[i][1], poll_data[i][0]
        next_time, next_id = poll_data[i + 1][1], poll_data[i + 1][0]
        
        # Either current time is newer, or if times are equal, current id should be greater
        assert (current_time > next_time) or (current_time == next_time and current_id > next_id), \
            f"Sort order incorrect at position {i}: {current_time}:{current_id} vs {next_time}:{next_id}"
