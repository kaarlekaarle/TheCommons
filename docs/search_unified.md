# Unified Search: People, Fields, and Institutions

This document describes the unified search functionality that allows searching across people, fields, and institutions in a single interface.

## Overview

The unified search system provides a single endpoint to search across different types of entities that can be delegated to:

- **People**: Users who can receive delegations
- **Fields**: Domains of expertise or interest
- **Institutions**: Organizations that can receive delegations

## API Reference

### Search Endpoint

```http
GET /api/delegations/search/unified
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (minimum 1 character) |
| `types` | string | No | Comma-separated list of target types (default: "people,fields,institutions") |
| `limit` | integer | No | Maximum number of results (default: 20, max: 100) |

### Target Types

- `people`: Search for users
- `fields`: Search for fields of expertise
- `institutions`: Search for institutions
- `values`: Search for constitutional values
- `ideas`: Search for ideas

### Example Request

```bash
curl -X GET "/api/delegations/search/unified?q=climate&types=people,fields,institutions&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Response Format

The response is an array of search results with a normalized structure:

```json
[
  {
    "type": "user|field|institution",
    "id": "uuid",
    "name": "Display name",
    "slug": "url-slug",
    "description": "Description text",
    "meta": {
      // Type-specific metadata
    }
  }
]
```

## Search Behavior

### Relevance Scoring

Results are ordered by relevance using a simple scoring system:

1. **Exact match** (score: 3): Query exactly matches name
2. **Starts with** (score: 2): Name starts with query
3. **Contains** (score: 1): Query appears anywhere in name/description
4. **No match** (score: 0): No relevance

### Case Insensitive

All searches are case insensitive.

### Partial Matching

Searches match partial strings in names and descriptions.

## Entity Types

### People (Users)

**Searchable Fields**:
- Username
- Display name
- Bio

**Response Example**:
```json
{
  "type": "user",
  "id": "user-123",
  "name": "Alice Johnson",
  "slug": "alice-johnson",
  "description": "Climate policy expert with 10 years experience",
  "meta": {
    "username": "alice-johnson",
    "email": "alice@example.com",
    "created_at": "2023-01-15T10:30:00Z"
  }
}
```

### Fields

**Searchable Fields**:
- Name
- Slug
- Description

**Response Example**:
```json
{
  "type": "field",
  "id": "field-456",
  "name": "Climate Policy",
  "slug": "climate-policy",
  "description": "Climate and environmental policy",
  "meta": {
    "created_at": "2023-02-20T14:15:00Z"
  }
}
```

### Institutions

**Searchable Fields**:
- Name
- Slug
- Description
- Kind (NGO, cooperative, party, civic, other)

**Response Example**:
```json
{
  "type": "institution",
  "id": "inst-789",
  "name": "Greenpeace",
  "slug": "greenpeace",
  "description": "Environmental protection organization",
  "meta": {
    "kind": "ngo",
    "url": "https://greenpeace.org",
    "created_at": "2023-03-10T09:45:00Z"
  }
}
```

## Use Cases

### Delegation Target Selection

Use unified search to find delegation targets:

```javascript
// Search for climate experts
const results = await fetch('/api/delegations/search/unified?q=climate&types=people,fields')
  .then(r => r.json());

// Display results for user selection
results.forEach(result => {
  console.log(`${result.name} (${result.type})`);
});
```

### Field Discovery

Discover available fields of expertise:

```javascript
// Search for policy-related fields
const fields = await fetch('/api/delegations/search/unified?q=policy&types=fields')
  .then(r => r.json());

// Show available fields
fields.forEach(field => {
  console.log(`Field: ${field.name} - ${field.description}`);
});
```

### Institution Lookup

Find institutions for delegation:

```javascript
// Search for environmental institutions
const institutions = await fetch('/api/delegations/search/unified?q=environmental&types=institutions')
  .then(r => r.json());

// Display institutions
institutions.forEach(inst => {
  console.log(`${inst.name} (${inst.meta.kind}) - ${inst.description}`);
});
```

## Implementation Details

### Database Queries

The search uses SQL LIKE queries with case-insensitive matching:

```sql
-- People search
SELECT * FROM users 
WHERE is_deleted = false 
  AND (username ILIKE '%query%' 
       OR display_name ILIKE '%query%' 
       OR bio ILIKE '%query%')

-- Fields search  
SELECT * FROM fields
WHERE is_active = true
  AND (name ILIKE '%query%'
       OR slug ILIKE '%query%'
       OR description ILIKE '%query%')

-- Institutions search
SELECT * FROM institutions  
WHERE is_active = true
  AND (name ILIKE '%query%'
       OR slug ILIKE '%query%'
       OR description ILIKE '%query%')
```

### Performance Considerations

- Results are limited to prevent performance issues
- Queries use database indexes on searchable fields
- Case-insensitive matching is handled at the database level
- Results are cached for frequently searched terms

### Security

- Search results respect user privacy settings
- Anonymous delegations are handled appropriately
- Access control is enforced based on user permissions

## Error Handling

### Common Errors

**400 Bad Request**: Invalid parameters
```json
{
  "error": "Invalid search query",
  "details": "Query must be at least 1 character"
}
```

**401 Unauthorized**: Missing or invalid token
```json
{
  "error": "Authentication required"
}
```

**500 Internal Server Error**: Database or system error
```json
{
  "error": "Search service unavailable"
}
```

### Rate Limiting

Search requests are rate limited to prevent abuse:
- 60 requests per minute per user
- 1000 requests per hour per user

## Best Practices

### Query Optimization

1. **Use specific types**: Limit search to relevant entity types
2. **Reasonable limits**: Use appropriate result limits
3. **Meaningful queries**: Use descriptive search terms

### User Experience

1. **Debounce input**: Wait for user to stop typing before searching
2. **Show loading states**: Indicate when search is in progress
3. **Handle empty results**: Provide helpful feedback for no matches
4. **Keyboard navigation**: Support arrow keys for result selection

### Performance

1. **Cache results**: Cache frequently searched terms
2. **Pagination**: Use pagination for large result sets
3. **Lazy loading**: Load additional results as needed

## Examples

### Complete Search Implementation

```javascript
class UnifiedSearch {
  constructor() {
    this.debounceTimeout = null;
    this.currentQuery = '';
  }

  async search(query, types = 'people,fields,institutions', limit = 20) {
    // Clear previous timeout
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }

    // Debounce search
    return new Promise((resolve) => {
      this.debounceTimeout = setTimeout(async () => {
        try {
          const response = await fetch(
            `/api/delegations/search/unified?q=${encodeURIComponent(query)}&types=${types}&limit=${limit}`,
            {
              headers: {
                'Authorization': `Bearer ${getToken()}`
              }
            }
          );

          if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
          }

          const results = await response.json();
          resolve(results);
        } catch (error) {
          console.error('Search error:', error);
          resolve([]);
        }
      }, 300); // 300ms debounce
    });
  }

  renderResults(results, onSelect) {
    return results.map(result => (
      <div 
        key={`${result.type}-${result.id}`}
        className="search-result"
        onClick={() => onSelect(result)}
      >
        <div className="result-name">{result.name}</div>
        <div className="result-type">{result.type}</div>
        <div className="result-description">{result.description}</div>
      </div>
    ));
  }
}
```

### React Hook Example

```javascript
function useUnifiedSearch() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query, types, limit) => {
    if (!query || query.length < 1) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/delegations/search/unified?q=${encodeURIComponent(query)}&types=${types}&limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
}
```

## Future Enhancements

### Planned Features

1. **Fuzzy matching**: Support for typos and approximate matches
2. **Semantic search**: AI-powered semantic understanding
3. **Search suggestions**: Auto-complete and search suggestions
4. **Advanced filters**: Filter by creation date, activity level, etc.
5. **Search analytics**: Track popular searches and improve relevance

### Integration Opportunities

1. **Delegation UI**: Integrate with delegation creation interface
2. **User profiles**: Link to detailed user/institution profiles
3. **Activity feeds**: Show recent activity for search results
4. **Recommendations**: Suggest related entities based on search history
