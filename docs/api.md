# The Commons – API Overview

This document outlines the key API endpoints of The Commons system. The API is RESTful, built with FastAPI, and designed to support real-time decision-making and transparent participation.

---

## Core Endpoints

### Authentication
- `POST /api/token` – Obtain JWT token
- `POST /api/token/refresh` – Refresh JWT token

---

### Users
- `GET /api/users/me` – Get current user info
- `POST /api/users/` – Create new user

---

### Polls
- `GET /api/polls/` – List all polls
- `POST /api/polls/` – Create a new poll
- `GET /api/polls/{poll_id}` – Get poll details

---

### Votes
- `POST /api/votes/` – Cast a vote
- `GET /api/votes/{poll_id}` – Get votes for a poll (with delegation resolution)

---

### Delegations
- `POST /api/delegations/` – Create a delegation (poll-specific or general)
- `DELETE /api/delegations/{id}` – Revoke a delegation
- `GET /api/delegations/active` – List active delegations for the current user
- `GET /api/delegations/resolve/{poll_id}` – Resolve delegation chain for a poll

---

### Activity Feed (Transparency Layer)
- `GET /api/activity-feed/` – List all user actions
  - Supports filters: `user_id`, `action_type`
  - Supports pagination: `limit`, `offset`

---

## API Design Notes
- All endpoints use JWT authentication (except `POST /api/token`).
- Requests and responses follow JSON format.
- Validation and error handling are consistent across endpoints.
- Rate limiting is in place to prevent abuse.

---

This document will evolve as the API develops. For full schema details, see the source code.