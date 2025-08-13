from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user, oauth2_scheme
from backend.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)
from backend.core.logging_config import get_logger
from backend.core.audit_mw import audit_event
from backend.core.metrics import increment_delegation_metric
from backend.database import get_db
from backend.models.delegation import Delegation
from backend.models.user import User
from backend.schemas.delegation import (
    DelegationCreate,
    DelegationInfo,
    DelegationResponse,
)

logger = get_logger(__name__)
router = APIRouter(tags=["delegations"])


@router.post("/", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
async def create_delegation(
    request: Request,
    delegation_in: DelegationCreate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Delegation:
    """Create a new delegation.

    Args:
        delegation_in: Delegation creation data
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Delegation: Created delegation

    Raises:
        ValidationError: If delegation data is invalid
        ServerError: If an unexpected error occurs
    """
    logger.info(
        "Creating new delegation",
        extra={"delegation_data": delegation_in.model_dump(), "user_id": current_user.id},
    )
    
    try:
        # Check if user is trying to delegate to themselves
        if delegation_in.delegatee_id == current_user.id:
            raise ValidationError("Cannot delegate to yourself")
        
        # Create the delegation directly without complex validation
        delegation = Delegation(
            delegator_id=current_user.id,
            delegatee_id=delegation_in.delegatee_id
        )
        db.add(delegation)
        await db.commit()
        
        logger.info(
            "Delegation created successfully",
            extra={"delegation_id": delegation.id, "user_id": current_user.id},
        )
        
        # Track delegation creation metric
        increment_delegation_metric("delegation_created", str(current_user.id))
        
        # Audit the delegation creation
        audit_event(
            "delegation_created",
            {
                "delegation_id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
            },
            request
        )
        
        # Broadcast delegation update
        try:
            from backend.core.websocket import manager
            await manager.broadcast_delegation_update({
                "id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast delegation creation", extra={"error": str(e)})
        
        # Return a simple response
        return {
            "id": str(delegation.id),
            "delegator_id": str(delegation.delegator_id),
            "delegatee_id": str(delegation.delegatee_id),
            "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
            "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to create delegation",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        if isinstance(e, (ValidationError, AuthorizationError)):
            raise
        raise ServerError("Failed to create delegation")


@router.post("/simple", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_delegation_simple(
    delegation_in: DelegationCreate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new delegation using a simpler approach."""
    logger.info(
        "Creating new delegation (simple)",
        extra={"delegation_data": delegation_in.model_dump(), "user_id": current_user.id},
    )
    
    try:
        # Check if user is trying to delegate to themselves
        if delegation_in.delegatee_id == current_user.id:
            raise ValidationError("Cannot delegate to yourself")
        
        # Remove any existing delegation first
        await db.execute(
            "UPDATE delegations SET is_deleted = true WHERE delegator_id = :delegator_id",
            {"delegator_id": str(current_user.id)}
        )
        
        # Insert new delegation using raw SQL
        result = await db.execute(
            """
            INSERT INTO delegations (id, delegator_id, delegatee_id, created_at, updated_at, is_deleted)
            VALUES (gen_random_uuid(), :delegator_id, :delegatee_id, now(), now(), false)
            RETURNING id, delegator_id, delegatee_id, created_at, updated_at
            """,
            {
                "delegator_id": str(current_user.id),
                "delegatee_id": str(delegation_in.delegatee_id)
            }
        )
        
        await db.commit()
        
        row = result.fetchone()
        if row:
            logger.info(
                "Delegation created successfully (simple)",
                extra={"delegation_id": row[0], "user_id": current_user.id},
            )
            
            return {
                "id": str(row[0]),
                "delegator_id": str(row[1]),
                "delegatee_id": str(row[2]),
                "created_at": row[3].isoformat() if row[3] else None,
                "updated_at": row[4].isoformat() if row[4] else None
            }
        else:
            raise ServerError("Failed to create delegation")
        
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to create delegation (simple)",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        if isinstance(e, (ValidationError, AuthorizationError)):
            raise
        raise ServerError("Failed to create delegation")


@router.post("/direct", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_delegation_direct(
    delegation_in: DelegationCreate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
) -> dict:
    """Create a new delegation using direct database connection."""
    logger.info(
        "Creating new delegation (direct)",
        extra={"delegation_data": delegation_in.model_dump(), "user_id": current_user.id},
    )
    
    try:
        # Check if user is trying to delegate to themselves
        if delegation_in.delegatee_id == current_user.id:
            raise ValidationError("Cannot delegate to yourself")
        
        # Use a direct database connection
        from backend.database import engine
        from sqlalchemy import text
        import uuid
        from datetime import datetime
        
        async with engine.begin() as conn:
            # Delete any existing delegation first
            await conn.execute(
                text("DELETE FROM delegations WHERE delegator_id = :delegator_id"),
                {"delegator_id": str(current_user.id)}
            )
            
            # Insert new delegation
            delegation_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await conn.execute(
                text("""
                INSERT INTO delegations (id, delegator_id, delegatee_id, created_at, updated_at, is_deleted)
                VALUES (:id, :delegator_id, :delegatee_id, :created_at, :updated_at, false)
                """),
                {
                    "id": delegation_id,
                    "delegator_id": str(current_user.id),
                    "delegatee_id": str(delegation_in.delegatee_id),
                    "created_at": now,
                    "updated_at": now
                }
            )
        
        logger.info(
            "Delegation created successfully (direct)",
            extra={"delegation_id": delegation_id, "user_id": current_user.id},
        )
        
        return {
            "id": delegation_id,
            "delegator_id": str(current_user.id),
            "delegatee_id": str(delegation_in.delegatee_id),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Failed to create delegation (direct)",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        if isinstance(e, (ValidationError, AuthorizationError)):
            raise
        raise ServerError("Failed to create delegation")


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_delegation(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove the current user's delegation.

    Args:
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Raises:
        ResourceNotFoundError: If no delegation exists
        ServerError: If an unexpected error occurs
    """
    logger.info(
        "Removing delegation",
        extra={"user_id": current_user.id},
    )
    
    try:
        # Find the user's delegation
        delegation_result = await db.execute(
            select(Delegation).where(
                and_(
                    Delegation.delegator_id == current_user.id,
                    Delegation.is_deleted == False
                )
            )
        )
        delegation = delegation_result.scalar_one_or_none()
        
        if not delegation:
            raise ResourceNotFoundError("No delegation found")
        
        # Soft delete the delegation
        await delegation.soft_delete(db)
        await db.commit()
        
        logger.info(
            "Delegation removed successfully",
            extra={"delegation_id": delegation.id, "user_id": current_user.id},
        )
        
        # Track delegation revocation metric
        increment_delegation_metric("delegation_revoked", str(current_user.id))
        
        # Audit the delegation removal
        audit_event(
            "delegation_removed",
            {
                "delegation_id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
            },
            request
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to remove delegation",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        if isinstance(e, (ValidationError, AuthorizationError, ResourceNotFoundError)):
            raise
        raise ServerError("Failed to remove delegation")


@router.get("/me", response_model=DelegationInfo)
async def get_my_delegation(
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DelegationInfo:
    """Get the current user's delegation information.

    Args:
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        DelegationInfo: User's delegation information
    """
    logger.info(
        "Getting user delegation",
        extra={"user_id": current_user.id},
    )
    
    try:
        # Find the user's delegation
        delegation_result = await db.execute(
            select(Delegation).where(
                and_(
                    Delegation.delegator_id == current_user.id,
                    Delegation.is_deleted == False
                )
            )
        )
        delegation = delegation_result.scalar_one_or_none()
        
        if not delegation:
            return DelegationInfo(has_delegate=False)
        
        # Fetch delegate info
        delegate_result = await db.execute(
            select(User).where(
                and_(
                    User.id == delegation.delegatee_id,
                    User.is_deleted == False
                )
            )
        )
        delegate = delegate_result.scalar_one_or_none()
        
        if not delegate:
            # Delegate was deleted, return no delegation
            return DelegationInfo(has_delegate=False)
        
        return DelegationInfo(
            has_delegatee=True,
            delegatee_id=delegate.id,
            delegatee_username=delegate.username,
            delegatee_email=delegate.email,
            created_at=delegation.created_at
        )
        
    except Exception as e:
        logger.error(
            "Failed to get user delegation",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get delegation information")
