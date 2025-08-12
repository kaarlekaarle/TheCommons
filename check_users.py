#!/usr/bin/env python3

import asyncio
from sqlalchemy import text
from backend.database import engine

async def check_users():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT username, email, is_active FROM users LIMIT 10'))
        print('Users in database:')
        for row in result.fetchall():
            print(f'  Username: {row[0]}, Email: {row[1]}, Active: {row[2]}')

if __name__ == '__main__':
    asyncio.run(check_users())
