import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings
from backend.schemas.content import PrincipleItem, ActionItem, StoryItem


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_content_dir():
    """Create a temporary content directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        content_dir = Path(temp_dir) / "real_content"
        content_dir.mkdir()
        yield content_dir


@pytest.fixture
def sample_principles_file(temp_content_dir):
    """Create a sample principles.json file."""
    principles_data = [
        {
            "id": "test-principle-1",
            "title": "Test Principle 1",
            "description": "This is a test principle",
            "tags": ["test", "principle"],
            "source": "Test source"
        },
        {
            "id": "test-principle-2",
            "title": "Test Principle 2",
            "description": "This is another test principle",
            "tags": ["test"],
            "source": "Test source 2"
        }
    ]
    
    principles_file = temp_content_dir / "principles.json"
    with open(principles_file, 'w') as f:
        json.dump(principles_data, f)
    
    return principles_file


@pytest.fixture
def sample_actions_file(temp_content_dir):
    """Create a sample actions.json file."""
    actions_data = [
        {
            "id": "test-action-1",
            "title": "Test Action 1",
            "description": "This is a test action",
            "scope": "city",
            "tags": ["test", "action"],
            "source": "Test source"
        }
    ]
    
    actions_file = temp_content_dir / "actions.json"
    with open(actions_file, 'w') as f:
        json.dump(actions_data, f)
    
    return actions_file


@pytest.fixture
def sample_stories_file(temp_content_dir):
    """Create a sample stories.json file."""
    stories_data = [
        {
            "id": "test-story-1",
            "title": "Test Story 1",
            "summary": "This is a test story summary",
            "impact": "Test impact",
            "link": "https://example.com"
        }
    ]
    
    stories_file = temp_content_dir / "stories.json"
    with open(stories_file, 'w') as f:
        json.dump(stories_data, f)
    
    return stories_file


class TestContentAPI:
    """Test content API endpoints."""
    
    def test_get_principles_demo_mode(self, client):
        """Test getting principles in demo mode."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', True):
            response = client.get("/api/content/principles")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "demo"
            assert len(data["items"]) > 0
            
            # Check structure of first item
            first_item = data["items"][0]
            assert "id" in first_item
            assert "title" in first_item
            assert "description" in first_item
    
    def test_get_actions_demo_mode(self, client):
        """Test getting actions in demo mode."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', True):
            response = client.get("/api/content/actions")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "demo"
            assert len(data["items"]) > 0
    
    def test_get_stories_demo_mode(self, client):
        """Test getting stories in demo mode."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', True):
            response = client.get("/api/content/stories")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "demo"
            assert len(data["items"]) > 0
    
    def test_get_principles_file_mode(self, client, temp_content_dir, sample_principles_file):
        """Test getting principles from file."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
             patch('backend.config.settings.CONTENT_DATA_DIR', str(temp_content_dir)), \
             patch('backend.services.content_loader.content_loader.content_dir', temp_content_dir):
            
            response = client.get("/api/content/principles")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "file"
            assert len(data["items"]) == 2
            
            # Check first item
            first_item = data["items"][0]
            assert first_item["id"] == "test-principle-1"
            assert first_item["title"] == "Test Principle 1"
            assert first_item["description"] == "This is a test principle"
            assert first_item["tags"] == ["test", "principle"]
            assert first_item["source"] == "Test source"
    
    def test_get_actions_file_mode(self, client, temp_content_dir, sample_actions_file):
        """Test getting actions from file."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
             patch('backend.config.settings.CONTENT_DATA_DIR', str(temp_content_dir)), \
             patch('backend.services.content_loader.content_loader.content_dir', temp_content_dir):
            
            response = client.get("/api/content/actions")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "file"
            assert len(data["items"]) == 1
            
            # Check first item
            first_item = data["items"][0]
            assert first_item["id"] == "test-action-1"
            assert first_item["title"] == "Test Action 1"
            assert first_item["description"] == "This is a test action"
            assert first_item["scope"] == "city"
            assert first_item["tags"] == ["test", "action"]
    
    def test_get_stories_file_mode(self, client, temp_content_dir, sample_stories_file):
        """Test getting stories from file."""
        with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
             patch('backend.config.settings.CONTENT_DATA_DIR', str(temp_content_dir)), \
             patch('backend.services.content_loader.content_loader.content_dir', temp_content_dir):
            
            response = client.get("/api/content/stories")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert "source" in data
            assert data["source"] == "file"
            assert len(data["items"]) == 1
            
            # Check first item
            first_item = data["items"][0]
            assert first_item["id"] == "test-story-1"
            assert first_item["title"] == "Test Story 1"
            assert first_item["summary"] == "This is a test story summary"
            assert first_item["impact"] == "Test impact"
            assert first_item["link"] == "https://example.com"
    
    def test_get_principles_missing_file(self, client):
        """Test getting principles when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = Path(temp_dir) / "real_content"
            content_dir.mkdir()
            
            with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
                 patch('backend.config.settings.CONTENT_DATA_DIR', str(content_dir)), \
                 patch('backend.services.content_loader.content_loader.content_dir', content_dir):
                
                # Clear the cache to ensure fresh data
                from backend.services.content_loader import content_loader
                content_loader.clear_cache()
                
                response = client.get("/api/content/principles")
                
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "count" in data
                assert "source" in data
                assert data["source"] == "file"
                assert len(data["items"]) == 0
    
    def test_get_actions_missing_file(self, client):
        """Test getting actions when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = Path(temp_dir) / "real_content"
            content_dir.mkdir()
            
            with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
                 patch('backend.config.settings.CONTENT_DATA_DIR', str(content_dir)), \
                 patch('backend.services.content_loader.content_loader.content_dir', content_dir):
                
                # Clear the cache to ensure fresh data
                from backend.services.content_loader import content_loader
                content_loader.clear_cache()
                
                response = client.get("/api/content/actions")
                
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "count" in data
                assert "source" in data
                assert data["source"] == "file"
                assert len(data["items"]) == 0
    
    def test_get_stories_missing_file(self, client):
        """Test getting stories when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = Path(temp_dir) / "real_content"
            content_dir.mkdir()
            
            with patch('backend.config.settings.USE_DEMO_CONTENT', False), \
                 patch('backend.config.settings.CONTENT_DATA_DIR', str(content_dir)), \
                 patch('backend.services.content_loader.content_loader.content_dir', content_dir):
                
                # Clear the cache to ensure fresh data
                from backend.services.content_loader import content_loader
                content_loader.clear_cache()
                
                response = client.get("/api/content/stories")
                
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "count" in data
                assert "source" in data
                assert data["source"] == "file"
                assert len(data["items"]) == 0
    
    def test_clear_content_cache(self, client):
        """Test clearing content cache."""
        response = client.post("/api/content/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Content cache cleared successfully"


class TestContentSchemas:
    """Test content Pydantic schemas."""
    
    def test_principle_item_schema(self):
        """Test PrincipleItem schema validation."""
        data = {
            "id": "test-id",
            "title": "Test Title",
            "description": "Test Description",
            "tags": ["test", "principle"],
            "source": "Test Source"
        }
        
        principle = PrincipleItem(**data)
        assert principle.id == "test-id"
        assert principle.title == "Test Title"
        assert principle.description == "Test Description"
        assert principle.tags == ["test", "principle"]
        assert principle.source == "Test Source"
    
    def test_action_item_schema(self):
        """Test ActionItem schema validation."""
        data = {
            "id": "test-id",
            "title": "Test Title",
            "description": "Test Description",
            "scope": "city",
            "tags": ["test", "action"],
            "source": "Test Source"
        }
        
        action = ActionItem(**data)
        assert action.id == "test-id"
        assert action.title == "Test Title"
        assert action.description == "Test Description"
        assert action.scope == "city"
        assert action.tags == ["test", "action"]
        assert action.source == "Test Source"
    
    def test_story_item_schema(self):
        """Test StoryItem schema validation."""
        data = {
            "id": "test-id",
            "title": "Test Title",
            "summary": "Test Summary",
            "impact": "Test Impact",
            "link": "https://example.com"
        }
        
        story = StoryItem(**data)
        assert story.id == "test-id"
        assert story.title == "Test Title"
        assert story.summary == "Test Summary"
        assert story.impact == "Test Impact"
        assert story.link == "https://example.com"
