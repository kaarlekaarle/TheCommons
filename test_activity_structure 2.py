import asyncio
import os
from backend.main import app
from httpx import AsyncClient

async def test_activity_structure():
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["USE_DEMO_CONTENT"] = "false"
    os.environ["CONTENT_DATA_DIR"] = "../data/real_content"
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/activity/")
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            print("Data type:", type(data))
            if data:
                print("First item keys:", list(data[0].keys()))
                print("First item:", data[0])
            else:
                print("No data returned")
        else:
            print("Error response:", resp.text)

if __name__ == "__main__":
    asyncio.run(test_activity_structure())
