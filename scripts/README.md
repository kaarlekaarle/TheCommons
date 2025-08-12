# Seeding Scripts

This directory contains scripts for seeding test data and measuring performance.

## Scripts

### `test_seed_small.py`
A small-scale test script that creates:
- 1 poll with 2 options
- 5 users voting directly for Option A
- 5 users delegating their votes to direct voters
- Measures performance of the poll results endpoint

**Usage:**
```bash
# Local environment
python scripts/test_seed_small.py

# Docker environment
docker compose exec web python scripts/test_seed_small.py
```

### `seed_large_poll.py`
A large-scale performance test script that creates:
- 1 poll with 2 options
- 500 users voting directly for Option A
- 500 users delegating their votes in chains to direct voters
- Measures performance of the poll results endpoint

**Usage:**
```bash
# Local environment
python scripts/seed_large_poll.py

# Docker environment
docker compose exec web python scripts/seed_large_poll.py
```

## Prerequisites

### Local Environment
1. **Database**: PostgreSQL must be running with the `the_commons` database
2. **API Server**: FastAPI server must be running on `http://localhost:8000`
3. **Dependencies**: Install httpx for HTTP client functionality
   ```bash
   pip install httpx
   ```

### Docker Environment
1. **Docker Compose**: All services must be running
   ```bash
   docker compose up -d
   ```
2. **Database**: PostgreSQL service (`db`) must be healthy
3. **API Server**: Web service (`web`) must be running

## Expected Results

### Small Test
- **Total users**: 11 (1 creator + 5 direct voters + 5 delegators)
- **Direct votes**: 5
- **Delegations**: 5
- **Expected Option A total**: 10 votes (5 direct + 5 delegated)
- **Expected Option B total**: 0 votes

### Large Test
- **Total users**: 1001 (1 creator + 500 direct voters + 500 delegators)
- **Direct votes**: 500
- **Delegations**: 500
- **Expected Option A total**: 1000 votes (500 direct + 500 delegated)
- **Expected Option B total**: 0 votes

## Performance Measurement

Both scripts measure the response time of the `/api/polls/{poll_id}/results` endpoint, which:
1. Calculates direct votes for each option
2. Resolves delegation chains to find final delegatees
3. Adds delegated votes to the final delegatees' chosen options
4. Returns aggregated results

## Notes

- The scripts use the existing database models and async session handling
- All users are created with predictable usernames and passwords
- The poll creator can authenticate to test the results endpoint
- Delegations are simple 1:1 chains (each delegator delegates to one direct voter)
- All votes are cast for Option A to create a clear performance test scenario

## Springfield Demo Seeding

### `seed_demo_city.py`
A comprehensive demo seeding script that creates a realistic small-city community called "Springfield" with:

**Users (12):**
- mayor, cityplanner, teacher, shop_owner, student, nurse, cyclist, driver, parent, librarian, waste_manager, developer
- All users: password123

**Level A (Baseline Policy) Proposals (10):**
- Vision Zero Commitment
- Open Government Policy
- Green Building Standard
- Affordable Housing Priority
- Public Space Access
- Climate Action Framework
- Digital Inclusion
- Local Food Commitment
- Mobility for All
- Zero Waste Commitment

**Level B (Poll) Proposals (30):**
- Install protected bike lanes on Washington Avenue from downtown to university district
- Launch 18-month curbside composting pilot in four residential neighborhoods
- Extend public library hours to 9 PM on weekdays for six-month trial
- Plant 750 street trees along major transit corridors and in underserved neighborhoods
- Install 25 public water refill stations in parks, schools, and community centers
- Retrofit lighting in all municipal buildings with energy-efficient LED systems
- Add wheelchair-accessible seating and improved pathways in Central Park
- Create monthly "Open Streets" program on Main Street during summer months
- Launch local food voucher program for 300 low-income households
- Replace diesel buses on Route 8 with electric buses within 24 months
- Start youth apprenticeship program in city maintenance and parks departments
- Create protected pedestrian crossing at 3rd and Market intersection
- Run public art mural program in underutilized downtown spaces
- Upgrade stormwater drainage system in flood-prone areas
- Pilot mobile mental health crisis response unit operating five days per week
- Offer free Wi-Fi in all public libraries, recreation centers, and community spaces
- Expand community policing foot patrols to three additional neighborhoods
- Begin construction of inclusive playground in Westside Recreation Area
- Install traffic-calming speed humps on Oak Drive near elementary school
- Provide energy-efficiency grants to 25 small businesses for storefront upgrades
- Introduce on-demand evening bus service for shift workers in industrial district
- Convert vacant lot at 12th and Pine into community garden for three years
- Offer free weekend transit for youth under 18 for 18-month pilot
- Create citywide tool and equipment lending library
- Add shaded seating areas to four senior housing complexes
- Implement bilingual signage in all city-owned buildings and facilities
- Start bike-share program with 150 bikes at 15 docking stations
- Build public charging station hub for electric vehicles in central parking garage
- Restore historic bandshell in Memorial Park
- Add three new trash and recycling bins per block in downtown core

**Content:**
- 20+ comments with PRO:/CON: prefixes
- 40+ votes across Level B proposals
- 3 delegations (student→cityplanner, shop_owner→cityplanner, driver→mayor)

**Safety:**
- Script is idempotent and safe to re-run

**Usage:**
```bash
# Docker environment (recommended)
docker compose exec web python scripts/seed_demo_city.py --reset

# Local environment
export DATABASE_URL="sqlite+aiosqlite:///test.db"
python scripts/seed_demo_city.py --reset

# Options
--reset      Delete existing demo content and re-seed (default)
--no-reset   Skip deletion, only add missing demo content  
--users-only Only create demo users, skip proposals/votes/comments
```

**Re-seeding:**
```bash
# Clean slate
python scripts/seed_demo_city.py --reset

# Add missing content only
python scripts/seed_demo_city.py --no-reset
```

**Demo Credentials:**
- Username: any of the demo usernames (mayor, cityplanner, etc.)
- Password: password123
