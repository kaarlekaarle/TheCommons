from fastapi import APIRouter, HTTPException, Depends
from typing import List

from backend.config import get_settings
from backend.schemas.content import PrincipleItem, ActionItem, StoryItem, ContentResponse
from backend.services.content_loader import content_loader

router = APIRouter(prefix="/content", tags=["content"])


def get_demo_principles() -> List[PrincipleItem]:
    """Return demo principles when USE_DEMO_CONTENT is enabled."""
    return [
        PrincipleItem(
            id="demo-vision-zero",
            title="Vision Zero Commitment",
            description="Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.",
            tags=["safety", "mobility"],
            source="Demo content"
        ),
        PrincipleItem(
            id="demo-open-government",
            title="Open Government Policy",
            description="Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.",
            tags=["transparency", "governance"],
            source="Demo content"
        ),
        PrincipleItem(
            id="demo-green-building",
            title="Green Building Standard",
            description="All new municipal buildings and major renovations must meet LEED Silver or equivalent green building standards.",
            tags=["sustainability", "infrastructure"],
            source="Demo content"
        )
    ]


def get_demo_actions() -> List[ActionItem]:
    """Return demo actions when USE_DEMO_CONTENT is enabled."""
    return [
        ActionItem(
            id="demo-bike-lanes",
            title="Install protected bike lanes on Washington Avenue",
            description="Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.",
            scope="city",
            tags=["mobility", "safety"],
            source="Demo content"
        ),
        ActionItem(
            id="demo-composting",
            title="Launch curbside composting pilot",
            description="Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.",
            scope="city",
            tags=["waste", "sustainability"],
            source="Demo content"
        ),
        ActionItem(
            id="demo-library-hours",
            title="Extend public library hours",
            description="Extend public library hours to 9 PM on weekdays for six-month trial to improve access for working families and students.",
            scope="city",
            tags=["education", "accessibility"],
            source="Demo content"
        )
    ]


def get_demo_stories() -> List[StoryItem]:
    """Return demo stories when USE_DEMO_CONTENT is enabled."""
    return [
        StoryItem(
            id="demo-vision-zero-success",
            title="Vision Zero Implementation",
            summary="Reduced traffic fatalities by 40% through street redesign and safety improvements.",
            impact="40% reduction in traffic fatalities",
            source="Demo content"
        ),
        StoryItem(
            id="demo-open-government-success",
            title="Open Government Initiative",
            summary="Published 200+ datasets, leading to better-informed community decisions.",
            impact="200+ datasets published",
            source="Demo content"
        ),
        StoryItem(
            id="demo-green-building-success",
            title="Green Building Program",
            summary="Retrofitted 15 public buildings, cutting energy costs by 30%.",
            impact="30% reduction in energy costs",
            source="Demo content"
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
    
    return ContentResponse(
        items=principles,
        count=len(principles),
        source=source
    )


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
    
    return ContentResponse(
        items=actions,
        count=len(actions),
        source=source
    )


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
    
    return ContentResponse(
        items=stories,
        count=len(stories),
        source=source
    )


@router.post("/cache/clear")
async def clear_content_cache() -> dict:
    """Clear the content cache (admin only)."""
    content_loader.clear_cache()
    return {"message": "Content cache cleared successfully"}
