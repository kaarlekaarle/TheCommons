#!/usr/bin/env python3
"""
Riverbend Demo City Seeding Script

Creates a realistic small-city community with Level A (baseline policy) and Level B (poll) proposals,
including comments, votes, and delegations.

Usage:
    python scripts/seed_demo_city.py [--reset|--no-reset|--users-only]

Options:
    --reset      Delete existing demo content and re-seed (default)
    --no-reset   Skip deletion, only add missing demo content
    --users-only Only create demo users, skip proposals/votes/comments
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import uuid4, UUID

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from sqlalchemy import select, delete, and_, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll, DecisionType
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.comment import Comment
from backend.models.delegation import Delegation
from backend.core.security import get_password_hash
from backend.config import settings


# Demo user definitions
DEMO_USERS = [
    {'username': 'mayor', 'email': 'mayor@riverbend.example'},
    {'username': 'cityplanner', 'email': 'cityplanner@riverbend.example'},
    {'username': 'teacher', 'email': 'teacher@riverbend.example'},
    {'username': 'shop_owner', 'email': 'shop_owner@riverbend.example'},
    {'username': 'student', 'email': 'student@riverbend.example'},
    {'username': 'nurse', 'email': 'nurse@riverbend.example'},
    {'username': 'cyclist', 'email': 'cyclist@riverbend.example'},
    {'username': 'driver', 'email': 'driver@riverbend.example'},
    {'username': 'parent', 'email': 'parent@riverbend.example'},
    {'username': 'librarian', 'email': 'librarian@riverbend.example'},
    {'username': 'waste_manager', 'email': 'waste_manager@riverbend.example'},
    {'username': 'developer', 'email': 'developer@riverbend.example'},
]

# Level A (baseline policy) proposals
LEVEL_A_PROPOSALS = [
    {
        'title': 'Vision Zero Commitment',
        'description': 'Commit to designing streets so that no one is killed or seriously injured in traffic.',
        'direction_choice': "Transportation Safety"
    },
    {
        'title': 'Open Government Policy',
        'description': 'Publish public records and datasets unless there\'s a clear legal reason not to.',
        'direction_choice': "Government Transparency"
    },
    {
        'title': 'Green Building Standard',
        'description': 'Require all new public buildings to meet the city\'s highest energy-efficiency code.',
        'direction_choice': "Environmental Policy"
    },
    {
        'title': 'Affordable Housing Priority',
        'description': 'Prioritize affordable housing in land-use and zoning decisions.',
        'direction_choice': "Housing & Development"
    },
    {
        'title': 'Public Space Access',
        'description': 'Ensure all residents live within a 10-minute walk of a safe, accessible public space.',
        'direction_choice': "Parks & Recreation"
    },
    {
        'title': 'Climate Action Framework',
        'description': 'Cut greenhouse gas emissions 50% by 2035, across all city operations.',
        'direction_choice': "Climate & Sustainability"
    },
    {
        'title': 'Digital Inclusion',
        'description': 'Guarantee all households affordable access to high-speed internet.',
        'direction_choice': "Technology & Innovation"
    },
    {
        'title': 'Local Food Commitment',
        'description': 'Increase the share of food consumed in the city that is grown or produced locally.',
        'direction_choice': "Food Security"
    },
    {
        'title': 'Mobility for All',
        'description': 'Design transport systems that serve all ages and abilities.',
        'direction_choice': "Public Transit"
    },
    {
        'title': 'Zero Waste Commitment',
        'description': 'Commit to diverting all recyclable and compostable materials from landfills.',
        'direction_choice': "Waste Management"
    }
]

# Level B (poll) proposals
LEVEL_B_PROPOSALS = [
    {
        'title': 'Install protected bike lanes on Oak Street from Central Park to City Hall',
        'description': 'Add dedicated, protected bicycle lanes along Oak Street to improve cyclist safety and encourage active transportation.',
        'options': ['Approve', 'Modify plan', 'Reject']
    },
    {
        'title': 'Launch 12-month curbside compost pickup pilot in three neighborhoods',
        'description': 'Begin organic waste collection service in Downtown, Westside, and Riverside neighborhoods to reduce landfill waste.',
        'options': ['Approve', 'Reduce scope', 'Reject']
    },
    {
        'title': 'Extend Saturday library hours from 5 PM to 8 PM for six-month trial',
        'description': 'Extend operating hours at the main library to better serve students and working families.',
        'options': ['Approve', 'Modify hours', 'Reject']
    },
    {
        'title': 'Plant 500 street trees along major bus routes',
        'description': 'Add urban trees along transit corridors to improve air quality and provide shade for transit users.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Install 20 public water refill stations in parks and downtown areas',
        'description': 'Add drinking water stations to reduce plastic bottle waste and improve public health.',
        'options': ['Approve', 'Reduce locations', 'Reject']
    },
    {
        'title': 'Retrofit lighting in all public schools with energy-efficient LEDs',
        'description': 'Replace existing lighting systems in 12 public school buildings to reduce energy consumption and costs.',
        'options': ['Approve', 'Phase implementation', 'Reject']
    },
    {
        'title': 'Add wheelchair-accessible seating and pathways in Riverside Park',
        'description': 'Install accessible benches and improve pathway surfaces to ensure park access for all residents.',
        'options': ['Approve', 'Modify scope', 'Reject']
    },
    {
        'title': 'Create weekly "car-free Sunday" on Main Avenue during summer months',
        'description': 'Close Main Avenue to vehicle traffic every Sunday from June through August for community events and recreation.',
        'options': ['Approve', 'Reduce frequency', 'Reject']
    },
    {
        'title': 'Launch local food voucher program for low-income households',
        'description': 'Provide $50 monthly vouchers redeemable at farmers\' markets for 200 qualifying households.',
        'options': ['Approve', 'Reduce amount', 'Reject']
    },
    {
        'title': 'Replace diesel buses on Route 6 with electric buses within 18 months',
        'description': 'Purchase 8 electric buses to replace aging diesel vehicles on the downtown-to-airport route.',
        'options': ['Approve', 'Extend timeline', 'Reject']
    },
    {
        'title': 'Start youth apprenticeship program in city maintenance departments',
        'description': 'Create 15 paid apprenticeship positions for youth aged 16-24 in parks, streets, and facilities maintenance.',
        'options': ['Approve', 'Reduce positions', 'Reject']
    },
    {
        'title': 'Create protected pedestrian crossing at 5th and Market',
        'description': 'Install signalized crosswalk with pedestrian refuge island at the busy 5th and Market intersection.',
        'options': ['Approve', 'Modify design', 'Reject']
    },
    {
        'title': 'Run public art mural program in underutilized spaces downtown',
        'description': 'Commission 10 murals on blank walls and underpasses to improve visual appeal and support local artists.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Upgrade stormwater drains in flood-prone neighborhoods',
        'description': 'Replace and expand drainage infrastructure in three neighborhoods that experience regular flooding.',
        'options': ['Approve', 'Prioritize areas', 'Reject']
    },
    {
        'title': 'Pilot mobile mental health support unit operating three days a week',
        'description': 'Deploy a mobile crisis intervention team to provide immediate mental health support in high-need areas.',
        'options': ['Approve', 'Reduce days', 'Reject']
    },
    {
        'title': 'Offer free Wi-Fi in all public libraries and recreation centers',
        'description': 'Install and maintain wireless internet access in 8 public facilities to improve digital access.',
        'options': ['Approve', 'Limit locations', 'Reject']
    },
    {
        'title': 'Expand community policing foot patrols to two additional neighborhoods',
        'description': 'Add walking patrols in Eastside and Southside neighborhoods to improve community-police relations.',
        'options': ['Approve', 'Add one area', 'Reject']
    },
    {
        'title': 'Begin construction of skate park in Westside Recreation Area',
        'description': 'Build a 15,000 square foot skate park with beginner and advanced areas for youth recreation.',
        'options': ['Approve', 'Reduce size', 'Reject']
    },
    {
        'title': 'Install traffic-calming speed tables on Oak Drive near elementary school',
        'description': 'Add three speed tables on Oak Drive to reduce vehicle speeds and improve pedestrian safety near the school.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Provide grants for storefront energy-efficiency upgrades to 20 small businesses',
        'description': 'Offer $5,000 grants to small businesses for lighting, HVAC, and insulation improvements.',
        'options': ['Approve', 'Reduce amount', 'Reject']
    },
    {
        'title': 'Introduce on-demand evening bus service for shift workers in industrial park',
        'description': 'Launch flexible bus service from 6 PM to 2 AM to serve workers at the industrial park and surrounding areas.',
        'options': ['Approve', 'Reduce hours', 'Reject']
    },
    {
        'title': 'Convert vacant lot at 14th and Pine into temporary community garden for two years',
        'description': 'Transform the 0.5-acre vacant lot into a community garden with 30 plots and shared composting area.',
        'options': ['Approve', 'Reduce size', 'Reject']
    },
    {
        'title': 'Offer free weekend transit for youth under 18 for one-year pilot',
        'description': 'Provide free bus and train rides on Saturdays and Sundays for all youth to encourage independent mobility.',
        'options': ['Approve', 'Limit days', 'Reject']
    },
    {
        'title': 'Create citywide tool library where residents can borrow equipment for home projects',
        'description': 'Establish a lending library with 200 tools and equipment items available for 7-day borrowing periods.',
        'options': ['Approve', 'Reduce inventory', 'Reject']
    },
    {
        'title': 'Add shaded seating areas to three senior housing complexes',
        'description': 'Install covered benches and tables with shade structures at senior housing facilities to improve outdoor access.',
        'options': ['Approve', 'Reduce locations', 'Reject']
    },
    {
        'title': 'Implement bilingual signage in all city-owned buildings',
        'description': 'Add Spanish-language signs alongside English in all municipal buildings to improve accessibility.',
        'options': ['Approve', 'Phase implementation', 'Reject']
    },
    {
        'title': 'Start bike-share program with 100 bikes at 10 docking stations',
        'description': 'Launch a public bicycle sharing system with stations throughout downtown and adjacent neighborhoods.',
        'options': ['Approve', 'Reduce scale', 'Reject']
    },
    {
        'title': 'Build public charging station hub for electric vehicles in central parking lot',
        'description': 'Install 12 electric vehicle charging stations in the main downtown parking facility to support EV adoption.',
        'options': ['Approve', 'Reduce stations', 'Reject']
    },
    {
        'title': 'Restore historic fountain in Civic Plaza',
        'description': 'Repair and restore the 1920s fountain in Civic Plaza, including plumbing, electrical, and decorative elements.',
        'options': ['Approve', 'Modify scope', 'Reject']
    },
    {
        'title': 'Add two new trash and recycling bins per block in downtown core',
        'description': 'Install 40 new waste receptacles with separate recycling compartments throughout the downtown area.',
        'options': ['Approve', 'Reduce number', 'Reject']
    }
]

# Sample comments for proposals
SAMPLE_COMMENTS = {
    'bike_lanes': [
        {'text': 'PRO: Improves cyclist safety and encourages active transportation', 'user': 'cyclist'},
        {'text': 'CON: Reduces street parking for local businesses', 'user': 'shop_owner'},
        {'text': 'PRO: Great for students commuting to university', 'user': 'student'},
        {'text': 'CON: Will slow down traffic during construction', 'user': 'driver'},
        {'text': 'This aligns with our Vision Zero commitment', 'user': 'cityplanner'},
    ],
    'composting': [
        {'text': 'PRO: Reduces landfill waste and supports soil health', 'user': 'waste_manager'},
        {'text': 'CON: Higher collection costs during pilot phase', 'user': 'mayor'},
        {'text': 'PRO: Teaches residents about waste reduction', 'user': 'teacher'},
        {'text': 'CON: Requires significant behavior change', 'user': 'parent'},
        {'text': 'Let\'s see how the pilot goes before expanding', 'user': 'librarian'},
    ],
    'library_hours': [
        {'text': 'PRO: Better access for working families', 'user': 'parent'},
        {'text': 'CON: Additional staffing costs', 'user': 'mayor'},
        {'text': 'PRO: Students need quiet study spaces on weekends', 'user': 'student'},
        {'text': 'This supports our cultural access goals', 'user': 'teacher'},
        {'text': 'CON: Limited budget for extended services', 'user': 'librarian'},
    ],
    'electric_buses': [
        {'text': 'PRO: Reduces air pollution in downtown', 'user': 'nurse'},
        {'text': 'CON: High upfront costs for new vehicles', 'user': 'mayor'},
        {'text': 'PRO: Quieter operation improves quality of life', 'user': 'parent'},
        {'text': 'CON: Limited charging infrastructure', 'user': 'driver'},
        {'text': 'This supports our climate action framework', 'user': 'cityplanner'},
    ],
    'water_stations': [
        {'text': 'PRO: Reduces plastic bottle waste', 'user': 'waste_manager'},
        {'text': 'PRO: Improves public health and hydration', 'user': 'nurse'},
        {'text': 'CON: Maintenance and water quality monitoring costs', 'user': 'mayor'},
        {'text': 'PRO: Great for families with children', 'user': 'parent'},
        {'text': 'This supports our zero waste commitment', 'user': 'cityplanner'},
    ],
    'led_lighting': [
        {'text': 'PRO: Significant energy and cost savings', 'user': 'developer'},
        {'text': 'PRO: Better lighting quality for students', 'user': 'teacher'},
        {'text': 'CON: High upfront installation costs', 'user': 'mayor'},
        {'text': 'PRO: Supports our green building standards', 'user': 'cityplanner'},
        {'text': 'CON: Disposal of old lighting fixtures', 'user': 'waste_manager'},
    ],
    'car_free_sunday': [
        {'text': 'PRO: Creates space for community events', 'user': 'parent'},
        {'text': 'CON: Impacts businesses that rely on Sunday traffic', 'user': 'shop_owner'},
        {'text': 'PRO: Reduces air pollution one day per week', 'user': 'nurse'},
        {'text': 'PRO: Great for families and outdoor activities', 'user': 'student'},
        {'text': 'CON: May inconvenience residents who need to drive', 'user': 'driver'},
    ],
    'food_vouchers': [
        {'text': 'PRO: Supports local farmers and food access', 'user': 'parent'},
        {'text': 'PRO: Improves nutrition for low-income families', 'user': 'nurse'},
        {'text': 'CON: Program administration costs', 'user': 'mayor'},
        {'text': 'PRO: Supports our local food commitment', 'user': 'cityplanner'},
        {'text': 'CON: Limited to farmers\' market availability', 'user': 'shop_owner'},
    ],
    'youth_apprenticeship': [
        {'text': 'PRO: Provides job training and opportunities', 'user': 'teacher'},
        {'text': 'PRO: Addresses youth unemployment', 'user': 'parent'},
        {'text': 'CON: Training and supervision costs', 'user': 'mayor'},
        {'text': 'PRO: Builds future workforce for city services', 'user': 'cityplanner'},
        {'text': 'PRO: Great opportunity for hands-on learning', 'user': 'student'},
    ],
    'pedestrian_crossing': [
        {'text': 'PRO: Improves safety at busy intersection', 'user': 'parent'},
        {'text': 'PRO: Supports our Vision Zero commitment', 'user': 'cityplanner'},
        {'text': 'CON: May slow down vehicle traffic', 'user': 'driver'},
        {'text': 'PRO: Better access for elderly residents', 'user': 'nurse'},
        {'text': 'CON: Construction disruption', 'user': 'shop_owner'},
    ],
    'public_art': [
        {'text': 'PRO: Improves visual appeal of downtown', 'user': 'shop_owner'},
        {'text': 'PRO: Supports local artists', 'user': 'teacher'},
        {'text': 'CON: Maintenance and vandalism concerns', 'user': 'mayor'},
        {'text': 'PRO: Creates cultural vibrancy', 'user': 'librarian'},
        {'text': 'PRO: Transforms underutilized spaces', 'user': 'cityplanner'},
    ],
    'stormwater_drains': [
        {'text': 'PRO: Reduces flooding in affected neighborhoods', 'user': 'parent'},
        {'text': 'PRO: Protects property values', 'user': 'developer'},
        {'text': 'CON: High infrastructure costs', 'user': 'mayor'},
        {'text': 'PRO: Improves water quality', 'user': 'nurse'},
        {'text': 'CON: Construction disruption', 'user': 'driver'},
    ],
    'mental_health_unit': [
        {'text': 'PRO: Provides immediate crisis support', 'user': 'nurse'},
        {'text': 'PRO: Reduces emergency room visits', 'user': 'mayor'},
        {'text': 'CON: Ongoing operational costs', 'user': 'cityplanner'},
        {'text': 'PRO: Better outcomes for mental health crises', 'user': 'teacher'},
        {'text': 'PRO: Supports community safety', 'user': 'parent'},
    ],
    'free_wifi': [
        {'text': 'PRO: Improves digital access for all residents', 'user': 'student'},
        {'text': 'PRO: Supports our digital inclusion goals', 'user': 'cityplanner'},
        {'text': 'CON: Ongoing maintenance and security costs', 'user': 'mayor'},
        {'text': 'PRO: Helps with job searches and education', 'user': 'teacher'},
        {'text': 'PRO: Attracts people to public spaces', 'user': 'librarian'},
    ],
    'community_policing': [
        {'text': 'PRO: Improves community-police relations', 'user': 'parent'},
        {'text': 'PRO: More effective than reactive policing', 'user': 'nurse'},
        {'text': 'CON: Additional staffing costs', 'user': 'mayor'},
        {'text': 'PRO: Builds trust in neighborhoods', 'user': 'cityplanner'},
        {'text': 'PRO: Prevents crime through presence', 'user': 'shop_owner'},
    ],
    'skate_park': [
        {'text': 'PRO: Provides youth recreation opportunities', 'user': 'student'},
        {'text': 'PRO: Reduces skateboarding in inappropriate areas', 'user': 'parent'},
        {'text': 'CON: Construction and maintenance costs', 'user': 'mayor'},
        {'text': 'PRO: Supports active lifestyles', 'user': 'nurse'},
        {'text': 'CON: Potential noise concerns', 'user': 'driver'},
    ],
    'speed_tables': [
        {'text': 'PRO: Improves safety near school', 'user': 'parent'},
        {'text': 'PRO: Supports Vision Zero goals', 'user': 'cityplanner'},
        {'text': 'CON: May slow down emergency vehicles', 'user': 'nurse'},
        {'text': 'PRO: Protects children and families', 'user': 'teacher'},
        {'text': 'CON: Inconvenience for drivers', 'user': 'driver'},
    ],
    'energy_grants': [
        {'text': 'PRO: Reduces energy costs for small businesses', 'user': 'shop_owner'},
        {'text': 'PRO: Supports our green building standards', 'user': 'cityplanner'},
        {'text': 'CON: Limited grant funding available', 'user': 'mayor'},
        {'text': 'PRO: Creates local jobs', 'user': 'developer'},
        {'text': 'PRO: Reduces environmental impact', 'user': 'waste_manager'},
    ],
    'evening_bus': [
        {'text': 'PRO: Serves shift workers who need transportation', 'user': 'nurse'},
        {'text': 'PRO: Improves access to jobs', 'user': 'parent'},
        {'text': 'CON: Low ridership may not justify costs', 'user': 'mayor'},
        {'text': 'PRO: Supports our mobility for all goals', 'user': 'cityplanner'},
        {'text': 'PRO: Reduces drunk driving', 'user': 'driver'},
    ],
    'community_garden': [
        {'text': 'PRO: Provides fresh food access', 'user': 'parent'},
        {'text': 'PRO: Supports our local food commitment', 'user': 'cityplanner'},
        {'text': 'CON: Temporary use of valuable land', 'user': 'developer'},
        {'text': 'PRO: Builds community connections', 'user': 'teacher'},
        {'text': 'PRO: Educational opportunity for children', 'user': 'student'},
    ],
    'free_youth_transit': [
        {'text': 'PRO: Encourages independent mobility for youth', 'user': 'student'},
        {'text': 'PRO: Reduces family transportation costs', 'user': 'parent'},
        {'text': 'CON: Revenue loss for transit system', 'user': 'mayor'},
        {'text': 'PRO: Supports our mobility for all goals', 'user': 'cityplanner'},
        {'text': 'PRO: Reduces traffic congestion', 'user': 'driver'},
    ],
    'tool_library': [
        {'text': 'PRO: Reduces consumer waste', 'user': 'waste_manager'},
        {'text': 'PRO: Makes tools accessible to all residents', 'user': 'parent'},
        {'text': 'CON: Equipment maintenance and replacement costs', 'user': 'mayor'},
        {'text': 'PRO: Supports DIY culture and skills', 'user': 'teacher'},
        {'text': 'PRO: Builds community connections', 'user': 'librarian'},
    ],
    'senior_seating': [
        {'text': 'PRO: Improves outdoor access for seniors', 'user': 'nurse'},
        {'text': 'PRO: Supports aging in place', 'user': 'parent'},
        {'text': 'CON: Maintenance and weather damage', 'user': 'mayor'},
        {'text': 'PRO: Encourages social interaction', 'user': 'librarian'},
        {'text': 'PRO: Supports our public space access goals', 'user': 'cityplanner'},
    ],
    'bilingual_signage': [
        {'text': 'PRO: Improves accessibility for Spanish speakers', 'user': 'teacher'},
        {'text': 'PRO: Supports inclusive community', 'user': 'parent'},
        {'text': 'CON: Translation and installation costs', 'user': 'mayor'},
        {'text': 'PRO: Makes services more accessible', 'user': 'nurse'},
        {'text': 'PRO: Reflects our diverse community', 'user': 'librarian'},
    ],
    'bike_share': [
        {'text': 'PRO: Provides last-mile transportation', 'user': 'cyclist'},
        {'text': 'PRO: Reduces car dependency', 'user': 'driver'},
        {'text': 'CON: High startup and maintenance costs', 'user': 'mayor'},
        {'text': 'PRO: Supports our mobility for all goals', 'user': 'cityplanner'},
        {'text': 'PRO: Great for short trips', 'user': 'student'},
    ],
    'ev_charging': [
        {'text': 'PRO: Supports electric vehicle adoption', 'user': 'driver'},
        {'text': 'PRO: Reduces air pollution', 'user': 'nurse'},
        {'text': 'CON: High installation and electricity costs', 'user': 'mayor'},
        {'text': 'PRO: Supports our climate action framework', 'user': 'cityplanner'},
        {'text': 'PRO: Attracts EV drivers to downtown', 'user': 'shop_owner'},
    ],
    'historic_fountain': [
        {'text': 'PRO: Preserves our historical heritage', 'user': 'librarian'},
        {'text': 'PRO: Improves Civic Plaza aesthetics', 'user': 'shop_owner'},
        {'text': 'CON: High restoration costs', 'user': 'mayor'},
        {'text': 'PRO: Creates gathering space', 'user': 'parent'},
        {'text': 'PRO: Supports our historical preservation goals', 'user': 'cityplanner'},
    ],
    'waste_bins': [
        {'text': 'PRO: Reduces litter in downtown', 'user': 'waste_manager'},
        {'text': 'PRO: Improves recycling rates', 'user': 'cityplanner'},
        {'text': 'CON: Ongoing maintenance and collection costs', 'user': 'mayor'},
        {'text': 'PRO: Better for businesses and visitors', 'user': 'shop_owner'},
        {'text': 'PRO: Supports our zero waste commitment', 'user': 'parent'},
    ]
}

# Sample votes for Level B proposals (user -> option mapping)
SAMPLE_VOTES = {
    'bike_lanes': {
        'cyclist': 'Yes', 'student': 'Yes', 'cityplanner': 'Yes', 'parent': 'Yes',
        'driver': 'No', 'shop_owner': 'No', 'mayor': 'Abstain', 'teacher': 'Yes',
        'nurse': 'Yes', 'librarian': 'Yes'
    },
    'composting': {
        'waste_manager': 'Yes', 'teacher': 'Yes', 'student': 'Yes', 'parent': 'Yes',
        'mayor': 'No', 'shop_owner': 'No', 'cyclist': 'Yes', 'nurse': 'Abstain',
        'librarian': 'Yes', 'developer': 'Yes'
    },
    'library_hours': {
        'parent': 'Yes', 'student': 'Yes', 'teacher': 'Yes', 'librarian': 'No',
        'mayor': 'No', 'shop_owner': 'Abstain', 'nurse': 'Yes', 'cyclist': 'Yes',
        'waste_manager': 'Yes', 'developer': 'Yes'
    },
    'electric_buses': {
        'nurse': 'Yes', 'parent': 'Yes', 'cityplanner': 'Yes', 'cyclist': 'Yes',
        'mayor': 'No', 'driver': 'No', 'shop_owner': 'Abstain', 'teacher': 'Yes',
        'student': 'Yes', 'librarian': 'Yes'
    }
}

# Delegations (delegator -> delegatee)
DELEGATIONS = [
    ('student', 'cityplanner'),
    ('shop_owner', 'cityplanner'),
    ('driver', 'mayor'),
]


class DemoSeeder:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        self.session_factory = None
        self.demo_users = {}
        self.demo_polls = {}
        
    async def setup(self):
        """Initialize database connection."""
        self.engine = create_async_engine(self.db_url)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def cleanup(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            
    async def get_or_create_user(self, username: str, email: str, password: str = "password123") -> User:
        """Get existing user or create new one."""
        async with self.session_factory() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"  Found existing user: {username}")
                return user
                
            # Create new user
            hashed_password = get_password_hash(password)
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"  Created new user: {username}")
            return user
            
    async def cleanup_demo_content(self):
        """Remove all existing demo content."""
        print("Cleaning up existing demo content...")
        # For now, skip cleanup to avoid UUID issues
        print("  Skipping cleanup (UUID handling issue)")
        return
            
    async def seed_users(self):
        """Create demo users."""
        print("Creating demo users...")
        for user_data in DEMO_USERS:
            user = await self.get_or_create_user(
                user_data['username'],
                user_data['email']
            )
            self.demo_users[user_data['username']] = user.id
        print(f"  Created {len(DEMO_USERS)} demo users")
        
    async def seed_level_a_proposals(self):
        """Create Level A (baseline policy) proposals."""
        if not settings.LEVEL_A_ENABLED:
            print("Level A decisions are disabled, skipping Level A proposals")
            return
            
        print("Creating Level A (baseline policy) proposals...")
        async with self.session_factory() as session:
            for i, proposal_data in enumerate(LEVEL_A_PROPOSALS):
                # Create poll
                poll = Poll(
                    title=proposal_data['title'],
                    description=proposal_data['description'],
                    created_by=self.demo_users['cityplanner'],
                    decision_type=DecisionType.LEVEL_A,
                    direction_choice=proposal_data['direction_choice'],
                    created_at=datetime.utcnow() - timedelta(hours=24-i*2),
                    updated_at=datetime.utcnow() - timedelta(hours=24-i*2)
                )
                session.add(poll)
                await session.commit()
                await session.refresh(poll)
                
                self.demo_polls[proposal_data['title']] = poll.id
                print(f"  Created Level A proposal: {proposal_data['title']}")
                
        print(f"  Created {len(LEVEL_A_PROPOSALS)} Level A proposals")
        
    async def seed_level_b_proposals(self):
        """Create Level B (poll) proposals with options."""
        print("Creating Level B (poll) proposals...")
        async with self.session_factory() as session:
            for i, proposal_data in enumerate(LEVEL_B_PROPOSALS):
                # Create poll
                poll = Poll(
                    title=proposal_data['title'],
                    description=proposal_data['description'],
                    created_by=self.demo_users['mayor'],
                    decision_type=DecisionType.LEVEL_B,
                    created_at=datetime.utcnow() - timedelta(hours=12-i*2),
                    updated_at=datetime.utcnow() - timedelta(hours=12-i*2)
                )
                session.add(poll)
                await session.commit()
                await session.refresh(poll)
                
                # Create options
                for option_text in proposal_data['options']:
                    option = Option(
                        text=option_text,
                        poll_id=poll.id
                    )
                    session.add(option)
                
                await session.commit()
                self.demo_polls[proposal_data['title']] = poll.id
                print(f"  Created Level B proposal: {proposal_data['title']}")
                
        print(f"  Created {len(LEVEL_B_PROPOSALS)} Level B proposals")
        
    async def seed_comments(self):
        """Add comments to proposals."""
        print("Adding comments to proposals...")
        async with self.session_factory() as session:
            comment_count = 0
            
            # Add comments to Level B proposals
            for proposal_title, comments in SAMPLE_COMMENTS.items():
                # Find the corresponding poll
                poll_id = None
                for poll_title in self.demo_polls:
                    if proposal_title.replace('_', ' ') in poll_title.lower():
                        poll_id = self.demo_polls[poll_title]
                        break
                
                if poll_id:
                    for comment_data in comments:
                        comment = Comment(
                            id=uuid4(),
                            poll_id=UUID(poll_id),
                            user_id=UUID(self.demo_users[comment_data['user']]),
                            body=comment_data['text'],
                            created_at=datetime.utcnow() - timedelta(minutes=comment_count*5)
                        )
                        session.add(comment)
                        comment_count += 1
                        
            await session.commit()
            print(f"  Added {comment_count} comments")
            
    async def seed_votes(self):
        """Cast votes on Level B proposals."""
        print("Casting votes on Level B proposals...")
        async with self.session_factory() as session:
            vote_count = 0
            
            for proposal_key, votes in SAMPLE_VOTES.items():
                # Find the corresponding poll and options
                poll_id = None
                for poll_title in self.demo_polls:
                    if proposal_key.replace('_', ' ') in poll_title.lower():
                        poll_id = self.demo_polls[poll_title]
                        break
                
                if poll_id:
                    # Get options for this poll
                    result = await session.execute(
                        select(Option).where(Option.poll_id == poll_id)
                    )
                    options = result.scalars().all()
                    option_map = {opt.text: opt.id for opt in options}
                    
                    for username, vote_choice in votes.items():
                        if username in self.demo_users and vote_choice in option_map:
                            vote = Vote(
                                poll_id=poll_id,
                                option_id=option_map[vote_choice],
                                user_id=self.demo_users[username],
                                created_at=datetime.utcnow() - timedelta(minutes=vote_count*3)
                            )
                            session.add(vote)
                            vote_count += 1
                            
            await session.commit()
            print(f"  Cast {vote_count} votes")
            
    async def seed_delegations(self):
        """Create delegations between demo users."""
        print("Creating delegations...")
        async with self.session_factory() as session:
            delegation_count = 0
            
            for delegator_username, delegatee_username in DELEGATIONS:
                if (delegator_username in self.demo_users and 
                    delegatee_username in self.demo_users):
                    
                    delegation = Delegation(
                        delegator_id=self.demo_users[delegator_username],
                        delegate_id=self.demo_users[delegatee_username],
                        created_at=datetime.utcnow() - timedelta(hours=6-delegation_count)
                    )
                    session.add(delegation)
                    delegation_count += 1
                    
            await session.commit()
            print(f"  Created {delegation_count} delegations")
            
    async def print_summary(self):
        """Print a summary of what was created."""
        print("\n" + "="*50)
        print("RIVERBEND DEMO SEEDING SUMMARY")
        print("="*50)
        print(f"Users created: {len(self.demo_users)}")
        print(f"Level A proposals: {len([p for p in self.demo_polls if 'Level A' in p])}")
        print(f"Level B proposals: {len([p for p in self.demo_polls if 'Level B' in p])}")
        print(f"Total proposals: {len(self.demo_polls)}")
        print(f"Delegations: {len(DELEGATIONS)}")
        print("\nDemo user credentials:")
        print("  Username: any of the demo usernames")
        print("  Password: password123")
        print("\nExample logins:")
        for user_data in DEMO_USERS[:3]:  # Show first 3
            print(f"  {user_data['username']} / password123")
        print("="*50)


async def main():
    parser = argparse.ArgumentParser(description='Seed Riverbend demo city data')
    parser.add_argument('--reset', action='store_true', default=True,
                       help='Delete existing demo content and re-seed (default)')
    parser.add_argument('--no-reset', action='store_true',
                       help='Skip deletion, only add missing demo content')
    parser.add_argument('--users-only', action='store_true',
                       help='Only create demo users, skip proposals/votes/comments')
    
    args = parser.parse_args()
    
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///test.db')
    
    seeder = DemoSeeder(db_url)
    
    try:
        await seeder.setup()
        
        if args.reset and not args.no_reset:
            await seeder.cleanup_demo_content()
            
        await seeder.seed_users()
        
        if not args.users_only:
            await seeder.seed_level_a_proposals()
            await seeder.seed_level_b_proposals()
            await seeder.seed_comments()
            await seeder.seed_votes()
            await seeder.seed_delegations()
            
        await seeder.print_summary()
        
    finally:
        await seeder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
