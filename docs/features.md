# The Commons – Features Overview

The Commons is an open platform for participatory decision-making, enabling dynamic delegation, real-time voting, and transparent tracking of all actions. This document outlines the current and planned features of the system.

---

## Core Features

### Dynamic Delegation System
- Delegate voting power to trusted users
- Revoke delegations at any time
- Delegation chains with max depth limit
- One active delegation per scope (poll-specific or general)

### Voting System
- Poll creation (single-choice or multiple-choice, time-limited)
- Vote casting with delegation resolution
- Transparent vote counting
- Public audit trails of votes

### Transparency Layer (Activity Feed)
- Public log of all user actions:
  - Votes cast
  - Delegations created/revoked
  - Polls created/closed
- API access with pagination and filters

### Security
- JWT authentication and token refresh
- Password hashing with bcrypt
- Role-based access control
- Rate limiting and session management via Redis
- Input validation and sanitization

### Performance and Scalability
- Async request handling
- Connection pooling
- Redis caching
- Docker support for deployment

---

## Planned Features

- Trust metrics and reputation system
- Delegation visualization tools
- Group/community features
- Governance tools
- Frontend client
- Real-time updates (WebSockets)
- Mobile support

---

## Technical Stack

- FastAPI (backend framework)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- Redis (caching)
- Alembic (migrations)
- Pytest (testing)
- Docker (containerization)

---

This document will evolve as the project grows.