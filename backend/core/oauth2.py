from typing import List, Optional

from fastapi.security import OAuth2PasswordBearer

from backend.config import settings

# OAuth2 Configuration
TOKEN_URL = "api/token"
TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM


# Define available scopes


class OAuth2Scopes:
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# Available scopes for different operations
SCOPES = {
    "users:read": OAuth2Scopes.READ,
    "users:write": OAuth2Scopes.WRITE,
    "users:admin": OAuth2Scopes.ADMIN,
    "polls:read": OAuth2Scopes.READ,
    "polls:write": OAuth2Scopes.WRITE,
    "polls:admin": OAuth2Scopes.ADMIN,
    "votes:read": OAuth2Scopes.READ,
    "votes:write": OAuth2Scopes.WRITE,
    "votes:admin": OAuth2Scopes.ADMIN,
}

# Create OAuth2 scheme with default configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL, auto_error=True, scopes=SCOPES)




def get_oauth2_scheme(
    token_url: Optional[str] = None,
    auto_error: bool = True,
    scopes: Optional[dict] = None,
) -> OAuth2PasswordBearer:
    """
    Get an OAuth2 scheme with custom configuration.
    Useful for endpoints that need different OAuth2 settings.
    """
    return OAuth2PasswordBearer(
        tokenUrl=token_url or TOKEN_URL, auto_error=auto_error, scopes=scopes or SCOPES
    )
