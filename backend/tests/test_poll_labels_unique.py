import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.poll import Poll
from backend.models.label import Label
from backend.models.poll_label import poll_labels
from backend.models.user import User


@pytest.mark.asyncio
async def test_poll_labels_unique_constraint(db_session: AsyncSession, test_user: User):
    """Test that the unique constraint prevents duplicate poll-label relationships."""
    
    # Create a label and poll
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    
    db_session.add_all([label, poll])
    await db_session.commit()
    
    # Insert first poll-label relationship
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Try to insert duplicate - should raise IntegrityError
    with pytest.raises(IntegrityError):
        await db_session.execute(
            poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
        )
        await db_session.commit()


@pytest.mark.asyncio
async def test_poll_labels_same_poll_different_labels(db_session: AsyncSession, test_user: User):
    """Test that a poll can be associated with multiple different labels."""
    
    # Create multiple labels and one poll
    label1 = Label(
        id=uuid4(),
        name="Test Label 1",
        slug="test-label-1",
        is_active=True
    )
    label2 = Label(
        id=uuid4(),
        name="Test Label 2",
        slug="test-label-2",
        is_active=True
    )
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    
    db_session.add_all([label1, label2, poll])
    await db_session.commit()
    
    # Insert poll-label relationships with different labels
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label1.id)
    )
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label2.id)
    )
    await db_session.commit()
    
    # Verify both relationships exist
    result = await db_session.execute(
        select(poll_labels).where(poll_labels.c.poll_id == poll.id)
    )
    relationships = result.fetchall()
    assert len(relationships) == 2, "Should have 2 poll-label relationships"


@pytest.mark.asyncio
async def test_poll_labels_different_polls_same_label(db_session: AsyncSession, test_user: User):
    """Test that multiple polls can be associated with the same label."""
    
    # Create one label and multiple polls
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    poll1 = Poll(
        id=uuid4(),
        title="Test Poll 1",
        decision_type="level_a",
        created_by=test_user.id
    )
    poll2 = Poll(
        id=uuid4(),
        title="Test Poll 2",
        decision_type="level_b",
        created_by=test_user.id
    )
    
    db_session.add_all([label, poll1, poll2])
    await db_session.commit()
    
    # Insert poll-label relationships with different polls
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll1.id, label_id=label.id)
    )
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll2.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Verify both relationships exist
    result = await db_session.execute(
        select(poll_labels).where(poll_labels.c.label_id == label.id)
    )
    relationships = result.fetchall()
    assert len(relationships) == 2, "Should have 2 poll-label relationships"


@pytest.mark.asyncio
async def test_poll_labels_cascade_delete(db_session: AsyncSession, test_user: User):
    """Test that poll-label relationships are deleted when poll is deleted."""
    
    # Create a label and poll
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    
    db_session.add_all([label, poll])
    await db_session.commit()
    
    # Insert poll-label relationship
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Verify relationship exists
    result = await db_session.execute(
        select(poll_labels).where(
            (poll_labels.c.poll_id == poll.id) & 
            (poll_labels.c.label_id == label.id)
        )
    )
    relationship = result.fetchone()
    assert relationship is not None, "Poll-label relationship should exist"
    
    # Delete the poll
    await db_session.delete(poll)
    await db_session.commit()
    
    # Verify relationship is deleted
    result = await db_session.execute(
        select(poll_labels).where(
            (poll_labels.c.poll_id == poll.id) & 
            (poll_labels.c.label_id == label.id)
        )
    )
    relationship = result.fetchone()
    assert relationship is None, "Poll-label relationship should be deleted"


@pytest.mark.asyncio
async def test_poll_labels_cascade_delete_label(db_session: AsyncSession, test_user: User):
    """Test that poll-label relationships are deleted when label is deleted."""
    
    # Create a label and poll
    label = Label(
        id=uuid4(),
        name="Test Label",
        slug="test-label",
        is_active=True
    )
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        decision_type="level_a",
        created_by=test_user.id
    )
    
    db_session.add_all([label, poll])
    await db_session.commit()
    
    # Insert poll-label relationship
    await db_session.execute(
        poll_labels.insert().values(poll_id=poll.id, label_id=label.id)
    )
    await db_session.commit()
    
    # Verify relationship exists
    result = await db_session.execute(
        select(poll_labels).where(
            (poll_labels.c.poll_id == poll.id) & 
            (poll_labels.c.label_id == label.id)
        )
    )
    relationship = result.fetchone()
    assert relationship is not None, "Poll-label relationship should exist"
    
    # Delete the label
    await db_session.delete(label)
    await db_session.commit()
    
    # Verify relationship is deleted
    result = await db_session.execute(
        select(poll_labels).where(
            (poll_labels.c.poll_id == poll.id) & 
            (poll_labels.c.label_id == label.id)
        )
    )
    relationship = result.fetchone()
    assert relationship is None, "Poll-label relationship should be deleted"
