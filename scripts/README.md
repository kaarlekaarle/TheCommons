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

## Riverbend Demo Seeding

### `seed_demo_city.py`
A comprehensive demo seeding script that creates a realistic small-city community called "Riverbend" with:

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
- Install protected bike lanes on Oak Street from Central Park to City Hall
- Launch 12-month curbside compost pickup pilot in three neighborhoods
- Extend Saturday library hours from 5 PM to 8 PM for six-month trial
- Plant 500 street trees along major bus routes
- Install 20 public water refill stations in parks and downtown areas
- Retrofit lighting in all public schools with energy-efficient LEDs
- Add wheelchair-accessible seating and pathways in Riverside Park
- Create weekly "car-free Sunday" on Main Avenue during summer months
- Launch local food voucher program for low-income households
- Replace diesel buses on Route 6 with electric buses within 18 months
- Start youth apprenticeship program in city maintenance departments
- Create protected pedestrian crossing at 5th and Market
- Run public art mural program in underutilized spaces downtown
- Upgrade stormwater drains in flood-prone neighborhoods
- Pilot mobile mental health support unit operating three days a week
- Offer free Wi-Fi in all public libraries and recreation centers
- Expand community policing foot patrols to two additional neighborhoods
- Begin construction of skate park in Westside Recreation Area
- Install traffic-calming speed tables on Oak Drive near elementary school
- Provide grants for storefront energy-efficiency upgrades to 20 small businesses
- Introduce on-demand evening bus service for shift workers in industrial park
- Convert vacant lot at 14th and Pine into temporary community garden for two years
- Offer free weekend transit for youth under 18 for one-year pilot
- Create citywide tool library where residents can borrow equipment for home projects
- Add shaded seating areas to three senior housing complexes
- Implement bilingual signage in all city-owned buildings
- Start bike-share program with 100 bikes at 10 docking stations
- Build public charging station hub for electric vehicles in central parking lot
- Restore historic fountain in Civic Plaza
- Add two new trash and recycling bins per block in downtown core

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
