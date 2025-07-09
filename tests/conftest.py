import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.database import mongodb
from app.models import generate_api_key, hash_api_key
from datetime import datetime
import os

# Test database configuration
TEST_DATABASE_NAME = "test_user_db"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create a test database connection."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[TEST_DATABASE_NAME]
    
    # Override the database connection for tests
    mongodb.client = client
    mongodb.database = db
    
    yield db
    
    # Clean up: drop all collections after each test
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db.drop_collection(collection_name)
    
    client.close()

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_api_key(test_db):
    """Create a test API key."""
    key = generate_api_key()
    key_hash = hash_api_key(key)
    
    api_key_data = {
        "name": "Test API Key",
        "description": "Test description",
        "is_active": True,
        "key_hash": key_hash,
        "created_at": datetime.utcnow(),
        "last_used": None
    }
    
    result = await test_db.api_keys.insert_one(api_key_data)
    api_key_data["_id"] = result.inserted_id
    
    return {
        "id": str(result.inserted_id),
        "key": key,
        "key_hash": key_hash,
        "data": api_key_data
    }

@pytest.fixture
async def auth_headers(test_api_key):
    """Create authentication headers with test API key."""
    return {"Authorization": f"Bearer {test_api_key['key']}"}

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "nome": "João Silva",
        "email": "joao@email.com",
        "data_nascimento": "1990-01-15"
    }

@pytest.fixture
async def created_user(test_db, test_user_data):
    """Create a test user in the database."""
    from datetime import datetime
    user_data = test_user_data.copy()
    user_data["data_nascimento"] = datetime.strptime(user_data["data_nascimento"], "%Y-%m-%d")
    
    result = await test_db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    return user_data