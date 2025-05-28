"""Test configuration settings."""

import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Redis Configuration - Use a mock Redis for tests
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use database 1 for tests
TEST_REDIS_MOCK = True  # Use mock Redis for tests

# Engine Settings
TEST_ENGINE_SETTINGS = {
    "echo": True,  # Enable SQL logging
    "future": True,
    "pool_pre_ping": True,
    "connect_args": {"check_same_thread": False}  # Allow SQLite to work with async
}

# Session Settings
TEST_SESSION_SETTINGS = {
    "expire_on_commit": False,
    "autocommit": False,
    "autoflush": False,
}

# Transaction Settings
TEST_TRANSACTION_SETTINGS = {
    "isolation_level": "SERIALIZABLE",  # Default isolation level
    "timeout": 30.0,  # Transaction timeout in seconds
    "retry_attempts": 3,  # Number of retry attempts for deadlocks
    "retry_delay": 0.1,  # Delay between retries in seconds
    "readonly": False,  # Default read-only mode
    "deferrable": False,  # Default deferrable mode
    "deferrable_constraints": [],  # List of constraints to defer
    "savepoint": True,  # Use savepoints for nested transactions
    "nested": True,  # Allow nested transactions
    "rollback_on_error": True,  # Rollback on error
    "commit_on_success": True,  # Commit on success
}

# User Settings
TEST_USER_SETTINGS = {
    "default_password": "testpass123",
    "token_expires_delta": 3600,  # 1 hour
    "username_prefix": "test_user_",
    "email_domain": "@test.com",
}

# API Settings
TEST_API_SETTINGS = {
    "base_url": "http://test",
    "timeout": 30.0,
    "follow_redirects": True,
}

# Cleanup Settings
TEST_CLEANUP_SETTINGS = {
    "verify_cleanup": True,
    "cleanup_tables": [
        "votes",
        "options",
        "polls",
        "users",
    ],
}

# Environment Variables
TEST_ENV_VARS = {
    "DATABASE_URL": TEST_DATABASE_URL,
    "REDIS_URL": TEST_REDIS_URL,
    "SECRET_KEY": "test_secret_key",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "ENVIRONMENT": "test",
    "DB_ECHO_LOG": "true",  # Enable database logging
    "RATE_LIMIT_PER_MINUTE": "100",  # Higher rate limit for tests
    "LOG_LEVEL": "DEBUG",  # Set logging level
}