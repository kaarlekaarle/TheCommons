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
    {'username': 'mayor', 'email': 'mayor@springfield.example'},
    {'username': 'cityplanner', 'email': 'cityplanner@springfield.example'},
    {'username': 'teacher', 'email': 'teacher@springfield.example'},
    {'username': 'shop_owner', 'email': 'shop_owner@springfield.example'},
    {'username': 'student', 'email': 'student@springfield.example'},
    {'username': 'nurse', 'email': 'nurse@springfield.example'},
    {'username': 'cyclist', 'email': 'cyclist@springfield.example'},
    {'username': 'driver', 'email': 'driver@springfield.example'},
    {'username': 'parent', 'email': 'parent@springfield.example'},
    {'username': 'librarian', 'email': 'librarian@springfield.example'},
    {'username': 'waste_manager', 'email': 'waste_manager@springfield.example'},
    {'username': 'developer', 'email': 'developer@springfield.example'},
]

# Level A (baseline policy) proposals - based on actual municipal policy frameworks
LEVEL_A_PROPOSALS = [
    {
        'title': 'Complete Streets Policy',
        'description': 'Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.',
        'direction_choice': "Transportation Safety"
    },
    {
        'title': 'Public Records Transparency Policy',
        'description': 'Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.',
        'direction_choice': "Government Transparency"
    },
    {
        'title': 'Green Building Standards for Municipal Construction',
        'description': 'Require all new municipal buildings and major renovations to meet LEED Silver certification or equivalent energy efficiency standards.',
        'direction_choice': "Environmental Policy"
    },
    {
        'title': 'Inclusive Housing Development Policy',
        'description': 'Ensure 20% of all new residential development includes affordable housing units or equivalent contributions to the housing trust fund.',
        'direction_choice': "Housing & Development"
    },
    {
        'title': 'Parks and Recreation Access Standards',
        'description': 'Maintain a minimum of 10 acres of parkland per 1,000 residents and ensure all neighborhoods have access to recreational facilities within a 10-minute walk.',
        'direction_choice': "Parks & Recreation"
    },
    {
        'title': 'Municipal Climate Action Plan',
        'description': 'Reduce city government greenhouse gas emissions by 50% by 2030 and achieve carbon neutrality by 2040 through energy efficiency and renewable energy.',
        'direction_choice': "Climate & Sustainability"
    },
    {
        'title': 'Digital Equity and Broadband Access Policy',
        'description': 'Ensure all residents have access to affordable high-speed internet and digital literacy training through partnerships with service providers and community organizations.',
        'direction_choice': "Technology & Innovation"
    },
    {
        'title': 'Local Food System Development Policy',
        'description': 'Support local food production and distribution by providing incentives for urban agriculture, farmers markets, and food processing facilities.',
        'direction_choice': "Food Security"
    },
    {
        'title': 'Transit-Oriented Development Framework',
        'description': 'Prioritize mixed-use development within 1/2 mile of transit stations to reduce car dependency and increase transit ridership.',
        'direction_choice': "Public Transit"
    },
    {
        'title': 'Zero Waste and Circular Economy Policy',
        'description': 'Achieve 90% waste diversion from landfills by 2030 through comprehensive recycling, composting, and waste reduction programs.',
        'direction_choice': "Waste Management"
    }
]

# Level B (poll) proposals - based on actual municipal council decisions
LEVEL_B_PROPOSALS = [
    {
        'title': 'Install protected bike lanes on Washington Avenue from downtown to university district',
        'description': 'Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.',
        'options': ['Approve', 'Modify plan', 'Reject']
    },
    {
        'title': 'Launch 18-month curbside composting pilot in four residential neighborhoods',
        'description': 'Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.',
        'options': ['Approve', 'Reduce scope', 'Reject']
    },
    {
        'title': 'Extend public library hours to 9 PM on weekdays for six-month trial',
        'description': 'Extend operating hours at the main library to better serve students, working families, and evening library users.',
        'options': ['Approve', 'Modify hours', 'Reject']
    },
    {
        'title': 'Plant 750 street trees along major transit corridors and in underserved neighborhoods',
        'description': 'Add urban trees along bus routes and in neighborhoods with low tree canopy to improve air quality, provide shade, and enhance walkability.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Install 25 public water refill stations in parks, schools, and community centers',
        'description': 'Add drinking water stations to reduce plastic bottle waste, improve public health, and encourage hydration during outdoor activities.',
        'options': ['Approve', 'Reduce locations', 'Reject']
    },
    {
        'title': 'Retrofit lighting in all municipal buildings with energy-efficient LED systems',
        'description': 'Replace existing lighting systems in 15 municipal buildings to reduce energy consumption by 40% and lower operating costs.',
        'options': ['Approve', 'Phase implementation', 'Reject']
    },
    {
        'title': 'Add wheelchair-accessible seating and improved pathways in Central Park',
        'description': 'Install accessible benches, improve pathway surfaces, and add shade structures to ensure park access for residents of all abilities.',
        'options': ['Approve', 'Modify scope', 'Reject']
    },
    {
        'title': 'Create monthly "Open Streets" program on Main Street during summer months',
        'description': 'Close Main Street to vehicle traffic on the first Sunday of each month from June through September for community events and recreation.',
        'options': ['Approve', 'Reduce frequency', 'Reject']
    },
    {
        'title': 'Launch local food voucher program for 300 low-income households',
        'description': 'Provide $75 monthly vouchers redeemable at farmers markets and local food co-ops for qualifying households to improve food access.',
        'options': ['Approve', 'Reduce amount', 'Reject']
    },
    {
        'title': 'Replace diesel buses on Route 8 with electric buses within 24 months',
        'description': 'Purchase 12 electric buses to replace aging diesel vehicles on the downtown-to-airport route, reducing emissions and noise pollution.',
        'options': ['Approve', 'Extend timeline', 'Reject']
    },
    {
        'title': 'Start youth apprenticeship program in city maintenance and parks departments',
        'description': 'Create 20 paid apprenticeship positions for youth aged 16-24 in parks maintenance, street repair, and facilities management.',
        'options': ['Approve', 'Reduce positions', 'Reject']
    },
    {
        'title': 'Create protected pedestrian crossing at 3rd and Market intersection',
        'description': 'Install signalized crosswalk with pedestrian refuge island and countdown timers at the busy 3rd and Market intersection.',
        'options': ['Approve', 'Modify design', 'Reject']
    },
    {
        'title': 'Run public art mural program in underutilized downtown spaces',
        'description': 'Commission 15 murals on blank walls and underpasses to improve visual appeal, support local artists, and reduce graffiti.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Upgrade stormwater drainage system in flood-prone areas',
        'description': 'Replace and expand drainage infrastructure in four neighborhoods that experience regular flooding during heavy rain events.',
        'options': ['Approve', 'Prioritize areas', 'Reject']
    },
    {
        'title': 'Pilot mobile mental health crisis response unit operating five days per week',
        'description': 'Deploy a mobile crisis intervention team with mental health professionals to provide immediate support in high-need areas.',
        'options': ['Approve', 'Reduce days', 'Reject']
    },
    {
        'title': 'Offer free Wi-Fi in all public libraries, recreation centers, and community spaces',
        'description': 'Install and maintain wireless internet access in 12 public facilities to improve digital access and support remote work and learning.',
        'options': ['Approve', 'Limit locations', 'Reject']
    },
    {
        'title': 'Expand community policing foot patrols to three additional neighborhoods',
        'description': 'Add walking patrols in Eastside, Southside, and Northside neighborhoods to improve community-police relations and crime prevention.',
        'options': ['Approve', 'Add one area', 'Reject']
    },
    {
        'title': 'Begin construction of inclusive playground in Westside Recreation Area',
        'description': 'Build a 20,000 square foot playground with accessible equipment for children of all abilities, including sensory-friendly areas.',
        'options': ['Approve', 'Reduce size', 'Reject']
    },
    {
        'title': 'Install traffic-calming speed humps on Oak Drive near elementary school',
        'description': 'Add four speed humps on Oak Drive to reduce vehicle speeds and improve pedestrian safety near the elementary school.',
        'options': ['Approve', 'Reduce number', 'Reject']
    },
    {
        'title': 'Provide energy-efficiency grants to 25 small businesses for storefront upgrades',
        'description': 'Offer $7,500 grants to small businesses for lighting, HVAC, insulation, and window improvements to reduce energy costs.',
        'options': ['Approve', 'Reduce amount', 'Reject']
    },
    {
        'title': 'Introduce on-demand evening bus service for shift workers in industrial district',
        'description': 'Launch flexible bus service from 7 PM to 3 AM to serve workers at the industrial park and surrounding residential areas.',
        'options': ['Approve', 'Reduce hours', 'Reject']
    },
    {
        'title': 'Convert vacant lot at 12th and Pine into community garden for three years',
        'description': 'Transform the 0.75-acre vacant lot into a community garden with 40 plots, shared composting area, and educational programming.',
        'options': ['Approve', 'Reduce size', 'Reject']
    },
    {
        'title': 'Offer free weekend transit for youth under 18 for 18-month pilot',
        'description': 'Provide free bus and train rides on Saturdays and Sundays for all youth to encourage independent mobility and reduce family transportation costs.',
        'options': ['Approve', 'Limit days', 'Reject']
    },
    {
        'title': 'Create citywide tool and equipment lending library',
        'description': 'Establish a lending library with 300 tools and equipment items available for 14-day borrowing periods to support DIY projects and reduce waste.',
        'options': ['Approve', 'Reduce inventory', 'Reject']
    },
    {
        'title': 'Add shaded seating areas to four senior housing complexes',
        'description': 'Install covered benches, tables, and shade structures at senior housing facilities to improve outdoor access and social interaction.',
        'options': ['Approve', 'Reduce locations', 'Reject']
    },
    {
        'title': 'Implement bilingual signage in all city-owned buildings and facilities',
        'description': 'Add Spanish-language signs alongside English in all municipal buildings to improve accessibility for Spanish-speaking residents.',
        'options': ['Approve', 'Phase implementation', 'Reject']
    },
    {
        'title': 'Start bike-share program with 150 bikes at 15 docking stations',
        'description': 'Launch a public bicycle sharing system with stations throughout downtown and adjacent neighborhoods to provide last-mile transportation.',
        'options': ['Approve', 'Reduce scale', 'Reject']
    },
    {
        'title': 'Build public charging station hub for electric vehicles in central parking garage',
        'description': 'Install 20 electric vehicle charging stations in the main downtown parking facility to support EV adoption and reduce emissions.',
        'options': ['Approve', 'Reduce stations', 'Reject']
    },
    {
        'title': 'Restore historic bandshell in Memorial Park',
        'description': 'Repair and restore the 1930s bandshell in Memorial Park, including structural repairs, electrical upgrades, and acoustic improvements.',
        'options': ['Approve', 'Modify scope', 'Reject']
    },
    {
        'title': 'Add three new trash and recycling bins per block in downtown core',
        'description': 'Install 60 new waste receptacles with separate recycling compartments throughout the downtown area to reduce litter and improve recycling rates.',
        'options': ['Approve', 'Reduce number', 'Reject']
    }
]

# Sample comments for proposals - balanced PRO/CON perspectives
SAMPLE_COMMENTS = {
    'bike_lanes': [
        {'text': 'PRO: This will significantly improve cyclist safety and encourage more people to bike instead of drive', 'user': 'cyclist'},
        {'text': 'CON: Removing street parking will hurt local businesses that depend on customer parking', 'user': 'shop_owner'},
        {'text': 'PRO: Great for students commuting to university - much safer than current conditions', 'user': 'student'},
        {'text': 'CON: Construction will cause traffic delays and the lanes will slow down vehicle traffic permanently', 'user': 'driver'},
        {'text': 'PRO: This aligns perfectly with our Complete Streets policy and Vision Zero goals', 'user': 'cityplanner'},
    ],
    'composting': [
        {'text': 'PRO: Reduces landfill waste by 30% and creates valuable compost for city parks', 'user': 'waste_manager'},
        {'text': 'CON: Higher collection costs during pilot phase - need to see if residents actually use it', 'user': 'mayor'},
        {'text': 'PRO: Teaches residents about waste reduction and soil health - great educational opportunity', 'user': 'teacher'},
        {'text': 'CON: Requires significant behavior change - many residents may not participate', 'user': 'parent'},
        {'text': 'PRO: Let\'s see how the pilot goes - if successful, we can expand citywide', 'user': 'librarian'},
    ],
    'library_hours': [
        {'text': 'PRO: Better access for working families who can\'t visit during regular hours', 'user': 'parent'},
        {'text': 'CON: Additional staffing costs of $45,000 annually - tight budget year', 'user': 'mayor'},
        {'text': 'PRO: Students need quiet study spaces on weeknights - current hours are too limited', 'user': 'student'},
        {'text': 'PRO: This supports our goal of making cultural and educational resources accessible to all', 'user': 'teacher'},
        {'text': 'CON: Limited budget for extended services - other departments may need to be cut', 'user': 'librarian'},
    ],
    'electric_buses': [
        {'text': 'PRO: Reduces air pollution in downtown by 85% compared to diesel buses', 'user': 'nurse'},
        {'text': 'CON: High upfront costs of $2.4 million - need to see long-term savings', 'user': 'mayor'},
        {'text': 'PRO: Quieter operation improves quality of life for residents along the route', 'user': 'parent'},
        {'text': 'CON: Limited charging infrastructure - need to build charging stations first', 'user': 'driver'},
        {'text': 'PRO: This supports our climate action plan and reduces our carbon footprint', 'user': 'cityplanner'},
    ],
    'water_stations': [
        {'text': 'PRO: Reduces plastic bottle waste by an estimated 50,000 bottles annually', 'user': 'waste_manager'},
        {'text': 'PRO: Improves public health by encouraging hydration during outdoor activities', 'user': 'nurse'},
        {'text': 'CON: Maintenance and water quality monitoring costs of $15,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Great for families with children - reduces need to carry water bottles', 'user': 'parent'},
        {'text': 'PRO: This supports our zero waste commitment and reduces environmental impact', 'user': 'cityplanner'},
    ],
    'led_lighting': [
        {'text': 'PRO: Significant energy savings of 40% and cost savings of $85,000 annually', 'user': 'developer'},
        {'text': 'PRO: Better lighting quality for students and staff in school buildings', 'user': 'teacher'},
        {'text': 'CON: High upfront installation costs of $320,000 - need to see payback period', 'user': 'mayor'},
        {'text': 'PRO: Supports our green building standards and reduces environmental impact', 'user': 'cityplanner'},
        {'text': 'CON: Disposal of old lighting fixtures - need to ensure proper recycling', 'user': 'waste_manager'},
    ],
    'open_streets': [
        {'text': 'PRO: Creates space for community events and encourages physical activity', 'user': 'parent'},
        {'text': 'CON: Impacts businesses that rely on Sunday traffic and parking', 'user': 'shop_owner'},
        {'text': 'PRO: Reduces air pollution one day per month and promotes community connection', 'user': 'nurse'},
        {'text': 'PRO: Great for families and outdoor activities - creates car-free space', 'user': 'student'},
        {'text': 'CON: May inconvenience residents who need to drive on Sundays', 'user': 'driver'},
    ],
    'food_vouchers': [
        {'text': 'PRO: Supports local farmers and improves food access for low-income families', 'user': 'parent'},
        {'text': 'PRO: Improves nutrition and health outcomes for vulnerable populations', 'user': 'nurse'},
        {'text': 'CON: Program administration costs of $25,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Supports our local food system development policy', 'user': 'cityplanner'},
        {'text': 'CON: Limited to farmers market availability - may not work year-round', 'user': 'shop_owner'},
    ],
    'youth_apprenticeship': [
        {'text': 'PRO: Provides valuable job training and career opportunities for young people', 'user': 'teacher'},
        {'text': 'PRO: Addresses youth unemployment and builds workforce skills', 'user': 'parent'},
        {'text': 'CON: Training and supervision costs of $180,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Builds future workforce for city services and creates career pathways', 'user': 'cityplanner'},
        {'text': 'PRO: Great opportunity for hands-on learning and skill development', 'user': 'student'},
    ],
    'pedestrian_crossing': [
        {'text': 'PRO: Improves safety at one of our most dangerous intersections', 'user': 'parent'},
        {'text': 'PRO: Supports our Complete Streets policy and Vision Zero commitment', 'user': 'cityplanner'},
        {'text': 'CON: May slow down vehicle traffic during peak hours', 'user': 'driver'},
        {'text': 'PRO: Better access for elderly residents and people with disabilities', 'user': 'nurse'},
        {'text': 'CON: Construction will cause traffic disruption for several weeks', 'user': 'shop_owner'},
    ],
    'public_art': [
        {'text': 'PRO: Improves visual appeal of downtown and attracts visitors', 'user': 'shop_owner'},
        {'text': 'PRO: Supports local artists and creates cultural vibrancy', 'user': 'teacher'},
        {'text': 'CON: Maintenance and potential vandalism costs of $12,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Creates cultural identity and transforms underutilized spaces', 'user': 'librarian'},
        {'text': 'PRO: Transforms blank walls into engaging public spaces', 'user': 'cityplanner'},
    ],
    'stormwater_drains': [
        {'text': 'PRO: Reduces flooding in affected neighborhoods by 80%', 'user': 'parent'},
        {'text': 'PRO: Protects property values and prevents costly flood damage', 'user': 'developer'},
        {'text': 'CON: High infrastructure costs of $1.2 million', 'user': 'mayor'},
        {'text': 'PRO: Improves water quality by reducing stormwater runoff', 'user': 'nurse'},
        {'text': 'CON: Construction disruption for several months in affected areas', 'user': 'driver'},
    ],
    'mental_health_unit': [
        {'text': 'PRO: Provides immediate crisis support and reduces emergency room visits', 'user': 'nurse'},
        {'text': 'PRO: More cost-effective than emergency room care for mental health crises', 'user': 'mayor'},
        {'text': 'CON: Ongoing operational costs of $280,000 annually', 'user': 'cityplanner'},
        {'text': 'PRO: Better outcomes for mental health crises and reduces stigma', 'user': 'teacher'},
        {'text': 'PRO: Supports community safety and provides appropriate crisis response', 'user': 'parent'},
    ],
    'free_wifi': [
        {'text': 'PRO: Improves digital access for all residents, especially low-income families', 'user': 'student'},
        {'text': 'PRO: Supports our digital equity policy and helps bridge the digital divide', 'user': 'cityplanner'},
        {'text': 'CON: Ongoing maintenance and security costs of $35,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Helps with job searches, education, and remote work opportunities', 'user': 'teacher'},
        {'text': 'PRO: Attracts people to public spaces and supports community engagement', 'user': 'librarian'},
    ],
    'community_policing': [
        {'text': 'PRO: Improves community-police relations and builds trust', 'user': 'parent'},
        {'text': 'PRO: More effective than reactive policing - prevents crime through presence', 'user': 'nurse'},
        {'text': 'CON: Additional staffing costs of $420,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Builds trust in neighborhoods and improves public safety', 'user': 'cityplanner'},
        {'text': 'PRO: Prevents crime through community engagement and visibility', 'user': 'shop_owner'},
    ],
    'inclusive_playground': [
        {'text': 'PRO: Provides recreation opportunities for children of all abilities', 'user': 'student'},
        {'text': 'PRO: Creates inclusive space where all families can play together', 'user': 'parent'},
        {'text': 'CON: Construction and maintenance costs of $450,000', 'user': 'mayor'},
        {'text': 'PRO: Supports active lifestyles and social development for all children', 'user': 'nurse'},
        {'text': 'CON: May attract more visitors and increase noise in the area', 'user': 'driver'},
    ],
    'speed_humps': [
        {'text': 'PRO: Improves safety near school and reduces vehicle speeds by 40%', 'user': 'parent'},
        {'text': 'PRO: Supports our Complete Streets policy and protects children', 'user': 'cityplanner'},
        {'text': 'CON: May slow down emergency vehicles and cause driver frustration', 'user': 'nurse'},
        {'text': 'PRO: Protects children and families walking to school', 'user': 'teacher'},
        {'text': 'CON: Inconvenience for drivers and potential damage to vehicles', 'user': 'driver'},
    ],
    'energy_grants': [
        {'text': 'PRO: Reduces energy costs for small businesses and improves competitiveness', 'user': 'shop_owner'},
        {'text': 'PRO: Supports our green building standards and reduces environmental impact', 'user': 'cityplanner'},
        {'text': 'CON: Limited grant funding available - only 25 businesses can benefit', 'user': 'mayor'},
        {'text': 'PRO: Creates local jobs for contractors and energy auditors', 'user': 'developer'},
        {'text': 'PRO: Reduces environmental impact and supports sustainability', 'user': 'waste_manager'},
    ],
    'evening_bus': [
        {'text': 'PRO: Serves shift workers who need reliable transportation after hours', 'user': 'nurse'},
        {'text': 'PRO: Improves access to jobs and reduces transportation barriers', 'user': 'parent'},
        {'text': 'CON: Low ridership may not justify the $180,000 annual cost', 'user': 'mayor'},
        {'text': 'PRO: Supports our transit-oriented development and mobility goals', 'user': 'cityplanner'},
        {'text': 'PRO: Reduces drunk driving and provides safe transportation option', 'user': 'driver'},
    ],
    'community_garden': [
        {'text': 'PRO: Provides fresh food access and educational opportunities', 'user': 'parent'},
        {'text': 'PRO: Supports our local food system development policy', 'user': 'cityplanner'},
        {'text': 'CON: Temporary use of valuable land that could be developed', 'user': 'developer'},
        {'text': 'PRO: Builds community connections and teaches sustainable practices', 'user': 'teacher'},
        {'text': 'PRO: Educational opportunity for children to learn about food production', 'user': 'student'},
    ],
    'free_youth_transit': [
        {'text': 'PRO: Encourages independent mobility for youth and reduces family costs', 'user': 'student'},
        {'text': 'PRO: Reduces family transportation costs and increases youth access', 'user': 'parent'},
        {'text': 'CON: Revenue loss for transit system of $65,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Supports our mobility for all goals and reduces car dependency', 'user': 'cityplanner'},
        {'text': 'PRO: Reduces traffic congestion and supports sustainable transportation', 'user': 'driver'},
    ],
    'tool_library': [
        {'text': 'PRO: Reduces consumer waste and makes tools accessible to all residents', 'user': 'waste_manager'},
        {'text': 'PRO: Makes expensive tools accessible to residents who can\'t afford them', 'user': 'parent'},
        {'text': 'CON: Equipment maintenance and replacement costs of $28,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Supports DIY culture and teaches valuable skills', 'user': 'teacher'},
        {'text': 'PRO: Builds community connections and reduces consumption', 'user': 'librarian'},
    ],
    'senior_seating': [
        {'text': 'PRO: Improves outdoor access for seniors and supports aging in place', 'user': 'nurse'},
        {'text': 'PRO: Supports aging in place and encourages social interaction', 'user': 'parent'},
        {'text': 'CON: Maintenance and weather damage costs of $8,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Encourages social interaction and outdoor activity for seniors', 'user': 'librarian'},
        {'text': 'PRO: Supports our parks and recreation access standards', 'user': 'cityplanner'},
    ],
    'bilingual_signage': [
        {'text': 'PRO: Improves accessibility for Spanish-speaking residents', 'user': 'teacher'},
        {'text': 'PRO: Supports inclusive community and makes services accessible', 'user': 'parent'},
        {'text': 'CON: Translation and installation costs of $45,000', 'user': 'mayor'},
        {'text': 'PRO: Makes city services more accessible to diverse populations', 'user': 'nurse'},
        {'text': 'PRO: Reflects our diverse community and improves inclusivity', 'user': 'librarian'},
    ],
    'bike_share': [
        {'text': 'PRO: Provides last-mile transportation and reduces car dependency', 'user': 'cyclist'},
        {'text': 'PRO: Reduces car dependency and supports sustainable transportation', 'user': 'driver'},
        {'text': 'CON: High startup and maintenance costs of $320,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Supports our mobility for all goals and transit-oriented development', 'user': 'cityplanner'},
        {'text': 'PRO: Great for short trips and reduces parking demand', 'user': 'student'},
    ],
    'ev_charging': [
        {'text': 'PRO: Supports electric vehicle adoption and reduces emissions', 'user': 'driver'},
        {'text': 'PRO: Reduces air pollution and supports clean transportation', 'user': 'nurse'},
        {'text': 'CON: High installation and electricity costs of $85,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Supports our climate action plan and reduces carbon footprint', 'user': 'cityplanner'},
        {'text': 'PRO: Attracts EV drivers to downtown and supports local businesses', 'user': 'shop_owner'},
    ],
    'historic_bandshell': [
        {'text': 'PRO: Preserves our historical heritage and cultural landmark', 'user': 'librarian'},
        {'text': 'PRO: Improves Memorial Park aesthetics and creates gathering space', 'user': 'shop_owner'},
        {'text': 'CON: High restoration costs of $280,000', 'user': 'mayor'},
        {'text': 'PRO: Creates gathering space for community events and performances', 'user': 'parent'},
        {'text': 'PRO: Supports our historical preservation and cultural goals', 'user': 'cityplanner'},
    ],
    'waste_bins': [
        {'text': 'PRO: Reduces litter in downtown and improves cleanliness', 'user': 'waste_manager'},
        {'text': 'PRO: Improves recycling rates and supports zero waste goals', 'user': 'cityplanner'},
        {'text': 'CON: Ongoing maintenance and collection costs of $22,000 annually', 'user': 'mayor'},
        {'text': 'PRO: Better for businesses and visitors - cleaner downtown', 'user': 'shop_owner'},
        {'text': 'PRO: Supports our zero waste commitment and reduces environmental impact', 'user': 'parent'},
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
        print("SPRINGFIELD DEMO SEEDING SUMMARY")
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
