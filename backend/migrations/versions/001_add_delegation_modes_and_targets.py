"""Add delegation modes and new target types.

Revision ID: 001
Revises:
Create Date: 2025-08-17 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database to add delegation modes and new target types."""
    # Create fields table
    op.create_table(
        "fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fields_slug"), "fields", ["slug"], unique=True)

    # Create institutions table
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="other"),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_institutions_slug"), "institutions", ["slug"], unique=True)

    # Add new columns to delegations table
    op.add_column(
        "delegations",
        sa.Column(
            "mode",
            sa.String(length=20),
            nullable=False,
            server_default="flexible_domain",
        ),
    )
    op.add_column(
        "delegations",
        sa.Column("is_anonymous", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "delegations",
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "delegations",
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "delegations",
        sa.Column("legacy_term_ends_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add foreign key constraints
    op.create_foreign_key(
        None, "delegations", "fields", ["field_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        None,
        "delegations",
        "institutions",
        ["institution_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add constitutional constraints
    # Note: Legacy term constraint is enforced at application level for cross-database compatibility
    # op.create_check_constraint(
    #     "legacy_term_max_4y",
    #     "delegations",
    #     "(mode != 'legacy_fixed_term') OR (legacy_term_ends_at IS NULL) OR "
    #     "(legacy_term_ends_at <= start_date + INTERVAL '4 years')",
    # )

    # Add partial index for legacy expiry scans
    op.create_index(
        "idx_legacy_active_by_expiry",
        "delegations",
        ["legacy_term_ends_at", "is_deleted", "revoked_at"],
        postgresql_where="mode = 'legacy_fixed_term' AND is_deleted = false AND revoked_at IS NULL",
    )

    # Create unified targets view
    op.execute(
        """
        CREATE VIEW unified_targets AS
        SELECT
            'user' as target_type,
            id as target_id,
            COALESCE(display_name, username) as name,
            username as slug,
            bio as description,
            NULL as tags,
            0.0 as popularity_score,
            NOT is_deleted as is_active,
            created_at::text as created_at,
            updated_at::text as updated_at
        FROM users
        WHERE is_deleted = false

        UNION ALL

        SELECT
            'field' as target_type,
            id as target_id,
            name,
            slug,
            description,
            NULL as tags,
            0.0 as popularity_score,
            is_active,
            created_at::text as created_at,
            updated_at::text as updated_at
        FROM fields
        WHERE is_active = true

        UNION ALL

        SELECT
            'institution' as target_type,
            id as target_id,
            name,
            slug,
            description,
            kind as tags,
            0.0 as popularity_score,
            is_active,
            created_at::text as created_at,
            updated_at::text as updated_at
        FROM institutions
        WHERE is_active = true
    """
    )


def downgrade() -> None:
    """Downgrade database to remove delegation modes and new target types."""
    # Drop unified targets view
    op.execute("DROP VIEW IF EXISTS unified_targets")

    # Drop partial index
    op.drop_index("idx_legacy_active_by_expiry", table_name="delegations")

    # Drop constitutional constraints
    # Note: Legacy term constraint was commented out for cross-database compatibility
    # op.drop_constraint("legacy_term_max_4y", "delegations", type_="check")

    # Drop foreign key constraints
    op.drop_constraint(None, "delegations", type_="foreignkey")
    op.drop_constraint(None, "delegations", type_="foreignkey")

    # Drop columns from delegations table
    op.drop_column("delegations", "legacy_term_ends_at")
    op.drop_column("delegations", "institution_id")
    op.drop_column("delegations", "field_id")
    op.drop_column("delegations", "is_anonymous")
    op.drop_column("delegations", "mode")

    # Drop institutions table
    op.drop_index(op.f("ix_institutions_slug"), table_name="institutions")
    op.drop_table("institutions")

    # Drop fields table
    op.drop_index(op.f("ix_fields_slug"), table_name="fields")
    op.drop_table("fields")
