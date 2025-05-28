import asyncio

import asyncpg

from backend.config import settings




def get_asyncpg_dsn():
    dsn = settings.DATABASE_URL
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    return dsn


async def validate_schema():
    """Validate the database schema and data."""
    # Connect to the database
    conn = await asyncpg.connect(get_asyncpg_dsn())

    try:
        # Get all tables
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
        print("Tables in database:", [table["table_name"] for table in tables])

        # Validate each table's structure
        for table in ["users", "polls", "options", "votes"]:
            print(f"\nValidating {table} table:")
            columns = await conn.fetch(
                f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
            """
            )
            for column in columns:
                print(
                    f"  - {column['column_name']}: "
                    f"{column['data_type']} "
                    f"(nullable: {column['is_nullable']})"
                )

        # Validate ENUM types
        print("\nValidating ENUM types:")
        poll_status_values = await conn.fetch(
            """
            SELECT DISTINCT status FROM polls
        """
        )
        print(
            "  - PollStatus values:",
            [row["status"] for row in poll_status_values]
        )

        poll_visibility_values = await conn.fetch(
            """
            SELECT DISTINCT visibility FROM polls
        """
        )
        print(
            "  - PollVisibility values:",
            [row["visibility"] for row in poll_visibility_values]
        )

        # Validate relationships
        print("\nValidating relationships:")
        # Check User -> Polls relationship
        user_polls = await conn.fetch(
            """
            SELECT u.id as user_id, COUNT(p.id) as poll_count
            FROM users u
            LEFT JOIN polls p ON u.id = p.created_by
            GROUP BY u.id
            LIMIT 1
        """
        )
        if user_polls:
            print(
                f"  - User {user_polls[0]['user_id']} has {user_polls[0]['poll_count']} polls"
            )

        # Check Poll -> Options relationship
        poll_options = await conn.fetch(
            """
            SELECT p.id as poll_id, COUNT(o.id) as option_count
            FROM polls p
            LEFT JOIN options o ON p.id = o.poll_id
            GROUP BY p.id
            LIMIT 1
        """
        )
        if poll_options:
            print(
                f"  - Poll {poll_options[0]['poll_id']} has {poll_options[0]['option_count']} options"
            )

        # Check Option -> Votes relationship
        option_votes = await conn.fetch(
            """
            SELECT o.id as option_id, COUNT(v.id) as vote_count
            FROM options o
            LEFT JOIN votes v ON o.id = v.option_id
            GROUP BY o.id
            LIMIT 1
        """
        )
        if option_votes:
            print(
                f"  - Option {option_votes[0]['option_id']} has {option_votes[0]['vote_count']} votes"
            )

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(validate_schema())
