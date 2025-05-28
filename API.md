# The Commons API Documentation

This document provides detailed information about The Commons API endpoints, their functionality, and usage.

## Authentication

All API endpoints except `/api/token` require authentication using a Bearer token.

### Get Access Token

```http
POST /api/token
```

Authenticate a user and receive an access token.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

**Status Codes:**
- `200 OK`: Authentication successful
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Server error

### Get Current User

```http
GET /api/me
```

Get information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "is_active": "boolean"
}
```

**Status Codes:**
- `200 OK`: User information retrieved
- `401 Unauthorized`: Invalid or missing token
- `500 Internal Server Error`: Server error

## Polls

### Create Poll

```http
POST /api/polls/
```

Create a new poll.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "title": "string",
    "description": "string"
}
```

**Response:**
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "created_by": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `201 Created`: Poll created successfully
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Invalid poll data
- `500 Internal Server Error`: Server error

### List Polls

```http
GET /api/polls/
```

Get a list of all polls.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)

**Response:**
```json
[
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "created_by": "integer",
        "created_at": "string",
        "updated_at": "string"
    }
]
```

**Status Codes:**
- `200 OK`: Polls retrieved successfully
- `500 Internal Server Error`: Server error

### Get Poll

```http
GET /api/polls/{poll_id}
```

Get a specific poll by ID.

**Path Parameters:**
- `poll_id` (integer): ID of the poll

**Response:**
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "created_by": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Poll retrieved successfully
- `404 Not Found`: Poll not found
- `500 Internal Server Error`: Server error

### Update Poll

```http
PUT /api/polls/{poll_id}
```

Update an existing poll.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `poll_id` (integer): ID of the poll

**Request Body:**
```json
{
    "title": "string",
    "description": "string"
}
```

**Response:**
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "created_by": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Poll updated successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to update poll
- `404 Not Found`: Poll not found
- `422 Unprocessable Entity`: Invalid update data
- `500 Internal Server Error`: Server error

### Delete Poll

```http
DELETE /api/polls/{poll_id}
```

Delete a poll.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `poll_id` (integer): ID of the poll

**Status Codes:**
- `204 No Content`: Poll deleted successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to delete poll
- `404 Not Found`: Poll not found
- `500 Internal Server Error`: Server error

## Votes

### Create Vote

```http
POST /api/votes/
```

Create a new vote.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "poll_id": "integer",
    "option_id": "integer",
    "weight": "integer"
}
```

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "option_id": "integer",
    "user_id": "integer",
    "weight": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `201 Created`: Vote created successfully
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Invalid vote data
- `500 Internal Server Error`: Server error

### List Votes

```http
GET /api/votes/
```

Get a list of all votes (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)

**Response:**
```json
[
    {
        "id": "integer",
        "poll_id": "integer",
        "option_id": "integer",
        "user_id": "integer",
        "weight": "integer",
        "created_at": "string",
        "updated_at": "string"
    }
]
```

**Status Codes:**
- `200 OK`: Votes retrieved successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized
- `500 Internal Server Error`: Server error

### Get Vote

```http
GET /api/votes/{vote_id}
```

Get a specific vote by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `vote_id` (integer): ID of the vote

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "option_id": "integer",
    "user_id": "integer",
    "weight": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Vote retrieved successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to view this vote
- `404 Not Found`: Vote not found
- `500 Internal Server Error`: Server error

### Update Vote

```http
PUT /api/votes/{vote_id}
PATCH /api/votes/{vote_id}
```

Update an existing vote.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `vote_id` (integer): ID of the vote

**Request Body:**
```json
{
    "option_id": "integer",
    "weight": "integer"
}
```

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "option_id": "integer",
    "user_id": "integer",
    "weight": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Vote updated successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to update vote
- `404 Not Found`: Vote not found
- `422 Unprocessable Entity`: Invalid update data
- `500 Internal Server Error`: Server error

### Delete Vote

```http
DELETE /api/votes/{vote_id}
```

Delete a vote.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `vote_id` (integer): ID of the vote

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "option_id": "integer",
    "user_id": "integer",
    "weight": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Vote deleted successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to delete vote
- `404 Not Found`: Vote not found
- `500 Internal Server Error`: Server error

### Cast Vote

```http
POST /api/votes/{vote_id}/cast
```

Cast a vote for a specific option.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `vote_id` (integer): ID of the vote

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "option_id": "integer",
    "user_id": "integer",
    "weight": "integer",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Vote cast successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to cast vote
- `404 Not Found`: Vote not found
- `422 Unprocessable Entity`: Invalid vote data
- `500 Internal Server Error`: Server error

## Options

### Create Option

```http
POST /api/options/
```

Create a new option for a poll.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "poll_id": "integer",
    "text": "string",
    "description": "string"
}
```

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "text": "string",
    "description": "string",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `201 Created`: Option created successfully
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Invalid option data
- `500 Internal Server Error`: Server error

### List Options

```http
GET /api/options/
```

Get a list of all options.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100)
- `poll_id` (integer, optional): Filter options by poll ID

**Response:**
```json
[
    {
        "id": "integer",
        "poll_id": "integer",
        "text": "string",
        "description": "string",
        "created_at": "string",
        "updated_at": "string"
    }
]
```

**Status Codes:**
- `200 OK`: Options retrieved successfully
- `500 Internal Server Error`: Server error

### Get Option

```http
GET /api/options/{option_id}
```

Get a specific option by ID.

**Path Parameters:**
- `option_id` (integer): ID of the option

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "text": "string",
    "description": "string",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Option retrieved successfully
- `404 Not Found`: Option not found
- `500 Internal Server Error`: Server error

### Update Option

```http
PUT /api/options/{option_id}
```

Update an existing option.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `option_id` (integer): ID of the option

**Request Body:**
```json
{
    "text": "string",
    "description": "string"
}
```

**Response:**
```json
{
    "id": "integer",
    "poll_id": "integer",
    "text": "string",
    "description": "string",
    "created_at": "string",
    "updated_at": "string"
}
```

**Status Codes:**
- `200 OK`: Option updated successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to update option
- `404 Not Found`: Option not found
- `422 Unprocessable Entity`: Invalid update data
- `500 Internal Server Error`: Server error

### Delete Option

```http
DELETE /api/options/{option_id}
```

Delete an option.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `option_id` (integer): ID of the option

**Status Codes:**
- `204 No Content`: Option deleted successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: User not authorized to delete option
- `404 Not Found`: Option not found
- `500 Internal Server Error`: Server error

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
    "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
    "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
    "detail": "Validation error",
    "errors": [
        {
            "loc": ["string"],
            "msg": "string",
            "type": "string"
        }
    ]
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:
- 60 requests per minute per IP address

When rate limit is exceeded, the API will return:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

## Best Practices

1. **Authentication**
   - Always include the Bearer token in the Authorization header
   - Store tokens securely
   - Implement token refresh mechanism for long-running applications

2. **Error Handling**
   - Implement proper error handling for all API responses
   - Check status codes before processing responses
   - Handle rate limiting gracefully

3. **Data Validation**
   - Validate all input data before sending to the API
   - Handle validation errors appropriately
   - Use appropriate data types for all fields

4. **Security**
   - Use HTTPS for all API requests
   - Never store sensitive data in client-side storage
   - Implement proper session management