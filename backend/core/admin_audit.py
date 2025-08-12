"""Admin audit logging for The Commons."""
from typing import Optional, Any, Dict
from fastapi import Request

from backend.core.logging_json import get_json_logger, get_request_context
from backend.models.user import User

logger = get_json_logger(__name__)

def log_admin_action(
    action: str,
    target_resource: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    user: Optional[User] = None,
    result: str = "success"
):
    """Log an admin action with full context.
    
    Args:
        action: The admin action being performed (e.g., "delete_user", "modify_poll")
        target_resource: The type of resource being acted upon (e.g., "user", "poll")
        target_id: The ID of the target resource
        details: Additional details about the action
        request: The FastAPI request object (for request context)
        user: The user performing the action
        result: The result of the action ("success", "failure", "denied")
    """
    # Get request context
    context = get_request_context()
    
    # Build log data
    log_data = {
        "event_type": "admin_action",
        "action": action,
        "target_resource": target_resource,
        "result": result,
    }
    
    if target_id:
        log_data["target_id"] = target_id
    
    if details:
        log_data["details"] = details
    
    if user:
        log_data["admin_user_id"] = str(user.id)
        log_data["admin_username"] = user.username
    
    # Add request context if available
    if request:
        log_data.update({
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
        })
    
    # Merge with existing context
    context.update(log_data)
    
    # Log the action
    logger.info("Admin action performed", **context)

def is_admin_user(user: User, admin_usernames: str = "") -> bool:
    """Check if a user is an admin based on superuser flag or username list.
    
    Args:
        user: The user to check
        admin_usernames: Comma-separated list of admin usernames
        
    Returns:
        True if the user is an admin, False otherwise
    """
    # Check superuser flag
    if user.is_user_superuser():
        return True
    
    # Check username list
    if admin_usernames:
        admin_list = [name.strip() for name in admin_usernames.split(",") if name.strip()]
        if user.username in admin_list:
            return True
    
    return False

def require_admin(
    user: User,
    admin_usernames: str = "",
    action: str = "access_admin_endpoint",
    target_resource: str = "unknown",
    request: Optional[Request] = None
) -> bool:
    """Require admin privileges for an action.
    
    Args:
        user: The user attempting the action
        admin_usernames: Comma-separated list of admin usernames
        action: The action being attempted
        target_resource: The resource being accessed
        request: The FastAPI request object
        
    Returns:
        True if the user has admin privileges
        
    Raises:
        PermissionError: If the user doesn't have admin privileges
    """
    if not is_admin_user(user, admin_usernames):
        # Log the denied access attempt
        log_admin_action(
            action=action,
            target_resource=target_resource,
            request=request,
            user=user,
            result="denied"
        )
        raise PermissionError("Admin privileges required")
    
    # Log the successful admin access
    log_admin_action(
        action=action,
        target_resource=target_resource,
        request=request,
        user=user,
        result="success"
    )
    
    return True
