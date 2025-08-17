"""Delegation model with support for multiple modes and target types."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class DelegationMode(str, Enum):
    """Delegation modes supporting transition philosophy."""

    LEGACY_FIXED_TERM = "legacy_fixed_term"  # Old politics: 4y term, always revocable
    FLEXIBLE_DOMAIN = "flexible_domain"  # Commons: per-poll/label/field values
    HYBRID_SEED = "hybrid_seed"  # Hybrid: global fallback + per-field refinement


class Delegation(SQLAlchemyBase):
    """Delegation model with constitutional protections and mode support."""

    __tablename__ = "delegations"

    # Core delegation fields
    delegator_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    delegatee_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Mode and scope
    mode = Column(
        String(20),
        nullable=False,
        default=DelegationMode.FLEXIBLE_DOMAIN,
        server_default=DelegationMode.FLEXIBLE_DOMAIN,
    )
    is_anonymous = Column(Boolean, default=False, server_default="false")

    # Target scope (existing + new)
    poll_id = Column(GUID(), ForeignKey("polls.id", ondelete="CASCADE"), nullable=True)
    label_id = Column(
        GUID(), ForeignKey("labels.id", ondelete="SET NULL"), nullable=True
    )
    field_id = Column(
        GUID(), ForeignKey("fields.id", ondelete="SET NULL"), nullable=True
    )
    institution_id = Column(
        GUID(), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    # TODO: Implement values-as-delegates support
    value_id = Column(
        GUID(), ForeignKey("values.id", ondelete="SET NULL"), nullable=True
    )
    idea_id = Column(GUID(), ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)

    # Chain and transparency
    chain_origin_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Timing fields
    start_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_date = Column(DateTime(timezone=True), nullable=True)
    legacy_term_ends_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

    # Constitutional constraints
    __table_args__ = (
        # Legacy term constraint: must be ≤ start + 4y if mode=legacy_fixed_term
        CheckConstraint(
            "(mode != 'legacy_fixed_term') OR (legacy_term_ends_at IS NULL) OR "
            "(legacy_term_ends_at <= start_date + INTERVAL '4 years')",
            name="legacy_term_max_4y",
        ),
        # Partial index for active legacy delegations by expiry (for expiry scans)
        Index(
            "idx_legacy_active_by_expiry",
            "legacy_term_ends_at",
            "is_deleted",
            "revoked_at",
            postgresql_where="mode = 'legacy_fixed_term' AND is_deleted = false AND revoked_at IS NULL",
        ),
        # Composite index for fast override chain resolution
        Index(
            "idx_active_delegations_lookup",
            "delegator_id",
            "is_deleted",
            "revoked_at",
            "poll_id",
            "mode",
            "created_at",
            postgresql_where="is_deleted = false AND revoked_at IS NULL",
        ),
        # Index for delegatee lookups
        Index(
            "idx_active_delegatee_lookup",
            "delegatee_id",
            "is_deleted",
            "revoked_at",
            postgresql_where="is_deleted = false AND revoked_at IS NULL",
        ),
        # Index for chain origin tracking
        Index(
            "idx_chain_origin_active",
            "chain_origin_id",
            "is_deleted",
            "revoked_at",
            postgresql_where="is_deleted = false AND revoked_at IS NULL",
        ),
    )

    # Relationships
    delegator = relationship(
        "User", foreign_keys=[delegator_id], back_populates="delegations_as_delegator"
    )
    delegatee = relationship(
        "User", foreign_keys=[delegatee_id], back_populates="delegations_as_delegatee"
    )
    poll = relationship("Poll", back_populates="delegations")
    label = relationship("Label", back_populates="delegations")
    field = relationship("Field", back_populates="delegations")
    institution = relationship("Institution", back_populates="delegations")
    # TODO: Implement values-as-delegates relationships
    value = relationship("Value", back_populates="delegations")
    idea = relationship("Idea", back_populates="delegations")
    chain_origin = relationship("User", foreign_keys=[chain_origin_id])

    async def soft_delete(self, db_session) -> None:
        """Soft delete the delegation."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    @property
    def is_legacy_fixed_term(self) -> bool:
        """Check if this is a legacy fixed-term delegation."""
        return self.mode == DelegationMode.LEGACY_FIXED_TERM

    @property
    def is_expired(self) -> bool:
        """Check if legacy delegation has expired."""
        if not self.is_legacy_fixed_term or not self.legacy_term_ends_at:
            return False
        return datetime.utcnow() > self.legacy_term_ends_at

    @property
    def is_revocable(self) -> bool:
        """All delegations are revocable by constitutional principle."""
        return True

    @property
    def target_type(self) -> str:
        """Get the target type for this delegation."""
        if self.poll_id:
            return "poll"
        elif self.label_id:
            return "label"
        elif self.field_id:
            return "field"
        elif self.institution_id:
            return "institution"
        elif self.value_id:
            return "value"
        elif self.idea_id:
            return "idea"
        else:
            return "global"

    @property
    def is_active(self) -> bool:
        """Check if delegation is currently active."""
        if self.is_deleted or self.revoked_at is not None:
            return False

        now = datetime.utcnow()

        # Check start date
        if self.start_date and now < self.start_date:
            return False

        # Check end date
        if self.end_date and now > self.end_date:
            return False

        # Check legacy term expiry
        if (
            self.is_legacy_fixed_term
            and self.legacy_term_ends_at
            and now > self.legacy_term_ends_at
        ):
            return False

        return True
