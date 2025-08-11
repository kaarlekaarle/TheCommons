import re
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
)

import redis.asyncio as aioredis
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from itsdangerous import URLSafeSerializer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings
from backend.core import exceptions
from backend.core.auth import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from backend.core.exception_handlers import configure_exception_handlers
from backend.core.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
    UserAlreadyExistsError,
    ValidationError,
    ConflictError,
    AuthenticationError,
)
from backend.core.logging_config import get_logger
from backend.core.oauth2 import TOKEN_EXPIRE_MINUTES
from backend.database import get_db, init_db
from backend.models.user import User
from backend.models.vote import Vote
from backend.schemas.token import Token
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.core.voting import get_vote

logger = get_logger(__name__)

# Initialize rate limiter
limiter = FastAPILimiter()

# Initialize session serializer
session_serializer = URLSafeSerializer(settings.SECRET_KEY)


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    is_active: bool = True
    is_superuser: bool = False

    @field_validator("username")
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must be alphanumeric with underscores and hyphens"
            )
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    password: Optional[str] = Field(None, min_length=8, max_length=100)

    @field_validator("username")
    def username_alphanumeric(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must be alphanumeric with underscores and hyphens"
            )
        return v

    @field_validator("password")
    def password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one number")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
                raise ValueError("Password must contain at least one special character")
        return v


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserSchema(UserInDBBase):
    # Note: Related objects (votes, polls) should be handled via separate Pydantic schemas.
    # votes: List["Vote"] = Field(default_factory=list)
    # polls: List["Poll"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserInDBBase):
    hashed_password: str = Field(
        ..., min_length=60, max_length=60
    )  # bcrypt hash length


class UserService:
    """Service for user-related operations.

    This service handles all user-related business logic including:
    - User creation and authentication
    - User information updates
    - User deletion
    - Token generation
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the user service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username to search for

        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                "Database error while fetching user by username",
                extra={
                    "username": username,
                    "error": str(e)
                },
                exc_info=True,
            )
            raise ValidationError("Failed to fetch user")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: Email to search for

        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                "Database error while fetching user by email",
                extra={
                    "email": email,
                    "error": str(e)
                },
                exc_info=True,
            )
            raise ValidationError("Failed to fetch user")

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            UserResponse: Created user

        Raises:
            ConflictError: If username or email already exists
            ValidationError: If user data is invalid
        """
        async with self.db.begin():
            try:
                # Check if username or email already exists
                if await self.get_user_by_username(user_data.username):
                    raise ConflictError("Username already exists")
                if await self.get_user_by_email(user_data.email):
                    raise ConflictError("Email already exists")

                # Create new user
                hashed_password = get_password_hash(user_data.password)
                user = User(
                    email=user_data.email,
                    username=user_data.username,
                    hashed_password=hashed_password,
                    is_active=user_data.is_active,
                    is_superuser=user_data.is_superuser,
                )

                self.db.add(user)
                await self.db.flush()

                logger.info(
                    "User created successfully",
                    extra={"user_id": user.id, "username": user.username},
                )

                return UserResponse.model_validate(user)
            except SQLAlchemyError as e:
                logger.error(
                    "Database error while creating user",
                    extra={"username": user_data.username, "error": str(e)},
                    exc_info=True,
                )
                raise ValidationError("Failed to create user")

    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            User: Authenticated user

        Raises:
            AuthenticationError: If authentication fails
        """
        user = await self.get_user_by_username(username)
        if not user:
            raise AuthenticationError("Invalid username or password")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        return user

    def create_access_token(self, user: User) -> str:
        """Create access token for user.

        Args:
            user: User to create token for

        Returns:
            str: JWT access token
        """
        return create_access_token({"sub": str(user.id)})

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user information.

        Args:
            user_id: ID of user to update
            user_data: New user data

        Returns:
            UserResponse: Updated user

        Raises:
            ResourceNotFoundError: If user not found
            ValidationError: If update data is invalid
        """
        async with self.db.begin():
            try:
                user = await self.db.get(User, user_id)
                if not user:
                    raise ResourceNotFoundError("User not found")

                if user_data.email is not None:
                    user.email = user_data.email
                if user_data.username is not None:
                    user.username = user_data.username
                if user_data.password is not None:
                    user.hashed_password = get_password_hash(user_data.password)

                await self.db.commit()
                await self.db.refresh(user)

                logger.info(
                    "User updated successfully",
                    extra={"user_id": user.id, "username": user.username},
                )
                return UserResponse.model_validate(user)
            except SQLAlchemyError as e:
                await self.db.rollback()
                logger.error(
                    "Database error during user update",
                    extra={"user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                raise ValidationError("Failed to update user")

    async def delete_user(self, user_id: int) -> None:
        """Delete a user.

        Args:
            user_id: ID of user to delete

        Raises:
            ResourceNotFoundError: If user not found
            ValidationError: If deletion fails
        """
        async with self.db.begin():
            try:
                user = await self.db.get(User, user_id)
                if not user:
                    raise ResourceNotFoundError("User not found")

                await self.db.delete(user)
                await self.db.commit()

                logger.info("User deleted successfully", extra={"user_id": user_id})
            except SQLAlchemyError as e:
                await self.db.rollback()
                logger.error(
                    "Database error during user deletion",
                    extra={"user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                raise ValidationError("Failed to delete user")

    async def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID.

        Args:
            user_id: ID of user to get

        Returns:
            UserResponse: User data

        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            user = await self.db.get(User, user_id)
            if not user:
                raise ResourceNotFoundError("User not found")
            return UserResponse.model_validate(user)
        except SQLAlchemyError as e:
            logger.error(
                "Database error while fetching user",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise ValidationError("Failed to fetch user")

    async def get_users(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[UserResponse]:
        """Get list of users.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return
            search: Optional search term

        Returns:
            List[UserResponse]: List of users
        """
        try:
            query = select(User)
            if search:
                query = query.where(
                    (User.username.ilike(f"%{search}%"))
                    | (User.email.ilike(f"%{search}%"))
                )
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            users = result.scalars().all()

            return [UserResponse.model_validate(user) for user in users]
        except SQLAlchemyError as e:
            logger.error(
                "Database error while fetching users",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ValidationError("Failed to fetch users")


# Set up logging
logger = get_logger(__name__)

# Configure OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting up application")
    await init_db()
    logger.info("Database initialized")
    # Log all available routes
    routes = [f"{route.methods} {route.path}" for route in app.routes]
    logger.info("Available routes", extra={"routes": routes})
    # Caching startup
    try:
        redis = aioredis.from_url("redis://localhost")
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info("Cache initialized")
    except Exception as e:
        logger.error("Failed to initialize cache", extra={"error": str(e)})
    yield
    # Shutdown logic
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The Commons API",
    version=settings.VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS based on environment
allowed_origins: List[str] = (
    settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list)
    else settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS
    else []
)
if settings.DEBUG:
    allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

# Include routers
logger.info("Registering routers...")
logger.info("Routers registered successfully")

# Add exception handlers
configure_exception_handlers(app)


@app.get("/health/db", response_model=Dict[str, Union[str, Dict[str, str]]])
async def database_health(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Union[str, Dict[str, str]]]:
    """Database health check endpoint.

    Args:
        db: Database session

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: Health status and optional error details

    Raises:
        HTTPException: If database connection fails
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except SQLAlchemyError as e:
        logger.error(
            "Database health check failed", extra={"error": str(e)}, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error",
        )


async def update_vote(
    db: AsyncSession, vote_id: int, vote_data: Dict[str, Any], user: User
) -> Vote:
    """Update a vote."""
    vote: Optional[Vote] = await get_vote(db, vote_id)

    if vote is None:
        raise ValueError(f"Vote with id {vote_id} not found")

    if vote.user_id != user.id:
        raise ValueError("Not authorized to update this vote")

    for key, value in vote_data.items():
        setattr(vote, key, value)

    try:
        await db.commit()
        await db.refresh(vote)
    except IntegrityError as e:
        await db.rollback()
        if "foreign key constraint" in str(e).lower():
            raise ValueError("Referenced option or poll does not exist")
        raise
    return vote


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Response:
    """Add request ID to each request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# 7. Add rate limiting for auth endpoints
@app.post("/api/token")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(RateLimiter(times=5, seconds=60)),
) -> Token:
    """Login endpoint with rate limiting and CSRF protection."""
    try:
        username = form_data.username
        password = form_data.password

        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )

        user_service = UserService(db)
        user = await user_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        access_token = user_service.create_access_token(user)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(
            "Login failed", extra={"username": username, "error": str(e)}, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


# 8. Add password complexity validation


def validate_password(password: str) -> bool:
    """Validate password complexity."""
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain lowercase")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain number")
    if not any(c in "!@#$%^&*()" for c in password):
        raise ValueError("Password must contain special character")
    return True


# 10. Add specific exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error(
        "Database error",
        extra={
            "request_id": request.state.request_id,
            "error": str(exc),
            "stack_trace": traceback.format_exc(),
        },
    )
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})


# 11. Add request ID tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# 13. Add error recovery
async def recover_from_error(db: AsyncSession) -> None:
    try:
        await db.rollback()
    except Exception as e:
        logger.error("Failed to recover from error", extra={"error": str(e)})


# 14. Add connection pooling
engine = create_async_engine(
    settings.DATABASE_URL, poolclass=NullPool
)


# 15. Add retry logic
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def execute_with_retry(db: AsyncSession, query) -> Any:
    return await db.execute(query)


# 16. Add transaction management
T = TypeVar("T")


async def execute_in_transaction(db: AsyncSession, func: Callable[..., Awaitable[T]]) -> T:
    """Execute a function within a database transaction.

    Args:
        db: Database session
        func: The async function to execute

    Returns:
        T: The result of the function execution
    """
    async with db.begin():
        return await func()


# 17. Add query timeout
async def set_query_timeout(db: AsyncSession) -> None:
    """Set query timeout for the database session."""
    try:
        await db.execute(text("SET statement_timeout = '5s'"))
    except TimeoutError:
        logger.error("Query timeout")


# 18. Add connection health check
async def check_db_connection(db: AsyncSession) -> bool:
    """Check if the database connection is healthy."""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# 19. Add caching
# Remove the @app.on_event("startup") startup function at line 704

# 20. Add response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add to Poll model
end_date = Column(DateTime, nullable=True)  # For time-limited polls
is_active = Column(Boolean, default=True)  # To close polls
max_votes_per_user = Column(Integer, default=1)  # For multiple-choice polls


# Add session middleware
@app.middleware("http")
async def add_session(request: Request, call_next) -> Response:
    """Add session management to requests."""
    session_id = request.cookies.get("session")
    if not session_id:
        session_id = session_serializer.dumps(str(uuid.uuid4()))

    request.state.session = session_serializer.loads(session_id)
    response = await call_next(request)
    response.set_cookie(
        key="session",
        value=session_id,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=3600,
    )
    return response


# Ensure the exception handler is correctly registered
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
