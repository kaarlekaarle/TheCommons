from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.config import get_settings
from backend.schemas.content import (
    ActionItem,
    ContentResponse,
    PrincipleItem,
    StoryItem,
)
from backend.services.content_loader import content_loader

router = APIRouter(prefix="/content", tags=["content"])


def get_demo_principles() -> List[PrincipleItem]:
    """Return demo principles when USE_DEMO_CONTENT is enabled."""
    return [
        PrincipleItem(
            id="ai-edu-001",
            title="AI in Education: A Tool for Stronger Learning",
            description="Our community leans toward using AI to support teachers and students—freeing teachers from routine tasks, offering tailored explanations, and improving access—while keeping education human at its core.",
            tags=["education", "technology", "ai", "governance"],
            source="The Commons MVP",
        )
    ]


def get_demo_actions() -> List[ActionItem]:
    """Return demo actions when USE_DEMO_CONTENT is enabled."""
    return [
        ActionItem(
            id="ai-edu-b-001",
            title="Pilot AI-Assisted Feedback in Grade 9 Writing",
            description="A small, time-boxed pilot where teachers use AI tools to provide formative, personalized writing feedback, with opt-in families and strict privacy rules.",
            scope="community",
            tags=["education", "technology", "ai", "pilot"],
            source="The Commons MVP",
        )
    ]


def get_demo_stories() -> List[StoryItem]:
    """Return demo stories when USE_DEMO_CONTENT is enabled."""
    return [
        StoryItem(
            id="demo-placeholder-story",
            title="Placeholder Story",
            summary="This is a placeholder story for demonstration purposes.",
            impact="Placeholder impact metrics",
            source="The Commons MVP",
        )
    ]


@router.get("/principles", response_model=ContentResponse)
async def get_principles() -> ContentResponse:
    """Get Level A principles (baseline policies)."""
    settings = get_settings()
    if settings.USE_DEMO_CONTENT:
        principles = get_demo_principles()
        source = "demo"
    else:
        principles = content_loader.load_principles()
        source = "file"

    return ContentResponse(items=principles, count=len(principles), source=source)


@router.get("/actions", response_model=ContentResponse)
async def get_actions() -> ContentResponse:
    """Get Level B actions (specific proposals)."""
    settings = get_settings()
    if settings.USE_DEMO_CONTENT:
        actions = get_demo_actions()
        source = "demo"
    else:
        actions = content_loader.load_actions()
        source = "file"

    return ContentResponse(items=actions, count=len(actions), source=source)


@router.get("/stories", response_model=ContentResponse)
async def get_stories() -> ContentResponse:
    """Get case studies and success stories."""
    settings = get_settings()
    if settings.USE_DEMO_CONTENT:
        stories = get_demo_stories()
        source = "demo"
    else:
        stories = content_loader.load_stories()
        source = "file"

    return ContentResponse(items=stories, count=len(stories), source=source)


@router.post("/cache/clear")
async def clear_content_cache() -> dict:
    """Clear the content cache (admin only)."""
    content_loader.clear_cache()
    return {"message": "Content cache cleared successfully"}
