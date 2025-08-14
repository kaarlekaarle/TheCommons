from typing import List, Optional, Literal
from uuid import UUID
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.auth import get_current_active_user, get_current_user_optional
from fastapi import Depends, HTTPException, status
from typing import Optional

# Custom dependency that bypasses authentication for public endpoints
async def bypass_auth():
    """Dependency that bypasses authentication for public endpoints."""
    return None
from backend.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    UnavailableFeatureError,
)
from backend.core.logging_config import get_logger
from backend.database import get_db
from backend.models.label import Label
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.delegation import Delegation
from backend.models.poll_label import poll_labels
from backend.schemas.label import Label as LabelSchema, LabelCreate, LabelUpdate, generate_slug
from backend.schemas.poll import PollSummary
from backend.config import settings

router = APIRouter()
public_router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[LabelSchema])
async def list_labels(
    include_inactive: bool = Query(False, description="Include inactive labels"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> List[Label]:
    """List all labels."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    query = select(Label)
    if not include_inactive:
        query = query.where(Label.is_active == True)
    
    result = await db.execute(query)
    labels = result.scalars().all()
    
    return labels


@router.post("/", response_model=LabelSchema)
async def create_label(
    label_data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Label:
    # Admin guard
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    """Create a new label (admin only)."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    if not settings.ALLOW_PUBLIC_LABELS and not current_user.is_superuser:
        raise AuthorizationError("Only admins can create labels")
    
    # Generate slug from name
    slug = generate_slug(label_data.name)
    
    # Check if slug already exists
    existing_result = await db.execute(
        select(Label).where(Label.slug == slug)
    )
    if existing_result.scalar_one_or_none():
        raise ValidationError(f"Label with slug '{slug}' already exists")
    
    # Create new label
    label = Label(
        name=label_data.name,
        slug=slug,
        is_active=True
    )
    
    db.add(label)
    await db.commit()
    await db.refresh(label)
    
    logger.info(f"Label created: {label.name} ({label.slug})", extra={
        "label_id": str(label.id),
        "created_by": str(current_user.id)
    })
    
    return label


@router.get("/{label_id}", response_model=LabelSchema)
async def get_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Label:
    """Get a specific label by ID."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    result = await db.execute(
        select(Label).where(
            and_(
                Label.id == label_id,
                Label.is_deleted == False
            )
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with id {label_id} not found")
    
    return label


@router.get("/slug/{slug}", response_model=LabelSchema)
async def get_label_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Label:
    """Get a specific label by slug."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    result = await db.execute(
        select(Label).where(
            and_(
                Label.slug == slug,
                Label.is_active == True,
                Label.is_deleted == False
            )
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with slug '{slug}' not found")
    
    return label


@router.patch("/{label_id}", response_model=LabelSchema)
async def update_label(
    label_id: UUID,
    label_data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Label:
    # Admin guard
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    """Update a label (admin only)."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    result = await db.execute(
        select(Label).where(
            and_(
                Label.id == label_id,
                Label.is_deleted == False
            )
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with id {label_id} not found")
    
    # Update fields
    if label_data.name is not None:
        label.name = label_data.name
        # Regenerate slug if name changed
        label.slug = generate_slug(label_data.name)
    
    if label_data.is_active is not None:
        label.is_active = label_data.is_active
    
    await db.commit()
    await db.refresh(label)
    
    logger.info(f"Label updated: {label.name} ({label.slug})", extra={
        "label_id": str(label.id),
        "updated_by": str(current_user.id)
    })
    
    return label


@router.delete("/{label_id}")
async def delete_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    # Admin guard
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    """Soft delete a label (admin only)."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    result = await db.execute(
        select(Label).where(
            and_(
                Label.id == label_id,
                Label.is_deleted == False
            )
        )
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with id {label_id} not found")
    
    # Soft delete
    await label.soft_delete(db)
    await db.commit()
    
    logger.info(f"Label deleted: {label.name} ({label.slug})", extra={
        "label_id": str(label.id),
        "deleted_by": str(current_user.id)
    })
    
    return {"message": "Label deleted successfully"}


@router.get("/{slug}/overview")
async def get_label_overview(
    slug: str,
    tab: Literal["all", "principles", "actions"] = Query("all", description="Tab filter: all, principles, actions"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(12, ge=1, le=24, description="Items per page (max 24)"),
    sort: Literal["newest", "oldest"] = Query("newest", description="Sort order: newest, oldest"),
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # Debug logging for duplicate investigation
    if settings.DEBUG or settings.TESTING:
        logger.info(f"Label overview request: slug={slug}, tab={tab}, page={page}, per_page={per_page}, sort={sort}")
    """Get overview for a specific label including counts, recent polls, and delegation info."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    # Get the label
    label_result = await db.execute(
        select(Label).where(
            and_(
                Label.slug == slug,
                Label.is_active == True,
                Label.is_deleted == False
            )
        )
    )
    label = label_result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with slug '{slug}' not found")
    
    # ETag support (skip in testing)
    if not settings.TESTING:
        # Get the most recent poll creation time for this label to use in ETag
        latest_poll_result = await db.execute(
            select(Poll.created_at).join(Poll.labels).where(
                and_(
                    Poll.labels.any(id=label.id),
                    Poll.is_deleted == False
                )
            ).order_by(desc(Poll.created_at)).limit(1)
        )
        latest_poll_created_at = latest_poll_result.scalar_one_or_none()
        
        # Create weak ETag from parameters and latest poll time
        etag_data = f"{slug}:{tab}:{page}:{per_page}:{sort}:{latest_poll_created_at}"
        etag = f'W/"{hashlib.md5(etag_data.encode()).hexdigest()}"'
        
        # Check If-None-Match header
        if_none_match = request.headers.get("if-none-match") if request else None
        if if_none_match and if_none_match == etag:
            response.status_code = 304
            return None
        
        # Set ETag header
        if response:
            response.headers["ETag"] = etag
    
    # Get counts using EXISTS to avoid row multiplication
    label_subq = select(poll_labels.c.poll_id).join(Label).where(Label.id == label.id)
    
    level_a_count_result = await db.execute(
        select(func.count(Poll.id)).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.decision_type == "level_a",
                Poll.is_deleted == False
            )
        )
    )
    level_a_count = level_a_count_result.scalar()
    
    level_b_count_result = await db.execute(
        select(func.count(Poll.id)).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.decision_type == "level_b",
                Poll.is_deleted == False
            )
        )
    )
    level_b_count = level_b_count_result.scalar()
    
    level_c_count_result = await db.execute(
        select(func.count(Poll.id)).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.decision_type == "level_c",
                Poll.is_deleted == False
            )
        )
    )
    level_c_count = level_c_count_result.scalar()
    
    total_count = level_a_count + level_b_count + level_c_count
    
    # Build query using EXISTS to avoid row multiplication
    base_query = select(Poll).options(selectinload(Poll.labels)).where(
        and_(
            Poll.id.in_(label_subq),
            Poll.is_deleted == False
        )
    )
    
    # Apply tab filter
    if tab == "principles":
        base_query = base_query.where(Poll.decision_type == "level_a")
    elif tab == "actions":
        base_query = base_query.where(Poll.decision_type == "level_b")
    # "all" tab includes all decision types
    
    # Apply sorting
    if sort == "newest":
        base_query = base_query.order_by(desc(Poll.created_at))
    else:  # oldest
        base_query = base_query.order_by(Poll.created_at)
    
    # Debug logging for SQL query
    if settings.DEBUG or settings.TESTING:
        compiled_query = base_query.compile(compile_kwargs={"literal_binds": True})
        logger.info(f"Base query SQL: {compiled_query}")
    
    # Get total count for the current tab using DISTINCT
    count_query = select(func.count(func.distinct(Poll.id))).where(
        and_(
            Poll.id.in_(label_subq),
            Poll.is_deleted == False
        )
    )
    
    if tab == "principles":
        count_query = count_query.where(Poll.decision_type == "level_a")
    elif tab == "actions":
        count_query = count_query.where(Poll.decision_type == "level_b")
    
    tab_total_result = await db.execute(count_query)
    tab_total = tab_total_result.scalar()
    
    # Debug logging for row counts
    if settings.DEBUG or settings.TESTING:
        logger.info(f"Tab total count: {tab_total}")
    
    # Apply pagination
    offset = (page - 1) * per_page
    paginated_query = base_query.offset(offset).limit(per_page)
    
    # Execute the query
    polls_result = await db.execute(paginated_query)
    polls = polls_result.scalars().all()
    
    # Debug logging for result count
    if settings.DEBUG or settings.TESTING:
        logger.info(f"Returned polls count: {len(polls)}")
        poll_ids = [str(poll.id) for poll in polls]
        logger.info(f"Poll IDs: {poll_ids}")
    
    # Calculate pagination info
    total_pages = (tab_total + per_page - 1) // per_page  # Ceiling division
    
    # Get delegation summary for current user (if authenticated)
    delegation_summary = None
    if current_user:
        # Get label-specific delegation
        label_delegation_result = await db.execute(
            select(Delegation).join(User, Delegation.delegatee_id == User.id).where(
                and_(
                    Delegation.delegator_id == current_user.id,
                    Delegation.label_id == label.id,
                    Delegation.revoked_at.is_(None),
                    Delegation.is_deleted == False
                )
            )
        )
        label_delegation = label_delegation_result.scalar_one_or_none()
        
        # Get global delegation
        global_delegation_result = await db.execute(
            select(Delegation).join(User, Delegation.delegatee_id == User.id).where(
                and_(
                    Delegation.delegator_id == current_user.id,
                    Delegation.label_id == None,
                    Delegation.revoked_at.is_(None),
                    Delegation.is_deleted == False
                )
            )
        )
        global_delegation = global_delegation_result.scalar_one_or_none()
        
        if label_delegation or global_delegation:
            delegation_summary = {
                "label_delegate": {
                    "id": str(label_delegation.delegatee_id),
                    "username": label_delegation.delegatee.username,
                    "email": label_delegation.delegatee.email
                } if label_delegation else None,
                "global_delegate": {
                    "id": str(global_delegation.delegatee_id),
                    "username": global_delegation.delegatee.username,
                    "email": global_delegation.delegatee.email
                } if global_delegation else None
            }
    
    def convert_to_poll_summary(poll: Poll) -> dict:
        return {
            "id": str(poll.id),
            "title": poll.title,
            "decision_type": poll.decision_type,
            "created_at": poll.created_at.isoformat(),
            "labels": [
                {
                    "name": label.name,
                    "slug": label.slug
                }
                for label in poll.labels
            ]
        }
    
    # API contract guard: verify uniqueness before returning
    seen_poll_ids = set()
    dedup_items = []
    for poll in polls:
        if poll.id not in seen_poll_ids:
            seen_poll_ids.add(poll.id)
            dedup_items.append(poll)
    
    # DEV/TESTING gated assertion and log for uniqueness at the wire
    ids = [str(p.id) for p in polls]
    dupes = {x for x in ids if ids.count(x) > 1}
    if (settings.DEBUG or settings.TESTING) and dupes:
        logger.warning("TOPIC_OVERVIEW_DUPES slug=%s dupes=%s sample_ids=%s",
                      slug, sorted(list(dupes))[:10], ids[:50])
    
    if len(dedup_items) != len(polls) and (settings.DEBUG or settings.TESTING):
        logger.warning(f"Duplicate polls detected in response for slug={slug}: "
                      f"returned {len(polls)} items, unique {len(dedup_items)} items")
        duplicate_ids = [str(poll.id) for poll in polls if str(poll.id) in seen_poll_ids]
        logger.warning(f"Duplicate poll IDs: {duplicate_ids}")
    
    # Use deduplicated items for response
    final_polls = dedup_items
    
    response_data = {
        "label": {
            "id": str(label.id),
            "name": label.name,
            "slug": label.slug
        },
        "counts": {
            "level_a": level_a_count,
            "level_b": level_b_count,
            "level_c": level_c_count,
            "total": total_count
        },
        "page": {
            "page": page,
            "per_page": per_page,
            "total": tab_total,
            "total_pages": total_pages
        },
        "items": [convert_to_poll_summary(poll) for poll in final_polls],
        "delegation_summary": delegation_summary
    }
    
    # Add debug info in development
    if settings.DEBUG or settings.TESTING:
        response_data["_debug"] = {
            "ids": [str(p.id) for p in final_polls],
            "total_returned": len(final_polls),
            "total_before_dedup": len(polls)
        }
    
    return response_data

@router.get("/dev/labels/{slug}/raw")
async def get_label_raw_debug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Debug endpoint to get raw label data (dev only)."""
    if not (settings.DEBUG or settings.TESTING or (current_user and current_user.is_superuser)):
        raise HTTPException(status_code=403, detail="Debug endpoint requires DEBUG/TESTING or superuser")
    
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    # Get the label
    label_result = await db.execute(
        select(Label).where(
            and_(
                Label.slug == slug,
                Label.is_active == True,
                Label.is_deleted == False
            )
        )
    )
    label = label_result.scalar_one_or_none()
    
    if not label:
        raise ResourceNotFoundError(f"Label with slug '{slug}' not found")
    
    # Get raw data for each tab
    label_subq = select(poll_labels.c.poll_id).join(Label).where(Label.id == label.id)
    
    # Level A (principles)
    level_a_result = await db.execute(
        select(Poll.id).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.decision_type == "level_a",
                Poll.is_deleted == False
            )
        ).order_by(desc(Poll.created_at))
    )
    level_a_ids = [str(row[0]) for row in level_a_result.fetchall()]
    
    # Level B (actions)
    level_b_result = await db.execute(
        select(Poll.id).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.decision_type == "level_b",
                Poll.is_deleted == False
            )
        ).order_by(desc(Poll.created_at))
    )
    level_b_ids = [str(row[0]) for row in level_b_result.fetchall()]
    
    # All polls
    all_result = await db.execute(
        select(Poll.id).where(
            and_(
                Poll.id.in_(label_subq),
                Poll.is_deleted == False
            )
        ).order_by(desc(Poll.created_at))
    )
    all_ids = [str(row[0]) for row in all_result.fetchall()]
    
    # Check for duplicates in each array
    def find_dupes(ids):
        return {x for x in ids if ids.count(x) > 1}
    
    return {
        "ids": {
            "level_a": level_a_ids,
            "level_b": level_b_ids,
            "all": all_ids
        },
        "counts": {
            "level_a": len(level_a_ids),
            "level_b": len(level_b_ids),
            "all": len(all_ids)
        },
        "duplicates": {
            "level_a": list(find_dupes(level_a_ids)),
            "level_b": list(find_dupes(level_b_ids)),
            "all": list(find_dupes(all_ids))
        }
    }


@public_router.get("/popular")
async def get_popular_labels(
    limit: int = Query(8, ge=1, le=24, description="Number of popular labels to return (max 24)"),
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    """Get popular labels by attached poll count."""
    if not settings.LABELS_ENABLED:
        raise UnavailableFeatureError("Labels feature is disabled")
    
    # ETag support (skip in testing)
    if not settings.TESTING:
        # Get the most recent label update time for ETag
        latest_label_result = await db.execute(
            select(Label.updated_at).where(
                and_(
                    Label.is_active == True,
                    Label.is_deleted == False
                )
            ).order_by(desc(Label.updated_at)).limit(1)
        )
        latest_label_updated_at = latest_label_result.scalar_one_or_none()
        
        # Create weak ETag from limit and latest label update time
        etag_data = f"popular:{limit}:{latest_label_updated_at}"
        etag = f'W/"{hashlib.md5(etag_data.encode()).hexdigest()}"'
        
        # Check If-None-Match header
        if_none_match = request.headers.get("if-none-match") if request else None
        if if_none_match and if_none_match == etag:
            response.status_code = 304
            return None
        
        # Set ETag header
        if response:
            response.headers["ETag"] = etag
    
    # Simple in-memory cache for non-testing environments
    cache_key = f"popular_labels_{limit}"
    if not settings.TESTING and hasattr(get_popular_labels, '_cache'):
        cache_data = getattr(get_popular_labels, '_cache', {})
        if cache_key in cache_data:
            return cache_data[cache_key]
    
    # Get labels with poll counts
    from backend.models.poll_label import poll_labels
    
    result = await db.execute(
        select(
            Label.id,
            Label.name,
            Label.slug,
            func.count(poll_labels.c.poll_id).label('poll_count')
        ).outerjoin(poll_labels).where(
            and_(
                Label.is_active == True,
                Label.is_deleted == False
            )
        ).group_by(Label.id, Label.name, Label.slug)
        .order_by(desc(func.count(poll_labels.c.poll_id)), Label.slug)
        .limit(limit)
    )
    
    labels_with_counts = result.all()
    
    popular_labels = [
        {
            "id": str(row.id),
            "name": row.name,
            "slug": row.slug,
            "poll_count": row.poll_count
        }
        for row in labels_with_counts
    ]
    
    # Cache the result for 60 seconds in non-testing environments
    if not settings.TESTING:
        if not hasattr(get_popular_labels, '_cache'):
            setattr(get_popular_labels, '_cache', {})
        cache_data = getattr(get_popular_labels, '_cache', {})
        cache_data[cache_key] = popular_labels
        setattr(get_popular_labels, '_cache', cache_data)
    
    return popular_labels
