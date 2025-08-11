"""Test environment configuration."""

import os
from typing import Dict, Any

def setup_test_env() -> None:
    """Set up test environment variables."""
    env_vars = {
        # Database Configuration - Use the same PostgreSQL database as main app
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/commons_db",
        "REDIS_URL": "redis://localhost:6379/1",
        "REDIS_MOCK": "true",
        
        # Security
        "SECRET_KEY": "test_secret_key_do_not_use_in_production",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        
        # Environment
        "ENVIRONMENT": "test",
        "DB_ECHO_LOG": "true",
        "LOG_LEVEL": "DEBUG",
        
        # Rate Limiting
        "RATE_LIMIT_PER_MINUTE": "100",
        
        # API Settings
        "API_BASE_URL": "http://test",
        "API_TIMEOUT": "30.0",
        "API_FOLLOW_REDIRECTS": "true",
        
        # Test User Settings
        "TEST_USER_PASSWORD": "testpass123",
        "TEST_USER_PREFIX": "test_user_",
        "TEST_USER_EMAIL_DOMAIN": "@test.com",
        
        # Transaction Settings
        "DB_ISOLATION_LEVEL": "SERIALIZABLE",
        "DB_TRANSACTION_TIMEOUT": "30.0",
        "DB_RETRY_ATTEMPTS": "3",
        "DB_RETRY_DELAY": "0.1",

        # CORS Settings
        "ALLOWED_ORIGINS": '["http://localhost:3000", "http://127.0.0.1:3000"]'
    }
    
    # Store original environment variables
    original_env = {}
    for key in env_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = env_vars[key]
    
    return original_env

def restore_env(original_env: Dict[str, str]) -> None:
    """Restore original environment variables."""
    for key in original_env:
        os.environ[key] = original_env[key]
    for key in list(os.environ.keys()):
        if key.startswith(("TEST_", "DB_", "API_")):
            del os.environ[key] 