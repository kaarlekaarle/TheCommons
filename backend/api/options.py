from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user
from backend.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
)
from backend.core.logging_config import get_logger
from backend.database import get_db
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.schemas.option import Option as OptionSchema
from backend.schemas.option import OptionCreate, OptionUpdate

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=OptionSchema, status_code=status.HTTP_201_CREATED)
async def create_option(
    option: OptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Option:
    """Create a new option for a poll.

    Args:
        option: Option creation data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Option: Created option

    Raises:
        ResourceNotFoundError: If poll not found
        AuthorizationError: If user is not poll creator
        ValidationError: If option data is invalid
    """
    # Verify the poll exists and belongs to the current user
    result = await db.execute(select(Poll).where(Poll.id == option.poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        logger.warning("Poll not found", extra={"poll_id": option.poll_id})
        raise ResourceNotFoundError("Poll not found")
    if poll.created_by != current_user.id:
        logger.warning(
            "Unauthorized poll access",
            extra={"poll_id": option.poll_id, "user_id": current_user.id},
        )
        raise AuthorizationError("Not enough permissions")

    try:
        db_option = Option(**option.model_dump())
        db.add(db_option)
        await db.commit()
        await db.refresh(db_option)

        logger.info(
            "Option created successfully",
            extra={"option_id": db_option.id, "poll_id": option.poll_id},
        )
        return db_option
    except Exception as e:
        logger.error(
            "Failed to create option",
            extra={"poll_id": option.poll_id, "error": str(e)},
            exc_info=True,
        )
        raise ValidationError("Invalid option data")


@router.get("/{option_id}", response_model=OptionSchema)
async def get_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Option:
    """Get an option by ID.

    Args:
        option_id: ID of the option
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Option: Requested option

    Raises:
        ResourceNotFoundError: If option not found
    """
    result = await db.execute(select(Option).where(Option.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        logger.warning("Option not found", extra={"option_id": option_id, "user_id": current_user.id})
        raise ResourceNotFoundError("Option not found")
    
    logger.info(
        "Retrieved option", 
        extra={"option_id": option_id, "user_id": current_user.id}
    )
    return option


@router.get("/poll/{poll_id}", response_model=List[OptionSchema])
async def get_poll_options(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Option]:
    """Get all options for a poll.

    Args:
        poll_id: ID of the poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List[Option]: List of options for the poll

    Raises:
        ResourceNotFoundError: If poll not found
    """
    # Verify poll exists
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        logger.warning("Poll not found", extra={"poll_id": poll_id, "user_id": current_user.id})
        raise ResourceNotFoundError("Poll not found")

    result = await db.execute(
        select(Option).where(
            Option.poll_id == poll_id
            if poll_id is not None
            else Option.poll_id.is_(None)
        )
    )
    options = result.scalars().all()

    logger.info(
        "Retrieved poll options",
        extra={
            "poll_id": poll_id, 
            "option_count": len(options),
            "user_id": current_user.id
        },
    )
    return options


@router.put("/{option_id}", response_model=OptionSchema)
async def update_option(
    option_id: int,
    option_update: OptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Option:
    """Update an option.

    Args:
        option_id: ID of the option to update
        option_update: Updated option data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Option: Updated option

    Raises:
        ResourceNotFoundError: If option or poll not found
        AuthorizationError: If user is not poll creator
        ValidationError: If update data is invalid
    """
    result = await db.execute(select(Option).where(Option.id == option_id))
    db_option = result.scalar_one_or_none()
    if not db_option:
        logger.warning("Option not found", extra={"option_id": option_id})
        raise ResourceNotFoundError("Option not found")

    # Verify the poll belongs to the current user
    result = await db.execute(select(Poll).where(Poll.id == db_option.poll_id))
    poll = result.scalar_one_or_none()
    if not poll or poll.created_by != current_user.id:
        logger.warning(
            "Unauthorized poll access",
            extra={"poll_id": db_option.poll_id, "user_id": current_user.id},
        )
        raise AuthorizationError("Not enough permissions")

    try:
        for field, value in option_update.model_dump(exclude_unset=True).items():
            setattr(db_option, field, value)

        await db.commit()
        await db.refresh(db_option)

        logger.info("Option updated successfully", extra={"option_id": option_id})
        return db_option
    except Exception as e:
        logger.error(
            "Failed to update option",
            extra={"option_id": option_id, "error": str(e)},
            exc_info=True,
        )
        raise ValidationError("Invalid update data")


@router.delete("/{option_id}")
async def delete_option(
    option_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Delete an option.

    Args:
        option_id: ID of the option to delete
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Dict[str, str]: Success message

    Raises:
        ResourceNotFoundError: If option or poll not found
        AuthorizationError: If user is not poll creator
    """
    result = await db.execute(select(Option).where(Option.id == option_id))
    db_option = result.scalar_one_or_none()
    if not db_option:
        logger.warning("Option not found", extra={"option_id": option_id})
        raise ResourceNotFoundError("Option not found")

    # Verify the poll belongs to the current user
    result = await db.execute(select(Poll).where(Poll.id == db_option.poll_id))
    poll = result.scalar_one_or_none()
    if not poll or poll.created_by != current_user.id:
        logger.warning(
            "Unauthorized poll access",
            extra={"poll_id": db_option.poll_id, "user_id": current_user.id},
        )
        raise AuthorizationError("Not enough permissions")

    await db.delete(db_option)
    await db.commit()

    logger.info("Option deleted successfully", extra={"option_id": option_id})
    return {"message": "Option deleted successfully"}
