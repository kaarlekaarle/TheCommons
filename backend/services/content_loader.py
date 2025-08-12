import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache
from datetime import datetime, timedelta

from backend.config import settings
from backend.schemas.content import PrincipleItem, ActionItem, StoryItem

logger = logging.getLogger(__name__)


class ContentLoader:
    """Service for loading content from files with caching."""
    
    def __init__(self):
        self.content_dir = Path(settings.CONTENT_DATA_DIR)
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
    
    def _get_file_path(self, content_type: str) -> Path:
        """Get the file path for a content type."""
        return self.content_dir / f"{content_type}.json"
    
    def _is_cache_valid(self, content_type: str) -> bool:
        """Check if cached content is still valid."""
        if content_type not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[content_type]
        file_path = self._get_file_path(content_type)
        
        # Check if file has been modified since cache
        if file_path.exists():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime > cache_time:
                return False
        
        # Check if cache has expired
        if datetime.now() - cache_time > self._cache_ttl:
            return False
        
        return True
    
    def _load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load and parse a JSON file."""
        try:
            if not file_path.exists():
                logger.warning(f"Content file not found: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error(f"Invalid JSON structure in {file_path}: expected list, got {type(data)}")
                return []
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {e}")
            return []
    
    def _validate_and_parse_principles(self, data: List[Dict[str, Any]]) -> List[PrincipleItem]:
        """Validate and parse principle data."""
        principles = []
        for i, item in enumerate(data):
            try:
                principle = PrincipleItem(**item)
                principles.append(principle)
            except Exception as e:
                logger.warning(f"Invalid principle at index {i}: {e}")
                continue
        return principles
    
    def _validate_and_parse_actions(self, data: List[Dict[str, Any]]) -> List[ActionItem]:
        """Validate and parse action data."""
        actions = []
        for i, item in enumerate(data):
            try:
                action = ActionItem(**item)
                actions.append(action)
            except Exception as e:
                logger.warning(f"Invalid action at index {i}: {e}")
                continue
        return actions
    
    def _validate_and_parse_stories(self, data: List[Dict[str, Any]]) -> List[StoryItem]:
        """Validate and parse story data."""
        stories = []
        for i, item in enumerate(data):
            try:
                story = StoryItem(**item)
                stories.append(story)
            except Exception as e:
                logger.warning(f"Invalid story at index {i}: {e}")
                continue
        return stories
    
    def load_principles(self) -> List[PrincipleItem]:
        """Load principles from file with caching."""
        if self._is_cache_valid("principles"):
            return self._cache.get("principles", [])
        
        file_path = self._get_file_path("principles")
        data = self._load_json_file(file_path)
        principles = self._validate_and_parse_principles(data)
        
        # Update cache
        self._cache["principles"] = principles
        self._cache_timestamps["principles"] = datetime.now()
        
        logger.info(f"Loaded {len(principles)} principles from {file_path}")
        return principles
    
    def load_actions(self) -> List[ActionItem]:
        """Load actions from file with caching."""
        if self._is_cache_valid("actions"):
            return self._cache.get("actions", [])
        
        file_path = self._get_file_path("actions")
        data = self._load_json_file(file_path)
        actions = self._validate_and_parse_actions(data)
        
        # Update cache
        self._cache["actions"] = actions
        self._cache_timestamps["actions"] = datetime.now()
        
        logger.info(f"Loaded {len(actions)} actions from {file_path}")
        return actions
    
    def load_stories(self) -> List[StoryItem]:
        """Load stories from file with caching."""
        if self._is_cache_valid("stories"):
            return self._cache.get("stories", [])
        
        file_path = self._get_file_path("stories")
        data = self._load_json_file(file_path)
        stories = self._validate_and_parse_stories(data)
        
        # Update cache
        self._cache["stories"] = stories
        self._cache_timestamps["stories"] = datetime.now()
        
        logger.info(f"Loaded {len(stories)} stories from {file_path}")
        return stories
    
    def clear_cache(self) -> None:
        """Clear the content cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Content cache cleared")


# Global content loader instance
content_loader = ContentLoader()
