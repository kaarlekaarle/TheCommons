"""Audit logging system for The Commons."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from backend.core.logging import add_context, get_logger

logger = get_logger(__name__)

class AuditAction(str, Enum):
    """Types of auditable actions."""
    # User actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_READ = "user_read"
    
    # Poll actions
    POLL_CREATE = "poll_create"
    POLL_UPDATE = "poll_update"
    POLL_DELETE = "poll_delete"
    POLL_CLOSE = "poll_close"
    POLL_REOPEN = "poll_reopen"
    
    # Vote actions
    VOTE_CAST = "vote_cast"
    VOTE_CHANGE = "vote_change"
    VOTE_DELETE = "vote_delete"
    
    # Delegation actions
    DELEGATION_CREATE = "delegation_create"
    DELEGATION_UPDATE = "delegation_update"
    DELEGATION_DELETE = "delegation_delete"
    
    # System actions
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in audit logs.
    
    Args:
        data: The data to mask.
        
    Returns:
        A copy of the data with sensitive fields masked.
    """
    masked_data = data.copy()
    sensitive_fields = {
        "password",
        "token",
        "secret",
        "key",
        "authorization",
        "cookie",
        "session",
    }
    
    for key in masked_data:
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            masked_data[key] = "***MASKED***"
    
    return masked_data

def audit_log(
    action: AuditAction,
    user_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Log an auditable action.
    
    Args:
        action: The type of action being audited.
        user_id: The ID of the user performing the action.
        resource_id: The ID of the resource being acted upon.
        resource_type: The type of resource being acted upon.
        details: Additional details about the action.
        success: Whether the action was successful.
        error: Error message if the action failed.
    """
    # Prepare audit context
    audit_context = {
        "audit_action": action,
        "audit_timestamp": datetime.utcnow().isoformat(),
        "audit_success": success,
    }
    
    if user_id is not None:
        audit_context["audit_user_id"] = user_id
    
    if resource_id is not None:
        audit_context["audit_resource_id"] = resource_id
    
    if resource_type is not None:
        audit_context["audit_resource_type"] = resource_type
    
    if details is not None:
        audit_context["audit_details"] = mask_sensitive_data(details)
    
    if error is not None:
        audit_context["audit_error"] = error
    
    # Add audit context to all subsequent logs
    add_context(**audit_context)
    
    # Log the audit event
    if success:
        logger.info(
            "audit_event",
            **audit_context
        )
    else:
        logger.error(
            "audit_event_failed",
            **audit_context
        )

def audit_log_decorator(action: AuditAction):
    """Decorator to automatically log auditable actions.
    
    Args:
        action: The type of action being audited.
        
    Returns:
        A decorator function that logs the action.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id and resource_id from kwargs if available
            user_id = kwargs.get("user_id")
            resource_id = kwargs.get("resource_id")
            resource_type = kwargs.get("resource_type")
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Log successful action
                audit_log(
                    action=action,
                    user_id=user_id,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    details={"result": str(result)},
                    success=True,
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                audit_log(
                    action=action,
                    user_id=user_id,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    details={"error": str(e)},
                    success=False,
                    error=str(e),
                )
                raise
        
        return wrapper
    
    return decorator 