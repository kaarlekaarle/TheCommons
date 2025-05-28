from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user
from backend.core.exceptions import AuthenticationError, ServerError
from backend.core.logging_config import get_logger
from backend.database import get_db
from backend.models.user import User
from backend.schemas.token import Token
from backend.schemas.user import UserResponse
from backend.services.user import UserService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login endpoint to get access token.

    Args:
        request: FastAPI request object
        form_data: Login form data containing username and password
        db: Database session

    Returns:
        Token: Access token data

    Raises:
        AuthenticationError: If authentication fails
        ServerError: If an unexpected error occurs
    """
    user_service = UserService(db)
    try:
        user = await user_service.authenticate_user(
            form_data.username, form_data.password
        )
        access_token = await user_service.create_access_token(user)
        token = Token(access_token=access_token, token_type="bearer")

        # Store user ID in session
        # request.state.session["user_id"] = user.id

        logger.info(
            "User logged in successfully",
            extra={"user_id": user.id, "username": user.username},
        )
        return token
    except AuthenticationError as e:
        logger.warning(
            "Login failed", extra={"username": form_data.username, "error": str(e)}
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during login",
            extra={"username": form_data.username, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to authenticate user")


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    request: Request, current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user information.

    Args:
        request: FastAPI request object
        current_user: Currently authenticated user

    Returns:
        User: Current user information
    """
    # Verify session matches current user
    session_user_id = request.state.session.get("user_id")
    if session_user_id != current_user.id:
        raise AuthenticationError("Invalid session")

    logger.info("Retrieved current user", extra={"user_id": current_user.id})
    return current_user
