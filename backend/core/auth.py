from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.exceptions import AuthenticationError
from backend.core.oauth2 import ALGORITHM, TOKEN_EXPIRE_MINUTES
from backend.database import get_db
from backend.models.user import User
from backend.schemas.token import TokenData

# Configure password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Use a fixed number of rounds
)

# Configure JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)




def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)




def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


async def get_user(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate a user."""
    user = await get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user




def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    from backend.schemas.error import ErrorCodes
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "detail": "Could not validate credentials",
            "code": ErrorCodes.INVALID_CREDENTIALS,
            "status_code": 401,
            "error_type": "AuthenticationError",
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
        
    try:
        # First try to decode the token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Then try to get the user
        try:
            user = await db.get(User, UUID(user_id))
            if user is None:
                raise credentials_exception
            return user
        except ValueError:  # Invalid UUID format
            raise credentials_exception
            
    except JWTError:  # Invalid token format or signature
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_user_active():
        from backend.schemas.error import ErrorCodes
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": "Inactive user",
                "code": ErrorCodes.AUTHENTICATION_ERROR,
                "status_code": 401,
                "error_type": "AuthenticationError",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    return current_user


async def get_current_user_from_token(token: str, db: AsyncSession) -> User:
    """Get current user from JWT token without FastAPI dependencies."""
    from backend.schemas.error import ErrorCodes
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "detail": "Could not validate credentials",
            "code": ErrorCodes.INVALID_CREDENTIALS,
            "status_code": 401,
            "error_type": "AuthenticationError",
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
        
    try:
        # First try to decode the token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Then try to get the user
        try:
            user = await db.get(User, UUID(user_id))
            if user is None:
                raise credentials_exception
            return user
        except ValueError:  # Invalid UUID format
            raise credentials_exception
            
    except JWTError:  # Invalid token format or signature
        raise credentials_exception
