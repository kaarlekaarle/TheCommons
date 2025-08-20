"""JSON utilities for safe serialization of complex types."""
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any


class JSONResponseEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, date, UUID, and Decimal objects safely."""
    
    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to JSON-safe formats."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def safe_json_response(data: Any) -> dict:
    """Convert data to JSON-safe format using our custom encoder."""
    try:
        # First convert to JSON string then back to dict to ensure all objects are serializable
        json_str = json.dumps(data, cls=JSONResponseEncoder)
        return json.loads(json_str)
    except Exception as e:
        return {
            "ok": False,
            "meta": {
                "errors": [f"serialization_error: {str(e)}"],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
