import logging
from datetime import datetime, date
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Simple in-memory metrics storage (in production, use Redis or a proper metrics system)
_metrics: Dict[str, Dict[str, int]] = {}

def increment_delegation_metric(metric_name: str, user_id: str = None) -> None:
    """
    Increment a delegation-related metric counter.
    
    Args:
        metric_name: Name of the metric (e.g., 'delegation_created', 'delegation_revoked')
        user_id: Optional user ID for user-specific tracking
    """
    today = date.today().isoformat()
    
    if today not in _metrics:
        _metrics[today] = {}
    
    metric_key = f"{metric_name}_{today}"
    _metrics[today][metric_key] = _metrics[today].get(metric_key, 0) + 1
    
    # Log the metric for monitoring
    extra_data = {
        "metric": metric_name,
        "date": today,
        "count": _metrics[today][metric_key]
    }
    
    if user_id:
        extra_data["user_id"] = user_id
    
    logger.info(
        f"Delegation metric: {metric_name}",
        extra=extra_data
    )

def get_delegation_metrics(date_str: str = None) -> Dict[str, Any]:
    """
    Get delegation metrics for a specific date or today.
    
    Args:
        date_str: Date string in ISO format (YYYY-MM-DD), defaults to today
        
    Returns:
        Dictionary containing metrics for the specified date
    """
    if date_str is None:
        date_str = date.today().isoformat()
    
    return _metrics.get(date_str, {})

def log_daily_delegation_summary() -> None:
    """Log a summary of delegation metrics for the current day."""
    today = date.today().isoformat()
    today_metrics = _metrics.get(today, {})
    
    if today_metrics:
        logger.info(
            "Daily delegation metrics summary",
            extra={
                "date": today,
                "metrics": today_metrics,
                "total_events": sum(today_metrics.values())
            }
        )
    else:
        logger.info(
            "No delegation activity today",
            extra={"date": today}
        )
