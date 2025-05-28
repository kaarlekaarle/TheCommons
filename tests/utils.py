"""Test utilities for generating test data and managing test state."""

import uuid
import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, AsyncGenerator, TypeVar, Callable, List, Tuple, Union, Set, Literal
from contextlib import asynccontextmanager
from functools import wraps
from enum import Enum, auto

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    TimeoutError,
    NoResultFound,
    MultipleResultsFound,
    DBAPIError,
)

from backend.core.auth import get_password_hash
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from tests.config import (
    TEST_USER_SETTINGS,
    TEST_TRANSACTION_SETTINGS,
)

T = TypeVar('T')



class BackoffStrategy(Enum):
    """Backoff strategies for retry operations."""
    EXPONENTIAL = auto()      # Exponential backoff
    LINEAR = auto()           # Linear backoff
    FIBONACCI = auto()        # Fibonacci backoff
    CONSTANT = auto()         # Constant delay
    RANDOM = auto()           # Random delay within bounds
    POLYNOMIAL = auto()       # Polynomial backoff
    GEOMETRIC = auto()        # Geometric backoff
    LOGARITHMIC = auto()      # Logarithmic backoff
    QUADRATIC = auto()        # Quadratic backoff
    CUBIC = auto()            # Cubic backoff
    COMPOSITE = auto()        # Composite of multiple strategies
    ADAPTIVE = auto()         # Adaptive backoff based on error type



class BackoffConfig:
    """Configuration for backoff strategies."""
    def __init__(
        self,
        base_delay: float,
        max_delay: float,
        multiplier: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.25,
        polynomial_degree: int = 2,
        geometric_ratio: float = 1.5,
        logarithmic_base: float = 2.0,
        composite_strategies: List[Tuple[BackoffStrategy, float]] = None,
        adaptive_weights: Dict[str, float] = None,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.jitter_factor = jitter_factor
        self.polynomial_degree = polynomial_degree
        self.geometric_ratio = geometric_ratio
        self.logarithmic_base = logarithmic_base
        self.composite_strategies = composite_strategies or [
            (BackoffStrategy.EXPONENTIAL, 0.6),
            (BackoffStrategy.FIBONACCI, 0.4),
        ]
        self.adaptive_weights = adaptive_weights or {
            "deadlock": 1.5,
            "timeout": 1.2,
            "connection": 1.0,
            "default": 1.0,
        }



class TestDataError(Exception):
    """Base exception for test data errors."""
    pass



class TestDataCreationError(TestDataError):
    """Error raised when test data creation fails."""
    pass



class TestDataCleanupError(TestDataError):
    """Error raised when test data cleanup fails."""
    pass



class TestDataVerificationError(TestDataError):
    """Error raised when test data verification fails."""
    pass



class TestTransactionError(TestDataError):
    """Error raised when transaction management fails."""
    pass



class RetryableError(TestTransactionError):
    """Error that can be retried."""
    pass



class NonRetryableError(TestTransactionError):
    """Error that should not be retried."""
    pass



def calculate_backoff(
    attempt: int,
    config: BackoffConfig,
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    error_type: Optional[str] = None,
) -> float:
    """Calculate the delay for a retry attempt using various backoff strategies.

    Args:
        attempt: The current attempt number (1-based)
        config: Backoff configuration
        strategy: The backoff strategy to use
        error_type: Type of error for adaptive strategy

    Returns:
        float: The delay in seconds
    """
    def add_jitter(delay: float) -> float:
        """Add jitter to the delay."""
        if not config.jitter:
            return delay
        jitter_amount = delay * config.jitter_factor
        return delay + random.uniform(-jitter_amount, jitter_amount)

    def fibonacci(n: int) -> int:
        """Calculate the nth Fibonacci number."""
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            a, b = 0, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            return b

    def get_adaptive_weight() -> float:
        """Get weight for adaptive strategy based on error type."""
        if not error_type:
            return config.adaptive_weights["default"]
        for key, weight in config.adaptive_weights.items():
            if key in error_type.lower():
                return weight
        return config.adaptive_weights["default"]

    # Calculate base delay based on strategy
    if strategy == BackoffStrategy.EXPONENTIAL:
        delay = min(config.base_delay * (config.multiplier ** (attempt - 1)), config.max_delay)
    elif strategy == BackoffStrategy.LINEAR:
        delay = min(config.base_delay * attempt, config.max_delay)
    elif strategy == BackoffStrategy.FIBONACCI:
        delay = min(config.base_delay * fibonacci(attempt), config.max_delay)
    elif strategy == BackoffStrategy.CONSTANT:
        delay = config.base_delay
    elif strategy == BackoffStrategy.RANDOM:
        delay = random.uniform(config.base_delay, config.max_delay)
    elif strategy == BackoffStrategy.POLYNOMIAL:
        delay = min(config.base_delay * (attempt ** config.polynomial_degree), config.max_delay)
    elif strategy == BackoffStrategy.GEOMETRIC:
        delay = min(config.base_delay * (config.geometric_ratio ** (attempt - 1)), config.max_delay)
    elif strategy == BackoffStrategy.LOGARITHMIC:
        delay = min(config.base_delay * math.log(attempt, config.logarithmic_base), config.max_delay)
    elif strategy == BackoffStrategy.QUADRATIC:
        delay = min(config.base_delay * (attempt ** 2), config.max_delay)
    elif strategy == BackoffStrategy.CUBIC:
        delay = min(config.base_delay * (attempt ** 3), config.max_delay)
    elif strategy == BackoffStrategy.COMPOSITE:
        # Combine multiple strategies with weights
        delay = 0
        for strategy, weight in config.composite_strategies:
            strategy_delay = calculate_backoff(attempt, config, strategy)
            delay += strategy_delay * weight
        delay = min(delay, config.max_delay)
    elif strategy == BackoffStrategy.ADAPTIVE:
        # Use adaptive strategy based on error type
        weight = get_adaptive_weight()
        delay = min(config.base_delay * weight * (config.multiplier ** (attempt - 1)), config.max_delay)
    else:
        raise ValueError(f"Unknown backoff strategy: {strategy}")

    return add_jitter(delay)



def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The error to check

    Returns:
        bool: True if the error is retryable, False otherwise
    """
    retryable_errors = {
        OperationalError,
        TimeoutError,
        DBAPIError,
    }

    return isinstance(error, tuple(retryable_errors))

async def retry_operation(
    operation: Callable,
    *args,
    max_attempts: int = None,
    base_delay: float = None,
    max_delay: float = None,
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    jitter: bool = True,
    jitter_factor: float = 0.25,
    multiplier: float = 2.0,
    polynomial_degree: int = 2,
    geometric_ratio: float = 1.5,
    logarithmic_base: float = 2.0,
    composite_strategies: List[Tuple[BackoffStrategy, float]] = None,
    adaptive_weights: Dict[str, float] = None,
    retryable_errors: Set[type] = None,
    **kwargs,
) -> Any:
    """Retry an operation with backoff.

    Args:
        operation: The operation to retry
        *args: Positional arguments for the operation
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        strategy: Backoff strategy to use
        jitter: Whether to add jitter to delays
        jitter_factor: Factor for jitter calculation
        multiplier: Multiplier for exponential backoff
        polynomial_degree: Degree for polynomial backoff
        geometric_ratio: Ratio for geometric backoff
        logarithmic_base: Base for logarithmic backoff
        composite_strategies: Strategies for composite backoff
        adaptive_weights: Weights for adaptive backoff
        retryable_errors: Set of error types that can be retried
        **kwargs: Keyword arguments for the operation

    Returns:
        Any: Result of the operation

    Raises:
        Exception: Last error if all retries fail
    """
    max_attempts = max_attempts or TEST_TRANSACTION_SETTINGS["retry_attempts"]
    base_delay = base_delay or TEST_TRANSACTION_SETTINGS["retry_delay"]
    max_delay = max_delay or base_delay * 10

    config = BackoffConfig(
        base_delay=base_delay,
        max_delay=max_delay,
        multiplier=multiplier,
        jitter=jitter,
        jitter_factor=jitter_factor,
        polynomial_degree=polynomial_degree,
        geometric_ratio=geometric_ratio,
        logarithmic_base=logarithmic_base,
        composite_strategies=composite_strategies,
        adaptive_weights=adaptive_weights,
    )

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            last_error = e
            if not is_retryable_error(e) or (retryable_errors and not isinstance(e, tuple(retryable_errors))):
                raise

            if attempt < max_attempts:
                delay = calculate_backoff(attempt, config, strategy, str(e))
                await asyncio.sleep(delay)

    raise last_error



def handle_db_error(error: Exception, context: str) -> None:
    """Handle database errors.

    Args:
        error: The error to handle
        context: Context where the error occurred

    Raises:
        TestDataError: Appropriate error based on the type of database error
    """
    if isinstance(error, IntegrityError):
        raise TestDataCreationError(f"Failed to create test data in {context}: {str(error)}")
    elif isinstance(error, OperationalError):
        raise TestTransactionError(f"Database operation failed in {context}: {str(error)}")
    elif isinstance(error, TimeoutError):
        raise TestTransactionError(f"Database operation timed out in {context}: {str(error)}")
    elif isinstance(error, NoResultFound):
        raise TestDataVerificationError(f"No test data found in {context}: {str(error)}")
    elif isinstance(error, MultipleResultsFound):
        raise TestDataVerificationError(f"Multiple test data entries found in {context}: {str(error)}")
    else:
        raise TestDataError(f"Unexpected error in {context}: {str(error)}")

@asynccontextmanager
async def managed_transaction(
    session: AsyncSession,
    isolation_level: Optional[str] = None,
    readonly: Optional[bool] = None,
    deferrable: Optional[bool] = None,
    timeout: Optional[float] = None,
    savepoint: Optional[bool] = None,
    nested: Optional[bool] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Manage a database transaction with retry logic.

    Args:
        session: Database session
        isolation_level: Transaction isolation level
        readonly: Whether the transaction is read-only
        deferrable: Whether constraints are deferrable
        timeout: Transaction timeout
        savepoint: Whether to use savepoints
        nested: Whether to allow nested transactions

    Yields:
        AsyncSession: Database session
    """
    settings = {
        "isolation_level": isolation_level or TEST_TRANSACTION_SETTINGS["isolation_level"],
        "readonly": readonly if readonly is not None else TEST_TRANSACTION_SETTINGS["readonly"],
        "deferrable": deferrable if deferrable is not None else TEST_TRANSACTION_SETTINGS["deferrable"],
        "timeout": timeout or TEST_TRANSACTION_SETTINGS["timeout"],
        "savepoint": savepoint if savepoint is not None else TEST_TRANSACTION_SETTINGS["savepoint"],
        "nested": nested if nested is not None else TEST_TRANSACTION_SETTINGS["nested"],
    }
    sp = None
    try:
        if session.bind.dialect.name != "sqlite":
            await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {settings['isolation_level']}"))
        if settings["readonly"]:
            await session.execute(text("SET TRANSACTION READ ONLY"))
        if settings["deferrable"]:
            await session.execute(text("SET TRANSACTION DEFERRABLE"))
        if settings["timeout"]:
            if session.bind.dialect.name != "sqlite":
                await session.execute(text(f"SET LOCAL statement_timeout = {settings['timeout'] * 1000}"))
        if settings["savepoint"]:
            sp = await session.begin_nested()
        yield session
        if not settings["savepoint"]:
            await session.commit()
    except Exception as e:
        await session.rollback()
        handle_db_error(e, "managed_transaction")
    finally:
        if sp is not None and getattr(sp, 'is_active', False):
            await sp.rollback()



def with_transaction(
    isolation_level: Optional[str] = None,
    readonly: Optional[bool] = None,
    deferrable: Optional[bool] = None,
    timeout: Optional[float] = None,
    savepoint: Optional[bool] = None,
    nested: Optional[bool] = None,
    retry_attempts: Optional[int] = None,
    retry_delay: Optional[float] = None,
    max_retry_delay: Optional[float] = None,
    retry_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    retry_jitter: bool = True,
    retry_jitter_factor: float = 0.25,
    retry_multiplier: float = 2.0,
    retry_polynomial_degree: int = 2,
    retry_geometric_ratio: float = 1.5,
    retry_logarithmic_base: float = 2.0,
    retry_composite_strategies: List[Tuple[BackoffStrategy, float]] = None,
    retry_adaptive_weights: Dict[str, float] = None,
) -> Callable[[Callable[..., AsyncGenerator[T, None]]], Callable[..., AsyncGenerator[T, None]]]:
    """Decorator for managing database transactions with retry logic.

    Args:
        isolation_level: Transaction isolation level
        readonly: Whether the transaction is read-only
        deferrable: Whether constraints are deferrable
        timeout: Transaction timeout
        savepoint: Whether to use savepoints
        nested: Whether to allow nested transactions
        retry_attempts: Maximum number of retry attempts
        retry_delay: Base delay between retries
        max_retry_delay: Maximum delay between retries
        retry_strategy: Backoff strategy to use
        retry_jitter: Whether to add jitter to delays
        retry_jitter_factor: Factor for jitter calculation
        retry_multiplier: Multiplier for exponential backoff
        retry_polynomial_degree: Degree for polynomial backoff
        retry_geometric_ratio: Ratio for geometric backoff
        retry_logarithmic_base: Base for logarithmic backoff
        retry_composite_strategies: Strategies for composite backoff
        retry_adaptive_weights: Weights for adaptive backoff
    """
    def decorator(func: Callable[..., AsyncGenerator[T, None]]) -> Callable[..., AsyncGenerator[T, None]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> AsyncGenerator[T, None]:
            session = args[0]
            if not isinstance(session, AsyncSession):
                raise ValueError("First argument must be an AsyncSession")
            async def operation() -> AsyncGenerator[T, None]:
                args_list = list(args)
                async with managed_transaction(
                    session,
                    isolation_level=isolation_level,
                    readonly=readonly,
                    deferrable=deferrable,
                    timeout=timeout,
                    savepoint=savepoint,
                    nested=nested,
                ) as managed_session:
                    # Replace the session in args with the managed session
                    args_list[0] = managed_session
                    return await func(*args_list, **kwargs)
            return await retry_operation(
                operation,
                max_attempts=retry_attempts,
                base_delay=retry_delay,
                max_delay=max_retry_delay,
                strategy=retry_strategy,
                jitter=retry_jitter,
                jitter_factor=retry_jitter_factor,
                multiplier=retry_multiplier,
                polynomial_degree=retry_polynomial_degree,
                geometric_ratio=retry_geometric_ratio,
                logarithmic_base=retry_logarithmic_base,
                composite_strategies=retry_composite_strategies,
                adaptive_weights=retry_adaptive_weights,
            )
        return wrapper
    return decorator



def generate_unique_username() -> str:
    """Generate a unique username for testing."""
    return f"{TEST_USER_SETTINGS['username_prefix']}{uuid.uuid4().hex[:8]}"



def generate_unique_email(username: Optional[str] = None) -> str:
    """Generate a unique email for testing."""
    username = username or generate_unique_username()
    return f"{username}{TEST_USER_SETTINGS['email_domain']}"

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def create_test_user(
    db_session: AsyncSession,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create a test user.

    Args:
        db_session: Database session
        username: Username for the user
        email: Email for the user
        password: Password for the user
        is_active: Whether the user is active
        is_superuser: Whether the user is a superuser

    Returns:
        User: Created user
    """
    username = username or generate_unique_username()
    email = email or generate_unique_email(username)
    password = password or TEST_USER_SETTINGS["default_password"]

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_superuser=is_superuser,
    )

    db_session.add(user)
    await db_session.flush()
    return user

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def create_test_poll(
    db_session: AsyncSession,
    user: User,
    title: str = "Test Poll",
    description: str = "This is a test poll",
) -> Poll:
    """Create a test poll.

    Args:
        db_session: Database session
        user: User creating the poll
        title: Title of the poll
        description: Description of the poll

    Returns:
        Poll: Created poll
    """
    poll = Poll(
        title=title,
        description=description,
        created_by=user.id,
    )

    db_session.add(poll)
    await db_session.flush()
    return poll

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def create_test_option(
    db_session: AsyncSession,
    poll: Poll,
    text: str = "Test Option",
) -> Option:
    """Create a test option.

    Args:
        db_session: Database session
        poll: Poll the option belongs to
        text: Text of the option

    Returns:
        Option: Created option
    """
    option = Option(
        poll_id=poll.id,
        text=text,
    )

    db_session.add(option)
    await db_session.flush()
    return option

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def create_test_vote(
    db_session: AsyncSession,
    user: User,
    poll: Poll,
    option: Option,
) -> Vote:
    """Create a test vote.

    Args:
        db_session: Database session
        user: User casting the vote
        poll: Poll being voted on
        option: Option being voted for

    Returns:
        Vote: Created vote
    """
    vote = Vote(
        user_id=user.id,
        poll_id=poll.id,
        option_id=option.id,
    )

    db_session.add(vote)
    await db_session.flush()
    return vote

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def create_test_poll_with_options(
    db_session: AsyncSession,
    user: User,
    title: str = "Test Poll",
    description: str = "This is a test poll",
    options: Optional[List[str]] = None,
) -> Tuple[Poll, List[Option]]:
    """Create a test poll with options.

    Args:
        db_session: Database session
        user: User creating the poll
        title: Title of the poll
        description: Description of the poll
        options: List of option texts

    Returns:
        Tuple[Poll, List[Option]]: Created poll and options
    """
    poll = await create_test_poll(db_session, user, title, description)

    if not options:
        options = ["Option 1", "Option 2", "Option 3"]

    created_options = []
    for option_text in options:
        option = await create_test_option(db_session, poll, option_text)
        created_options.append(option)

    return poll, created_options

@with_transaction(
    isolation_level="SERIALIZABLE",
    readonly=False,
    savepoint=True,
)
async def cleanup_test_data(db_session: AsyncSession) -> None:
    """Clean up test data.

    Args:
        db_session: Database session
    """
    for table in TEST_CLEANUP_SETTINGS["cleanup_tables"]:
        await db_session.execute(text(f"DELETE FROM {table}"))

@with_transaction(
    isolation_level="READ COMMITTED",
    readonly=True,
    savepoint=False,
)
async def get_test_user_by_email(db_session: AsyncSession, email: str) -> Optional[User]:
    """Get a test user by email.

    Args:
        db_session: Database session
        email: Email to search for

    Returns:
        Optional[User]: Found user or None
    """
    result = await db_session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

@with_transaction(
    isolation_level="READ COMMITTED",
    readonly=True,
    savepoint=False,
)
async def get_test_poll_by_title(db_session: AsyncSession, title: str) -> Optional[Poll]:
    """Get a test poll by title.

    Args:
        db_session: Database session
        title: Title to search for

    Returns:
        Optional[Poll]: Found poll or None
    """
    result = await db_session.execute(
        select(Poll).where(Poll.title == title)
    )
    return result.scalar_one_or_none()

@with_transaction(
    isolation_level="READ COMMITTED",
    readonly=True,
    savepoint=False,
)
async def verify_test_data_cleanup(db_session: AsyncSession) -> bool:
    """Verify that test data has been cleaned up.

    Args:
        db_session: Database session

    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    for table in TEST_CLEANUP_SETTINGS["cleanup_tables"]:
        result = await db_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar_one()
        if count > 0:
            return False
    return True