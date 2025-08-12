# Content Pipeline Documentation

The Commons includes a flexible content pipeline that allows you to serve real community data instead of demo content. This system is feature-flagged and can be easily switched between demo and real data sources.

## Overview

The content pipeline provides:
- **Principles** (Level A): Long-term baseline policies and values
- **Actions** (Level B): Specific proposals and initiatives  
- **Stories**: Case studies and success stories for the landing page

## Configuration

### Environment Variables

#### Backend
```bash
# Content pipeline settings
USE_DEMO_CONTENT=false                    # Default: false (use real data)
CONTENT_DATA_DIR=./data/real_content     # Default: ./data/real_content
```

#### Frontend
```bash
# Content pipeline feature flag
VITE_USE_DEMO_CONTENT=false              # Default: false (use real data)
```

### Behavior by Environment

**Development**: 
- `USE_DEMO_CONTENT=true` - Shows demo content for development
- `USE_DEMO_CONTENT=false` - Loads from `CONTENT_DATA_DIR`

**Production**:
- `USE_DEMO_CONTENT=false` - Always loads from `CONTENT_DATA_DIR`
- `VITE_USE_DEMO_CONTENT=false` - Frontend fetches from API

## File Formats

### JSON Structure

All content files use JSON format with arrays of objects:

#### principles.json
```json
[
  {
    "id": "p-open-data",
    "title": "Open Data & Transparency",
    "description": "Publish decisions, datasets, and rationales openly by default.",
    "tags": ["governance", "transparency"],
    "source": "Public policy frameworks"
  }
]
```

#### actions.json
```json
[
  {
    "id": "a-bike-lane-main",
    "title": "Install protected bike lanes on Main St",
    "description": "Add protected bicycle lanes along Main Street from downtown to the university district.",
    "scope": "city",
    "tags": ["mobility"],
    "source": "Municipal agenda examples"
  }
]
```

#### stories.json
```json
[
  {
    "id": "s-park-renewal",
    "title": "Park Renewal via Community Vote",
    "summary": "Residents prioritized shading, seating, and play areas in the downtown park redesign.",
    "impact": "Higher park usage, fewer incidents, increased community satisfaction",
    "link": ""
  }
]
```

### Field Descriptions

#### PrincipleItem
- `id`: Unique identifier (required)
- `title`: Short, descriptive title (required)
- `description`: Detailed description (required)
- `tags`: Array of categories/tags (optional)
- `source`: Source or origin (optional)

#### ActionItem
- `id`: Unique identifier (required)
- `title`: Short, descriptive title (required)
- `description`: Detailed description (required)
- `scope`: Scope (city, district, org, etc.) (optional)
- `tags`: Array of categories/tags (optional)
- `source`: Source or origin (optional)

#### StoryItem
- `id`: Unique identifier (required)
- `title`: Short, descriptive title (required)
- `summary`: Brief summary (required)
- `impact`: Measurable impact or outcomes (optional)
- `link`: URL to more details (optional)

## API Endpoints

### Get Principles
```bash
GET /api/content/principles
```

**Response:**
```json
{
  "items": [
    {
      "id": "p-open-data",
      "title": "Open Data & Transparency",
      "description": "Publish decisions, datasets, and rationales openly by default.",
      "tags": ["governance", "transparency"],
      "source": "Public policy frameworks"
    }
  ],
  "count": 1,
  "source": "file"
}
```

### Get Actions
```bash
GET /api/content/actions
```

**Response:**
```json
{
  "items": [
    {
      "id": "a-bike-lane-main",
      "title": "Install protected bike lanes on Main St",
      "description": "Add protected bicycle lanes along Main Street.",
      "scope": "city",
      "tags": ["mobility"],
      "source": "Municipal agenda examples"
    }
  ],
  "count": 1,
  "source": "file"
}
```

### Get Stories
```bash
GET /api/content/stories
```

**Response:**
```json
{
  "items": [
    {
      "id": "s-park-renewal",
      "title": "Park Renewal via Community Vote",
      "summary": "Residents prioritized shading, seating, and play areas.",
      "impact": "Higher park usage, fewer incidents",
      "link": ""
    }
  ],
  "count": 1,
  "source": "file"
}
```

### Clear Cache
```bash
POST /api/content/cache/clear
```

**Response:**
```json
{
  "message": "Content cache cleared successfully"
}
```

## Adding Real Municipal Data

### Step 1: Prepare Your Data

1. **Extract from existing sources:**
   - Municipal policy documents
   - City council agendas
   - Public records
   - Community feedback

2. **Format as JSON:**
   - Follow the schema above
   - Use consistent IDs (e.g., `p-{category}-{number}`)
   - Add appropriate tags for categorization

### Step 2: Replace Content Files

```bash
# Backup existing files
cp data/real_content/principles.json data/real_content/principles.json.backup

# Replace with your data
cp your-municipal-principles.json data/real_content/principles.json
cp your-municipal-actions.json data/real_content/actions.json
cp your-municipal-stories.json data/real_content/stories.json
```

### Step 3: Verify

```bash
# Test the API endpoints
curl http://localhost:8000/api/content/principles
curl http://localhost:8000/api/content/actions
curl http://localhost:8000/api/content/stories
```

### Step 4: Clear Cache (if needed)

```bash
curl -X POST http://localhost:8000/api/content/cache/clear
```

## Example: Converting Municipal Data

### From City Council Agenda
**Original:**
```
Item 4.3: Install protected bike lanes on Washington Avenue
Description: Add dedicated bicycle lanes along Washington Avenue from downtown to university district
Budget: $450,000
```

**Converted to actions.json:**
```json
{
  "id": "a-bike-lane-washington",
  "title": "Install protected bike lanes on Washington Avenue",
  "description": "Add dedicated bicycle lanes along Washington Avenue from downtown to university district. Budget: $450,000",
  "scope": "city",
  "tags": ["mobility", "infrastructure"],
  "source": "City Council Agenda - March 2024"
}
```

### From Municipal Policy
**Original:**
```
Vision Zero Policy: Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.
```

**Converted to principles.json:**
```json
{
  "id": "p-vision-zero",
  "title": "Vision Zero Commitment",
  "description": "Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.",
  "tags": ["safety", "mobility"],
  "source": "Municipal Transportation Policy"
}
```

## Optional: Convert to Database Proposals

Use the seed script to convert file content into actual proposals:

```bash
# Dry run to see what would be created
python backend/scripts/load_seed_from_files.py --dry-run

# Create Level A proposals from principles
python backend/scripts/load_seed_from_files.py --principles

# Create Level B proposals from actions
python backend/scripts/load_seed_from_files.py --actions

# Create both
python backend/scripts/load_seed_from_files.py --all
```

## Caching

The content system includes automatic caching:
- **Cache TTL**: 5 minutes
- **File monitoring**: Cache invalidated when files change
- **Manual clear**: Use `/api/content/cache/clear` endpoint

## Error Handling

The system gracefully handles:
- Missing files (returns empty arrays)
- Malformed JSON (logs warnings, skips invalid items)
- Network errors (frontend shows fallback states)

## Testing

### Backend Tests
```bash
# Run content API tests
pytest backend/tests/test_content_api.py -v
```

### Frontend Tests
```bash
# Run content component tests
npm test -- --run src/components/content/__tests__/
```

## Troubleshooting

### Content Not Loading
1. Check file permissions: `ls -la data/real_content/`
2. Verify JSON syntax: `python -m json.tool data/real_content/principles.json`
3. Check logs: `docker-compose logs web | grep content`

### Cache Issues
1. Clear cache: `curl -X POST http://localhost:8000/api/content/cache/clear`
2. Restart backend: `docker-compose restart web`

### Frontend Not Updating
1. Check feature flag: `echo $VITE_USE_DEMO_CONTENT`
2. Clear browser cache
3. Check network tab for API errors

## Future Enhancements

### CSV Support
Future versions may support CSV files alongside JSON:
```bash
# Future: CSV support
CONTENT_DATA_FORMAT=csv  # or json
```

### Admin Upload
Future versions may include admin endpoints for uploading content:
```bash
# Future: Admin upload endpoints
POST /api/admin/content/principles
POST /api/admin/content/actions
POST /api/admin/content/stories
```

### Real-time Updates
Future versions may support WebSocket updates when content files change.

## Best Practices

1. **Use consistent IDs**: Follow a naming convention (e.g., `p-{category}-{number}`)
2. **Add meaningful tags**: Help with categorization and filtering
3. **Include sources**: Track where content comes from
4. **Regular updates**: Keep content fresh and relevant
5. **Backup files**: Version control your content files
6. **Test changes**: Verify API responses after updates
