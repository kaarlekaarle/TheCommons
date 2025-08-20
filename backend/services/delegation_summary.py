"""Safe delegation summary service with defensive error handling."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging_config import get_logger
from backend.models.delegation import Delegation
from backend.models.label import Label
from backend.models.user import User
from backend.services.delegation import DelegationService
from backend.utils.json import safe_json_response

logger = get_logger(__name__)


class SafeDelegationSummaryService:
    """Service for safely retrieving delegation summaries with comprehensive error handling."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.delegation_service = DelegationService(db)

    async def get_safe_summary(
        self, user_id: Optional[str], trace_id: str
    ) -> Dict[str, Any]:
        """
        Get delegation summary with comprehensive error handling.
        Never throws - always returns a structured response.
        """
        start_time = datetime.utcnow()
        errors = []

        # Short-circuit if no user
        if not user_id:
            return {
                "ok": False,
                "counts": {"mine": 0, "inbound": 0},
                "adoption": {"commons": 0, "legacy": 0},
                "meta": {
                    "errors": ["no_user"],
                    "trace_id": trace_id,
                    "generated_at": start_time.isoformat(),
                    "duration_ms": 0,
                },
            }

        try:
            # Get global delegation safely
            global_delegate_info = await self._get_global_delegation_safe(
                user_id, errors
            )

            # Get per-label delegations safely
            per_label_delegations = await self._get_label_delegations_safe(
                user_id, errors
            )

            # Calculate basic counts
            counts = {
                "mine": 1 if global_delegate_info else 0 + len(per_label_delegations),
                "inbound": 0,  # TODO: Implement inbound delegation count safely
            }

            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            response = {
                "ok": len(errors) == 0,
                "global_delegate": global_delegate_info,
                "per_label": per_label_delegations,
                "counts": counts,
                "meta": {
                    "errors": errors if errors else None,
                    "trace_id": trace_id,
                    "generated_at": start_time.isoformat(),
                    "duration_ms": round(duration_ms, 2),
                },
            }

            logger.info(
                "Generated delegation summary",
                extra={
                    "user_id": user_id,
                    "trace_id": trace_id,
                    "duration_ms": duration_ms,
                    "errors_count": len(errors),
                    "global_delegate": bool(global_delegate_info),
                    "label_delegations_count": len(per_label_delegations),
                },
            )

            return safe_json_response(response)

        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                "Catastrophic error in delegation summary",
                extra={
                    "user_id": user_id,
                    "trace_id": trace_id,
                    "error": str(e),
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )

            return {
                "ok": False,
                "counts": {"mine": 0, "inbound": 0},
                "meta": {
                    "errors": [f"catastrophic_error: {str(e)}"],
                    "trace_id": trace_id,
                    "generated_at": start_time.isoformat(),
                    "duration_ms": round(duration_ms, 2),
                },
            }

    async def _get_global_delegation_safe(
        self, user_id: str, errors: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Safely get global delegation info."""
        try:
            global_delegation = await self.delegation_service.get_active_delegation(
                user_id
            )

            if not global_delegation or global_delegation.label_id:
                return None

            # Fetch delegate info with bounded query
            delegate_result = await self.db.execute(
                select(User)
                .where(
                    and_(
                        User.id == global_delegation.delegatee_id,
                        User.is_deleted == False,
                    )
                )
                .limit(1)  # Safety limit
            )
            delegate = delegate_result.scalar_one_or_none()

            if not delegate:
                errors.append("global_delegate_user_not_found")
                return None

            return {
                "has_delegatee": True,
                "delegatee_id": str(delegate.id),
                "delegatee_username": delegate.username,
                "delegatee_email": delegate.email,
                "created_at": (
                    global_delegation.created_at.isoformat()
                    if global_delegation.created_at
                    else None
                ),
            }

        except Exception as e:
            errors.append(f"global_delegation_error: {str(e)}")
            logger.warning(
                "Error getting global delegation",
                extra={"user_id": user_id, "error": str(e)},
            )
            return None

    async def _get_label_delegations_safe(
        self, user_id: str, errors: List[str]
    ) -> List[Dict[str, Any]]:
        """Safely get label-specific delegations."""
        try:
            from backend.config import get_settings

            settings = get_settings()

            if not settings.LABELS_ENABLED:
                return []

            # Get label delegations with safety limits
            label_delegations_result = await self.db.execute(
                select(Delegation)
                .where(
                    and_(
                        Delegation.delegator_id == user_id,
                        Delegation.label_id.isnot(None),
                        Delegation.is_deleted == False,
                        Delegation.revoked_at.is_(None),
                    )
                )
                .limit(100)  # Safety limit to prevent runaway queries
            )
            label_delegations = label_delegations_result.scalars().all()

            safe_delegations = []

            for delegation in label_delegations:
                try:
                    # Get label info safely
                    label_result = await self.db.execute(
                        select(Label).where(Label.id == delegation.label_id).limit(1)
                    )
                    label = label_result.scalar_one_or_none()

                    # Get delegate info safely
                    delegate_result = await self.db.execute(
                        select(User)
                        .where(
                            and_(
                                User.id == delegation.delegatee_id,
                                User.is_deleted == False,
                            )
                        )
                        .limit(1)
                    )
                    delegate = delegate_result.scalar_one_or_none()

                    if label and delegate:
                        safe_delegations.append(
                            {
                                "label": {
                                    "id": str(label.id),
                                    "name": label.name,
                                    "slug": label.slug,
                                },
                                "delegate": {
                                    "id": str(delegate.id),
                                    "username": delegate.username,
                                    "email": delegate.email,
                                },
                                "created_at": (
                                    delegation.created_at.isoformat()
                                    if delegation.created_at
                                    else None
                                ),
                            }
                        )
                    else:
                        errors.append(f"label_delegation_incomplete: {delegation.id}")

                except Exception as e:
                    errors.append(f"label_delegation_item_error: {str(e)}")
                    logger.warning(
                        "Error processing label delegation",
                        extra={
                            "user_id": user_id,
                            "delegation_id": delegation.id,
                            "error": str(e),
                        },
                    )

            return safe_delegations

        except Exception as e:
            errors.append(f"label_delegations_error: {str(e)}")
            logger.warning(
                "Error getting label delegations",
                extra={"user_id": user_id, "error": str(e)},
            )
            return []
