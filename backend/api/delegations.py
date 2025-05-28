from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user, get_current_user
from backend.core.decorators import handle_errors
from backend.core.exceptions import ResourceNotFoundError
from backend.core.exceptions.delegation import (
    CircularDelegationError,
    DelegationAlreadyExistsError,
    DelegationChainError,
    DelegationLimitExceededError,
    DelegationStatsError,
    InvalidDelegationPeriodError,
    SelfDelegationError,
)
from backend.core.exceptions import DelegationAuthorizationError
from backend.core.logging_config import get_logger
from backend.core.tasks import StatsCalculationTask
from backend.database import get_db
from backend.models.delegation import Delegation
from backend.models.user import User
from backend.schemas.delegation import (
    Delegation,
    DelegationChainResponse,
    DelegationCreate,
    DelegationListResponse,
    DelegationStatsResponse,
    DelegationTransparencyResponse,
)
from backend.services.delegation import DelegationService

router = APIRouter(prefix="/delegations", tags=["delegations"])
logger = get_logger(__name__)


@router.post("", response_model=Delegation)
@handle_errors
async def create_delegation(
    delegation: DelegationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Delegation:
    """Create a new delegation."""
    service = DelegationService(db)
    try:
        created_delegation = await service.create_delegation(
            delegator_id=current_user.id,
            delegatee_id=delegation.delegatee_id,
            start_date=delegation.start_date or datetime.utcnow(),
            end_date=delegation.end_date,
            poll_id=delegation.poll_id,
        )
        return Delegation.from_orm(created_delegation)
    except (
        SelfDelegationError,
        CircularDelegationError,
        InvalidDelegationPeriodError,
        DelegationAlreadyExistsError,
        DelegationLimitExceededError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{delegation_id}", response_model=Delegation)
@handle_errors
async def get_delegation(
    delegation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Delegation:
    """Get a delegation by ID."""
    service = DelegationService(db)
    try:
        delegation = await service.get_delegation(delegation_id)
        return Delegation.from_orm(delegation)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=DelegationListResponse)
@handle_errors
async def list_delegations(
    poll_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DelegationListResponse:
    """List delegations for the current user."""
    service = DelegationService(db)
    delegations = await service.get_active_delegations(current_user.id, poll_id)
    return DelegationListResponse(
        delegations=[Delegation.from_orm(d) for d in delegations]
    )


@router.delete("/{delegation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_delegation(
    delegation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a delegation."""
    service = DelegationService(db)
    try:
        await service.revoke_delegation(delegation_id, current_user.id)
    except (ResourceNotFoundError, DelegationAuthorizationError) as e:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if isinstance(e, ResourceNotFoundError)
                else status.HTTP_403_FORBIDDEN
            ),
            detail=str(e),
        )


@router.get("/resolve/{poll_id}", response_model=DelegationChainResponse)
@handle_errors(
    {
        DelegationChainError: (400, "Invalid delegation chain"),
    }
)
async def resolve_delegation_chain(
    poll_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DelegationChainResponse:
    """Resolve the delegation chain for a specific poll.

    Args:
        poll_id: ID of the poll
        current_user: Currently authenticated user
        db: Database session

    Returns:
        DelegationChainResponse: Resolved delegation chain
    """
    service = DelegationService(db)
    try:
        final_delegatee_id = await service.resolve_delegation_chain(
            current_user.id, poll_id
        )
        return DelegationChainResponse(
            final_delegatee_id=final_delegatee_id,
            chain_length=1,  # TODO: Implement chain length tracking
            is_circular=False,
            exceeds_max_depth=False,
        )
    except DelegationChainError as e:
        if "exceeds maximum depth" in str(e):
            return DelegationChainResponse(
                final_delegatee_id=current_user.id,
                chain_length=5,
                is_circular=False,
                exceeds_max_depth=True,
            )
        elif "Circular delegation" in str(e):
            return DelegationChainResponse(
                final_delegatee_id=current_user.id,
                chain_length=0,
                is_circular=True,
                exceeds_max_depth=False,
            )
        raise


@router.get("/transparency/{poll_id}", response_model=DelegationTransparencyResponse)
async def get_delegation_transparency(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DelegationTransparencyResponse:
    """Get transparency information about delegations for a poll.

    Args:
        poll_id: ID of the poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        DelegationTransparencyResponse: Transparency information about delegations

    Raises:
        ResourceNotFoundError: If poll not found
    """
    delegation_service = DelegationService(db)

    # Get all delegations for this poll
    delegations = await delegation_service.get_poll_delegations(poll_id)

    # Build delegation chains
    chains = []
    for delegation in delegations:
        try:
            chain = await delegation_service.resolve_delegation_chain(
                delegation.delegator_id, poll_id, include_path=True
            )
            chains.append(chain)
        except ValueError as e:
            logger.warning(
                "Failed to resolve delegation chain",
                extra={
                    "poll_id": poll_id,
                    "delegator_id": delegation.delegator_id,
                    "error": str(e),
                },
            )

    # Get statistics
    total_delegations = len(delegations)
    active_delegations = len([d for d in delegations if d.is_active])
    total_delegators = len(set(d.delegator_id for d in delegations))
    total_delegatees = len(set(d.delegatee_id for d in delegations))

    response = DelegationTransparencyResponse(
        poll_id=poll_id,
        total_delegations=total_delegations,
        active_delegations=active_delegations,
        total_delegators=total_delegators,
        total_delegatees=total_delegatees,
        delegation_chains=chains,
    )

    logger.info(
        "Retrieved delegation transparency",
        extra={
            "poll_id": poll_id,
            "total_delegations": total_delegations,
            "active_delegations": active_delegations,
        },
    )
    return response


@router.get("/stats", response_model=DelegationStatsResponse)
@handle_errors
async def get_delegation_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DelegationStatsResponse:
    """Get delegation statistics for the current user."""
    service = DelegationService(db)
    try:
        stats = await service.get_delegation_stats(current_user.id)
        return DelegationStatsResponse(**stats)
    except DelegationStatsError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/stats/invalidate")
async def invalidate_stats_cache(
    poll_id: Optional[UUID] = Query(
        None, description="Optional poll ID to invalidate stats for a specific poll"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Invalidate cached delegation statistics.

    Args:
        poll_id: Optional poll ID to invalidate stats for a specific poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        dict: Success message
    """
    delegation_service = DelegationService(db)
    await delegation_service.invalidate_stats_cache(poll_id)

    logger.info("Invalidated delegation statistics cache", extra={"poll_id": poll_id})
    return {"status": "success", "message": "Cache invalidated successfully"}


@router.post("/stats/cleanup")
async def cleanup_stats_cache(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Trigger cleanup of old delegation statistics.

    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Currently authenticated user

    Returns:
        dict: Success message
    """
    stats_task = StatsCalculationTask(db)
    background_tasks.add_task(stats_task.cleanup_old_stats)

    logger.info("Triggered background cleanup of old delegation stats")
    return {"status": "success", "message": "Cleanup task scheduled"}
