from typing import Any, List, Optional
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Security, status, Request, Query
from sqlalchemy import and_, select, or_, func
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
from backend.models.delegation import Delegation, DelegationMode
from backend.models.field import Field
from backend.services.delegation_summary import SafeDelegationSummaryService
from backend.models.institution import Institution, InstitutionKind
from backend.models.user import User
from backend.models.label import Label
from backend.schemas.delegation import (
    DelegationCreate,
    DelegationInfo,
    DelegationResponse,
    DelegationSummary,
)
from backend.services.delegation import DelegationService, DelegationTarget
from backend.services.concentration_monitor import ConcentrationMonitorService
from backend.services.super_delegate_detector import SuperDelegateDetectorService
from backend.services.adoption_telemetry import AdoptionTelemetryService
from backend.config import get_settings
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(tags=["delegations"])


@router.get("/modes", response_model=dict)
async def get_delegation_modes(
    current_user: User = Security(get_current_active_user),
) -> dict:
    """Get server capabilities and defaults for delegation modes.
    
    Returns:
        dict: Server capabilities including enabled modes and feature flags
    """
    settings = get_settings()
    
    return {
        "modes": {
            "legacy_fixed_term": {
                "enabled": getattr(settings, "LEGACY_MODE_ENABLED", True),
                "description": "Old politics: 4-year term, always revocable",
                "max_term_years": 4,
                "default_term_years": 4,
            },
            "flexible_domain": {
                "enabled": True,  # Always enabled
                "description": "Commons: per-poll/label/field values",
                "default": True,
            },
            "hybrid_seed": {
                "enabled": True,  # Always enabled
                "description": "Hybrid: global fallback + per-field refinement",
            },
        },
        "targets": {
            "user": {"enabled": True},
            "field": {"enabled": getattr(settings, "UNIFIED_SEARCH_ENABLED", True)},
            "institution": {"enabled": getattr(settings, "INSTITUTIONS_ENABLED", True)},
            "value": {"enabled": True},  # Values-as-delegates
            "idea": {"enabled": True},   # Ideas-as-delegates
        },
        "features": {
            "unified_search": getattr(settings, "UNIFIED_SEARCH_ENABLED", True),
            "institutions": getattr(settings, "INSTITUTIONS_ENABLED", True),
            "legacy_mode": getattr(settings, "LEGACY_MODE_ENABLED", True),
            "anonymous_delegations": True,
        },
    }


@router.post("/", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
async def create_delegation(
    request: Request,
    delegation_in: DelegationCreate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Delegation:
    """Create a new delegation with mode support.

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
        "Creating new delegation with mode support",
        extra={"delegation_data": delegation_in.model_dump(), "user_id": current_user.id},
    )
    
    try:
        # Check if user is trying to delegate to themselves
        if delegation_in.delegatee_id == current_user.id:
            raise ValidationError("Cannot delegate to yourself")
        
        # Validate mode if provided
        mode = DelegationMode.FLEXIBLE_DOMAIN
        if hasattr(delegation_in, 'mode') and delegation_in.mode:
            try:
                mode = DelegationMode(delegation_in.mode)
            except ValueError:
                raise ValidationError(f"Invalid delegation mode: {delegation_in.mode}")
        
        # Handle target specification
        target = None
        if hasattr(delegation_in, 'target') and delegation_in.target:
            target = DelegationTarget(
                target_type=delegation_in.target.get('type'),
                target_id=delegation_in.target.get('id')
            )
        
        # Resolve target IDs based on target specification
        poll_id = None
        label_id = None
        field_id = None
        institution_id = None
        value_id = None
        idea_id = None
        
        if target:
            if target.type == 'poll':
                poll_id = target.id
            elif target.type == 'label':
                # Find label by slug or ID
                if hasattr(delegation_in, 'label_slug') and delegation_in.label_slug:
                    label_result = await db.execute(
                        select(Label).where(
                            and_(
                                Label.slug == delegation_in.label_slug,
                                Label.is_active == True,
                                Label.is_deleted == False
                            )
                        )
                    )
                    label = label_result.scalar_one_or_none()
                    if not label:
                        raise ValidationError(f"Label with slug '{delegation_in.label_slug}' not found")
                    label_id = label.id
            elif target.type == 'field':
                field_id = target.id
            elif target.type == 'institution':
                institution_id = target.id
            elif target.type == 'value':
                value_id = target.id
            elif target.type == 'idea':
                idea_id = target.id
        
        # Check for warnings before creating delegation
        warnings = {}
        
        # Check concentration
        concentration_monitor = ConcentrationMonitorService(db)
        is_high_conc, conc_level, conc_percent = await concentration_monitor.is_high_concentration(
            delegation_in.delegatee_id, field_id
        )
        if is_high_conc:
            warnings["concentration"] = {
                "active": True,
                "level": conc_level,
                "percent": conc_percent
            }
        else:
            warnings["concentration"] = {
                "active": False,
                "level": "",
                "percent": conc_percent
            }
        
        # Check super-delegate risk
        super_delegate_detector = SuperDelegateDetectorService(db)
        super_risk, super_reason, super_stats = await super_delegate_detector.would_create_super_delegate(
            delegation_in.delegatee_id, field_id
        )
        if super_risk:
            warnings["superDelegateRisk"] = {
                "active": True,
                "reason": super_reason,
                "stats": super_stats
            }
        else:
            warnings["superDelegateRisk"] = {
                "active": False,
                "reason": super_reason,
                "stats": super_stats
            }
        
        # Use delegation service for creation
        delegation_service = DelegationService(db)
        
        delegation = await delegation_service.create_delegation(
            delegator_id=current_user.id,
            delegatee_id=delegation_in.delegatee_id,
            mode=mode,
            target=target,
            poll_id=poll_id,
            label_id=label_id,
            field_id=field_id,
            institution_id=institution_id,
            value_id=value_id,
            idea_id=idea_id,
            is_anonymous=getattr(delegation_in, 'is_anonymous', False),
            legacy_term_ends_at=getattr(delegation_in, 'legacy_term_ends_at', None),
        )
        
        await db.commit()
        
        # Track adoption telemetry
        try:
            telemetry_service = AdoptionTelemetryService(db)
            context = {
                "target_type": delegation.target_type,
                "field_id": str(field_id) if field_id else None,
                "has_warnings": bool(warnings.get("concentration", {}).get("active") or warnings.get("superDelegateRisk", {}).get("active"))
            }
            await telemetry_service.track_delegation_mode(current_user.id, mode, context)
        except Exception as e:
            logger.warning(f"Failed to track adoption telemetry: {e}")
        
        logger.info(
            "Delegation created successfully with mode support",
            extra={
                "delegation_id": delegation.id, 
                "user_id": current_user.id,
                "mode": mode,
                "target_type": delegation.target_type,
            },
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
                "mode": delegation.mode,
                "target_type": delegation.target_type,
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
                "mode": delegation.mode,
                "target_type": delegation.target_type,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast delegation creation", extra={"error": str(e)})
        
        # Return enhanced response with warnings
        return {
            "delegation": {
                "id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
                "mode": delegation.mode,
                "target_type": delegation.target_type,
                "is_anonymous": delegation.is_anonymous,
                "legacy_term_ends_at": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
                "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None
            },
            "warnings": warnings
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to create delegation with mode support",
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
        service = DelegationService(db)
        
        # Revoke the user's delegation using the service
        await service.revoke_user_delegation(current_user.id)
        await db.commit()
        
        logger.info(
            "Delegation revoked successfully",
            extra={"user_id": current_user.id},
        )
        
        # Track delegation revocation metric
        increment_delegation_metric("delegation_revoked", str(current_user.id))
        
        # Audit the delegation removal
        audit_event(
            "delegation_removed",
            {
                "delegator_id": str(current_user.id),
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
        service = DelegationService(db)
        
        # Get active delegation using service (checks both is_deleted and revoked_at)
        delegation = await service.get_active_delegation(current_user.id)
        
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


@router.get("/me/summary", response_model=DelegationSummary)
async def get_my_delegation_summary(
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DelegationSummary:
    """Get the current user's delegation summary including global and label-specific delegations.

    Args:
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        DelegationSummary: User's delegation summary
    """
    settings = get_settings()
    logger.info(
        "Getting user delegation summary",
        extra={"user_id": current_user.id},
    )
    
    try:
        service = DelegationService(db)
        
        # Get global delegation
        global_delegation = await service.get_active_delegation(current_user.id)
        global_delegate_info = None
        
        if global_delegation and not global_delegation.label_id:
            # Fetch delegate info for global delegation
            delegate_result = await db.execute(
                select(User).where(
                    and_(
                        User.id == global_delegation.delegatee_id,
                        User.is_deleted == False
                    )
                )
            )
            delegate = delegate_result.scalar_one_or_none()
            
            if delegate:
                global_delegate_info = DelegationInfo(
                    has_delegatee=True,
                    delegatee_id=delegate.id,
                    delegatee_username=delegate.username,
                    delegatee_email=delegate.email,
                    created_at=global_delegation.created_at
                )
        
        # Get label-specific delegations
        per_label_delegations = []
        if settings.LABELS_ENABLED:
            label_delegations_result = await db.execute(
                select(Delegation).where(
                    and_(
                        Delegation.delegator_id == current_user.id,
                        Delegation.label_id.isnot(None),
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None)
                    )
                )
            )
            label_delegations = label_delegations_result.scalars().all()
            
            for delegation in label_delegations:
                # Get label info
                label_result = await db.execute(
                    select(Label).where(Label.id == delegation.label_id)
                )
                label = label_result.scalar_one_or_none()
                
                # Get delegate info
                delegate_result = await db.execute(
                    select(User).where(
                        and_(
                            User.id == delegation.delegatee_id,
                            User.is_deleted == False
                        )
                    )
                )
                delegate = delegate_result.scalar_one_or_none()
                
                if label and delegate:
                    per_label_delegations.append({
                        "label": {
                            "id": str(label.id),
                            "name": label.name,
                            "slug": label.slug
                        },
                        "delegate": {
                            "id": str(delegate.id),
                            "username": delegate.username,
                            "email": delegate.email
                        },
                        "created_at": delegation.created_at.isoformat() if delegation.created_at else None
                    })
        
        return DelegationSummary(
            global_delegate=global_delegate_info,
            per_label=per_label_delegations
        )
        
    except Exception as e:
        logger.error(
            "Failed to get user delegation summary",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get delegation summary")


@router.get("/summary", response_model=dict)
async def get_safe_delegation_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> dict:
    """
    Get delegation summary with comprehensive error handling and observability.
    Always returns 200 with ok flag and meta information.
    """
    trace_id = str(uuid.uuid4())
    
    # Add trace_id to request for downstream logging
    request.state.trace_id = trace_id
    
    # Try to get current user, but don't fail if unauthenticated
    current_user = None
    if token:
        try:
            from backend.core.auth import get_current_active_user
            # Try to get user, but don't fail the request if authentication fails
            current_user = await get_current_active_user(token, db)
        except Exception:
            # User is not authenticated, continue with None
            pass
    
    logger.info(
        "Safe delegation summary requested",
        extra={
            "trace_id": trace_id,
            "user_id": current_user.id if current_user else None,
            "authenticated": bool(current_user)
        }
    )
    
    try:
        service = SafeDelegationSummaryService(db)
        user_id = str(current_user.id) if current_user else None
        
        summary = await service.get_safe_summary(user_id, trace_id)
        
        logger.info(
            "Safe delegation summary completed",
            extra={
                "trace_id": trace_id,
                "user_id": user_id,
                "ok": summary.get("ok", False),
                "error_count": len(summary.get("meta", {}).get("errors", [])),
                "duration_ms": summary.get("meta", {}).get("duration_ms", 0)
            }
        )
        
        return summary
        
    except Exception as e:
        logger.error(
            "Catastrophic error in safe delegation summary endpoint",
            extra={
                "trace_id": trace_id,
                "user_id": current_user.id if current_user else None,
                "error": str(e)
            },
            exc_info=True
        )
        
        # Always return 200 with error information
        return {
            "ok": False,
            "counts": {"mine": 0, "inbound": 0},
            "meta": {
                "errors": [f"endpoint_error: {str(e)}"],
                "trace_id": trace_id,
                "generated_at": "error"
            }
        }


@router.get("/my", response_model=List[dict])
async def get_my_delegations(
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get current user's delegations with mode information.
    
    Returns:
        List[dict]: User's delegations with mode, legacy_term_ends_at, and chain_trace
    """
    try:
        query = select(Delegation).where(
            and_(
                Delegation.delegator_id == current_user.id,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
            )
        ).order_by(Delegation.created_at.desc())
        
        result = await db.execute(query)
        delegations = result.scalars().all()
        
        # Get chain trace for each delegation
        delegation_service = DelegationService(db)
        
        response = []
        for delegation in delegations:
            # Resolve chain trace
            chain = await delegation_service.resolve_delegation_chain(
                user_id=delegation.delegator_id,
                poll_id=delegation.poll_id,
                label_id=delegation.label_id,
                field_id=delegation.field_id,
                institution_id=delegation.institution_id,
                value_id=delegation.value_id,
                idea_id=delegation.idea_id,
            )
            
            chain_trace = []
            for chain_delegation in chain:
                chain_trace.append({
                    "delegation_id": str(chain_delegation.id),
                    "delegator_id": str(chain_delegation.delegator_id),
                    "delegatee_id": str(chain_delegation.delegatee_id),
                    "mode": chain_delegation.mode,
                    "target_type": chain_delegation.target_type,
                    "is_expired": chain_delegation.is_expired,
                })
            
            response.append({
                "id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
                "mode": delegation.mode,
                "target_type": delegation.target_type,
                "is_anonymous": delegation.is_anonymous,
                "legacy_term_ends_at": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None,
                "is_expired": delegation.is_expired,
                "chain_trace": chain_trace,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
                "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None,
            })
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to get user delegations",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get user delegations")


@router.post("/{delegation_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_delegation(
    delegation_id: UUID,
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke a delegation.
    
    All delegations are revocable by constitutional principle, regardless of mode.
    
    Args:
        delegation_id: ID of the delegation to revoke
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        dict: Success message
    """
    try:
        delegation_service = DelegationService(db)
        await delegation_service.revoke_delegation(delegation_id)
        await db.commit()
        
        logger.info(
            f"Delegation {delegation_id} revoked successfully",
            extra={
                "delegation_id": str(delegation_id),
                "user_id": current_user.id,
            },
        )
        
        return {"message": "Delegation revoked successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Failed to revoke delegation {delegation_id}",
            extra={"delegation_id": str(delegation_id), "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to revoke delegation")


@router.get("/search/unified", response_model=List[dict])
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    types: str = Query("people,fields,institutions", description="Comma-separated list of target types"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Unified search across people, fields, and institutions.
    
    Args:
        q: Search query
        types: Comma-separated list of target types to search
        limit: Maximum number of results
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List[dict]: Search results with normalized shape
    """
    try:
        target_types = [t.strip() for t in types.split(",")]
        results = []
        
        # Search users (people)
        if "people" in target_types:
            user_query = select(User).where(
                and_(
                    User.is_deleted == False,
                    or_(
                        User.username.ilike(f"%{q}%"),
                        User.display_name.ilike(f"%{q}%"),
                        User.bio.ilike(f"%{q}%") if User.bio else False,
                    )
                )
            ).limit(limit)
            
            user_result = await db.execute(user_query)
            users = user_result.scalars().all()
            
            for user in users:
                results.append({
                    "type": "user",
                    "id": str(user.id),
                    "name": user.display_name or user.username,
                    "slug": user.username,
                    "description": user.bio,
                    "meta": {
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                    }
                })
        
        # Search fields
        if "fields" in target_types:
            field_query = select(Field).where(
                and_(
                    Field.is_active == True,
                    or_(
                        Field.name.ilike(f"%{q}%"),
                        Field.slug.ilike(f"%{q}%"),
                        Field.description.ilike(f"%{q}%") if Field.description else False,
                    )
                )
            ).limit(limit)
            
            field_result = await db.execute(field_query)
            fields = field_result.scalars().all()
            
            for field in fields:
                results.append({
                    "type": "field",
                    "id": str(field.id),
                    "name": field.name,
                    "slug": field.slug,
                    "description": field.description,
                    "meta": {
                        "created_at": field.created_at.isoformat() if field.created_at else None,
                    }
                })
        
        # Search institutions
        if "institutions" in target_types:
            institution_query = select(Institution).where(
                and_(
                    Institution.is_active == True,
                    or_(
                        Institution.name.ilike(f"%{q}%"),
                        Institution.slug.ilike(f"%{q}%"),
                        Institution.description.ilike(f"%{q}%") if Institution.description else False,
                    )
                )
            ).limit(limit)
            
            institution_result = await db.execute(institution_query)
            institutions = institution_result.scalars().all()
            
            for institution in institutions:
                results.append({
                    "type": "institution",
                    "id": str(institution.id),
                    "name": institution.name,
                    "slug": institution.slug,
                    "description": institution.description,
                    "meta": {
                        "kind": institution.kind,
                        "url": institution.url,
                        "created_at": institution.created_at.isoformat() if institution.created_at else None,
                    }
                })
        
        # Sort by relevance (simple: exact matches first, then partial)
        def relevance_score(item):
            name = item["name"].lower()
            query = q.lower()
            if name == query:
                return 3
            elif name.startswith(query):
                return 2
            elif query in name:
                return 1
            return 0
        
        results.sort(key=relevance_score, reverse=True)
        
        return results[:limit]
        
    except Exception as e:
        logger.error(
            "Failed to perform unified search",
            extra={"query": q, "types": types, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to perform unified search")


@router.get("/telemetry/adoption", response_model=dict)
async def get_adoption_telemetry(
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get adoption telemetry for delegation modes.
    
    This endpoint provides aggregate counts by mode over time for transition tracking.
    
    Returns:
        dict: Adoption statistics by mode
    """
    try:
        # Count delegations by mode
        mode_counts_query = select(
            Delegation.mode,
            func.count(Delegation.id).label('count')
        ).where(
            and_(
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
            )
        ).group_by(Delegation.mode)
        
        result = await db.execute(mode_counts_query)
        mode_counts = {row.mode: row.count for row in result}
        
        # Calculate percentages
        total_delegations = sum(mode_counts.values())
        mode_percentages = {}
        if total_delegations > 0:
            mode_percentages = {
                mode: (count / total_delegations) * 100 
                for mode, count in mode_counts.items()
            }
        
        # Count users in hybrid mode (have both global and specific delegations)
        hybrid_users_query = select(func.count(func.distinct(Delegation.delegator_id))).where(
            and_(
                Delegation.mode == DelegationMode.HYBRID_SEED,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
            )
        )
        
        result = await db.execute(hybrid_users_query)
        hybrid_users_count = result.scalar() or 0
        
        return {
            "mode_counts": mode_counts,
            "mode_percentages": mode_percentages,
            "total_delegations": total_delegations,
            "hybrid_users_count": hybrid_users_count,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(
            "Failed to get adoption telemetry",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get adoption telemetry")


@router.get("/me/chain", response_model=dict)
async def get_my_delegation_chain(
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's outbound delegation chain(s) by field.
    
    Returns:
        dict: Delegation chains organized by field with display names
    """
    try:
        # Get user's active delegations
        delegations_query = select(Delegation).where(
            and_(
                Delegation.delegator_id == current_user.id,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
                Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
            )
        )
        
        result = await db.execute(delegations_query)
        user_delegations = result.scalars().all()
        
        # Group by field
        chains = {}
        field_counts = {}
        
        for delegation in user_delegations:
            field_id = str(delegation.field_id) if delegation.field_id else "global"
            
            if field_id not in chains:
                chains[field_id] = {
                    "fieldId": delegation.field_id,
                    "fieldName": None,  # Will be populated if field exists
                    "path": []
                }
                field_counts[field_id] = 0
            
            field_counts[field_id] += 1
            
            # Get delegatee info
            delegatee_result = await db.execute(
                select(User).where(User.id == delegation.delegatee_id)
            )
            delegatee = delegatee_result.scalar_one_or_none()
            
            # Get field info if it exists
            field_name = None
            if delegation.field_id:
                field_result = await db.execute(
                    select(Field).where(Field.id == delegation.field_id)
                )
                field = field_result.scalar_one_or_none()
                if field:
                    field_name = field.name or field.slug
                    chains[field_id]["fieldName"] = field_name
            
            if delegatee:
                chains[field_id]["path"].append({
                    "delegator": str(delegation.delegator_id),
                    "delegatorName": current_user.username,  # Current user is always delegator
                    "delegatee": str(delegation.delegatee_id),
                    "delegateeName": delegatee.username,
                    "mode": delegation.mode,
                    "startsAt": delegation.start_date.isoformat() if delegation.start_date else None,
                    "endsAt": delegation.end_date.isoformat() if delegation.end_date else None,
                    "legacyTermEndsAt": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None
                })
        
        return {
            "chains": list(chains.values()),
            "totalChains": len(chains),
            "summary": {
                "totalDelegations": sum(field_counts.values()),
                "byField": field_counts
            }
        }
        
    except Exception as e:
        logger.error(
            "Failed to get user delegation chain",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get delegation chain")


@router.get("/{delegatee_id}/inbound", response_model=dict)
async def get_delegatee_inbound_delegations(
    delegatee_id: UUID,
    field_id: Optional[UUID] = Query(None, description="Optional field ID to filter by"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get who has delegated to a specific person.
    
    Args:
        delegatee_id: ID of the delegatee to check
        field_id: Optional field ID to filter by
        limit: Maximum number of results to return
        cursor: Cursor for pagination
        
    Returns:
        dict: Inbound delegations and counts with pagination
    """
    try:
        # Build base query
        base_query = select(Delegation).where(
            and_(
                Delegation.delegatee_id == delegatee_id,
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
                Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
            )
        )
        
        # Add field filter if provided
        if field_id:
            base_query = base_query.where(Delegation.field_id == field_id)
        
        # Add pagination if cursor provided
        if cursor:
            try:
                cursor_date = datetime.fromisoformat(cursor)
                base_query = base_query.where(Delegation.created_at < cursor_date)
            except ValueError:
                # Invalid cursor, ignore it
                pass
        
        # Order by creation date for consistent pagination
        base_query = base_query.order_by(Delegation.created_at.desc())
        
        # Get delegations with limit + 1 to check if there are more
        result = await db.execute(base_query.limit(limit + 1))
        delegations = result.scalars().all()
        
        # Check if there are more results
        has_more = len(delegations) > limit
        if has_more:
            delegations = delegations[:-1]  # Remove the extra item
        
        # Get delegatee info
        delegatee_result = await db.execute(
            select(User).where(User.id == delegatee_id)
        )
        delegatee = delegatee_result.scalar_one_or_none()
        
        if not delegatee:
            raise ResourceNotFoundError(f"Delegatee {delegatee_id} not found")
        
        # Build response
        inbound = []
        field_counts = {}
        field_names = {}
        
        for delegation in delegations:
            # Get delegator info
            delegator_result = await db.execute(
                select(User).where(User.id == delegation.delegator_id)
            )
            delegator = delegator_result.scalar_one_or_none()
            
            # Get field info if it exists
            field_name = None
            if delegation.field_id:
                field_result = await db.execute(
                    select(Field).where(Field.id == delegation.field_id)
                )
                field = field_result.scalar_one_or_none()
                if field:
                    field_name = field.name or field.slug
                    field_names[str(delegation.field_id)] = field_name
            
            inbound_item = {
                "delegatorId": str(delegation.delegator_id),
                "delegatorName": delegator.username if delegator else "Unknown",
                "fieldId": str(delegation.field_id) if delegation.field_id else None,
                "fieldName": field_name,
                "mode": delegation.mode,
                "createdAt": delegation.created_at.isoformat() if delegation.created_at else None,
                "expiresAt": delegation.end_date.isoformat() if delegation.end_date else None,
                "legacyTermEndsAt": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None
            }
            inbound.append(inbound_item)
            
            # Count by field
            field_key = str(delegation.field_id) if delegation.field_id else "global"
            field_counts[field_key] = field_counts.get(field_key, 0) + 1
        
        # Get total count
        total_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_count = total_result.scalar() or 0
        
        # Get top 3 fields by count
        top_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_fields_with_names = []
        for field_id, count in top_fields:
            if field_id == "global":
                top_fields_with_names.append({"fieldId": field_id, "fieldName": "Global", "count": count})
            else:
                field_name = field_names.get(field_id, field_id)
                top_fields_with_names.append({"fieldId": field_id, "fieldName": field_name, "count": count})
        
        # Prepare next cursor
        next_cursor = None
        if has_more and delegations:
            next_cursor = delegations[-1].created_at.isoformat()
        
        return {
            "delegateeId": str(delegatee_id),
            "delegateeName": delegatee.username,
            "inbound": inbound,
            "counts": {
                "total": total_count,
                "byField": field_counts
            },
            "summary": {
                "totalInbound": total_count,
                "topFields": top_fields_with_names
            },
            "pagination": {
                "hasMore": has_more,
                "nextCursor": next_cursor,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(
            "Failed to get inbound delegations",
            extra={"delegatee_id": delegatee_id, "error": str(e)},
            exc_info=True,
        )
        if isinstance(e, ResourceNotFoundError):
            raise
        raise ServerError("Failed to get inbound delegations")


@router.get("/health/summary", response_model=dict)
async def get_delegation_health_summary(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of top delegatees to return"),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get lightweight transparency summary of delegation patterns.
    
    Args:
        limit: Maximum number of top delegatees to return per category
        
    Returns:
        dict: Summary of delegation patterns and top delegatees
    """
    try:
        # Get top delegatees globally
        top_delegatees_query = select(
            Delegation.delegatee_id,
            func.count(Delegation.id).label('count')
        ).where(
            and_(
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
                Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
            )
        ).group_by(Delegation.delegatee_id).order_by(
            func.count(Delegation.id).desc()
        ).limit(limit)
        
        result = await db.execute(top_delegatees_query)
        top_delegatees_data = result.fetchall()
        
        # Get total delegations for percentage calculation
        total_result = await db.execute(
            select(func.count(Delegation.id)).where(
                and_(
                    Delegation.is_deleted == False,
                    Delegation.revoked_at.is_(None),
                    Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow())
                )
            )
        )
        total_delegations = total_result.scalar() or 0
        
        # Build top delegatees list
        top_delegatees = []
        for delegatee_id, count in top_delegatees_data:
            # Get delegatee info
            delegatee_result = await db.execute(
                select(User).where(User.id == delegatee_id)
            )
            delegatee = delegatee_result.scalar_one_or_none()
            
            percent = (count / total_delegations * 100) if total_delegations > 0 else 0
            
            top_delegatees.append({
                "id": str(delegatee_id),
                "name": delegatee.username if delegatee else "Unknown",
                "count": count,
                "percent": round(percent, 2)
            })
        
        # Get top delegatees by field
        by_field_query = select(
            Delegation.field_id,
            Delegation.delegatee_id,
            func.count(Delegation.id).label('count')
        ).where(
            and_(
                Delegation.is_deleted == False,
                Delegation.revoked_at.is_(None),
                Delegation.end_date.is_(None) | (Delegation.end_date > datetime.utcnow()),
                Delegation.field_id.is_not(None)
            )
        ).group_by(Delegation.field_id, Delegation.delegatee_id).order_by(
            Delegation.field_id,
            func.count(Delegation.id).desc()
        )
        
        result = await db.execute(by_field_query)
        by_field_data = result.fetchall()
        
        # Group by field
        by_field = {}
        for field_id, delegatee_id, count in by_field_data:
            field_key = str(field_id)
            if field_key not in by_field:
                by_field[field_key] = []
            
            # Get delegatee info
            delegatee_result = await db.execute(
                select(User).where(User.id == delegatee_id)
            )
            delegatee = delegatee_result.scalar_one_or_none()
            
            # Get field info
            field_result = await db.execute(
                select(Field).where(Field.id == field_id)
            )
            field = field_result.scalar_one_or_none()
            
            by_field[field_key].append({
                "id": str(delegatee_id),
                "name": delegatee.username if delegatee else "Unknown",
                "count": count,
                "fieldName": field.name if field else "Unknown Field"
            })
        
        # Limit top delegatees per field
        for field_key in by_field:
            by_field[field_key] = by_field[field_key][:limit]
        
        return {
            "topDelegatees": top_delegatees,
            "byField": by_field,
            "totalDelegations": total_delegations,
            "generatedAt": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Failed to get delegation health summary",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get delegation health summary")


@router.get("/adoption/stats", response_model=dict)
async def get_adoption_stats(
    days: int = Query(14, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get adoption statistics for delegation modes.
    
    Args:
        days: Number of days to look back for statistics
        
    Returns:
        dict: Adoption statistics including mode usage and transitions
    """
    try:
        telemetry_service = AdoptionTelemetryService(db)
        stats = await telemetry_service.get_adoption_stats(days)
        return stats
        
    except Exception as e:
        logger.error(
            "Failed to get adoption stats",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to get adoption stats")
