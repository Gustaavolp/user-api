import pytest
from fastapi import status
from httpx import AsyncClient
from bson import ObjectId
from datetime import datetime
from app.models import generate_api_key, hash_api_key

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test the root health check endpoint."""
        response = await async_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "User API is running!"}

class TestAPIKeyEndpoints:
    """Test API key management endpoints."""
    
    async def test_create_api_key(self, async_client: AsyncClient, test_db):
        """Test creating a new API key."""
        api_key_data = {
            "name": "Test API Key",
            "description": "Test description",
            "is_active": True
        }
        
        response = await async_client.post("/api/v1/api-keys", json=api_key_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["description"] == "Test description"
        assert data["is_active"] is True
        assert "key" in data
        assert "key_preview" in data
        assert "created_at" in data
        assert data["last_used"] is None
    
    async def test_create_api_key_minimal(self, async_client: AsyncClient, test_db):
        """Test creating API key with minimal data."""
        api_key_data = {"name": "Minimal Key"}
        
        response = await async_client.post("/api/v1/api-keys", json=api_key_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "Minimal Key"
        assert data["description"] is None
        assert data["is_active"] is True
    
    async def test_create_api_key_invalid_name(self, async_client: AsyncClient, test_db):
        """Test creating API key with invalid name."""
        api_key_data = {"name": ""}
        
        response = await async_client.post("/api/v1/api-keys", json=api_key_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_api_keys(self, async_client: AsyncClient, test_db, auth_headers):
        """Test listing API keys."""
        response = await async_client.get("/api/v1/api-keys", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test API key
    
    async def test_get_api_keys_unauthorized(self, async_client: AsyncClient, test_db):
        """Test listing API keys without authentication."""
        response = await async_client.get("/api/v1/api-keys")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_api_key_by_id(self, async_client: AsyncClient, test_db, test_api_key, auth_headers):
        """Test getting specific API key by ID."""
        response = await async_client.get(f"/api/v1/api-keys/{test_api_key['id']}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Test API Key"
        assert data["id"] == test_api_key['id']
    
    async def test_get_api_key_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test getting non-existent API key."""
        fake_id = str(ObjectId())
        response = await async_client.get(f"/api/v1/api-keys/{fake_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_get_api_key_invalid_id(self, async_client: AsyncClient, test_db, auth_headers):
        """Test getting API key with invalid ID format."""
        response = await async_client.get("/api/v1/api-keys/invalid_id", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_update_api_key(self, async_client: AsyncClient, test_db, test_api_key, auth_headers):
        """Test updating an API key."""
        update_data = {
            "name": "Updated API Key",
            "description": "Updated description"
        }
        
        response = await async_client.put(f"/api/v1/api-keys/{test_api_key['id']}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Updated API Key"
        assert data["description"] == "Updated description"
    
    async def test_update_api_key_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test updating non-existent API key."""
        fake_id = str(ObjectId())
        update_data = {"name": "Updated Name"}
        
        response = await async_client.put(f"/api/v1/api-keys/{fake_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_delete_api_key(self, async_client: AsyncClient, test_db, auth_headers):
        """Test deleting an API key."""
        # Create a key to delete
        key = generate_api_key()
        key_hash = hash_api_key(key)
        
        api_key_data = {
            "name": "Key to Delete",
            "key_hash": key_hash,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        
        result = await test_db.api_keys.insert_one(api_key_data)
        key_id = str(result.inserted_id)
        
        response = await async_client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        deleted_key = await test_db.api_keys.find_one({"_id": result.inserted_id})
        assert deleted_key is None
    
    async def test_delete_api_key_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test deleting non-existent API key."""
        fake_id = str(ObjectId())
        response = await async_client.delete(f"/api/v1/api-keys/{fake_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestUserEndpoints:
    """Test user management endpoints."""
    
    async def test_create_user(self, async_client: AsyncClient, test_db, auth_headers, test_user_data):
        """Test creating a new user."""
        response = await async_client.post("/api/v1/users", json=test_user_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["nome"] == test_user_data["nome"]
        assert data["email"] == test_user_data["email"]
        assert data["data_nascimento"] == test_user_data["data_nascimento"]
        assert "id" in data
    
    async def test_create_user_duplicate_email(self, async_client: AsyncClient, test_db, auth_headers, test_user_data):
        """Test creating user with duplicate email."""
        # Create first user
        await async_client.post("/api/v1/users", json=test_user_data, headers=auth_headers)
        
        # Try to create another user with same email
        response = await async_client.post("/api/v1/users", json=test_user_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    async def test_create_user_invalid_email(self, async_client: AsyncClient, test_db, auth_headers):
        """Test creating user with invalid email."""
        invalid_user_data = {
            "nome": "Test User",
            "email": "invalid-email",
            "data_nascimento": "1990-01-15"
        }
        
        response = await async_client.post("/api/v1/users", json=invalid_user_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_create_user_unauthorized(self, async_client: AsyncClient, test_db, test_user_data):
        """Test creating user without authentication."""
        response = await async_client.post("/api/v1/users", json=test_user_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_users(self, async_client: AsyncClient, test_db, auth_headers, created_user):
        """Test listing users."""
        response = await async_client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check that our created user is in the list
        user_emails = [user["email"] for user in data]
        assert created_user["email"] in user_emails
    
    async def test_get_users_unauthorized(self, async_client: AsyncClient, test_db):
        """Test listing users without authentication."""
        response = await async_client.get("/api/v1/users")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_user_by_id(self, async_client: AsyncClient, test_db, auth_headers, created_user):
        """Test getting specific user by ID."""
        user_id = str(created_user["_id"])
        response = await async_client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["nome"] == created_user["nome"]
        assert data["email"] == created_user["email"]
        assert data["id"] == user_id
    
    async def test_get_user_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test getting non-existent user."""
        fake_id = str(ObjectId())
        response = await async_client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_get_user_invalid_id(self, async_client: AsyncClient, test_db, auth_headers):
        """Test getting user with invalid ID format."""
        response = await async_client.get("/api/v1/users/invalid_id", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_update_user(self, async_client: AsyncClient, test_db, auth_headers, created_user):
        """Test updating a user."""
        user_id = str(created_user["_id"])
        update_data = {
            "nome": "Updated Name",
            "email": "updated@email.com"
        }
        
        response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["nome"] == "Updated Name"
        assert data["email"] == "updated@email.com"
    
    async def test_update_user_partial(self, async_client: AsyncClient, test_db, auth_headers, created_user):
        """Test partially updating a user."""
        user_id = str(created_user["_id"])
        update_data = {"nome": "Partially Updated"}
        
        response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["nome"] == "Partially Updated"
        assert data["email"] == created_user["email"]  # Should remain unchanged
    
    async def test_update_user_duplicate_email(self, async_client: AsyncClient, test_db, auth_headers, test_user_data):
        """Test updating user with duplicate email."""
        # Create two users
        response1 = await async_client.post("/api/v1/users", json=test_user_data, headers=auth_headers)
        user1_id = response1.json()["id"]
        
        user2_data = {
            "nome": "Second User",
            "email": "second@email.com",
            "data_nascimento": "1985-05-20"
        }
        response2 = await async_client.post("/api/v1/users", json=user2_data, headers=auth_headers)
        user2_id = response2.json()["id"]
        
        # Try to update user2 with user1's email
        update_data = {"email": test_user_data["email"]}
        response = await async_client.put(f"/api/v1/users/{user2_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    async def test_update_user_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test updating non-existent user."""
        fake_id = str(ObjectId())
        update_data = {"nome": "Updated Name"}
        
        response = await async_client.put(f"/api/v1/users/{fake_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_delete_user(self, async_client: AsyncClient, test_db, auth_headers, created_user):
        """Test deleting a user."""
        user_id = str(created_user["_id"])
        response = await async_client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        deleted_user = await test_db.users.find_one({"_id": created_user["_id"]})
        assert deleted_user is None
    
    async def test_delete_user_not_found(self, async_client: AsyncClient, test_db, auth_headers):
        """Test deleting non-existent user."""
        fake_id = str(ObjectId())
        response = await async_client.delete(f"/api/v1/users/{fake_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_delete_user_unauthorized(self, async_client: AsyncClient, test_db, created_user):
        """Test deleting user without authentication."""
        user_id = str(created_user["_id"])
        response = await async_client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestAPIIntegration:
    """Test API integration scenarios."""
    
    async def test_full_user_workflow(self, async_client: AsyncClient, test_db):
        """Test complete user management workflow."""
        # 1. Create API key
        api_key_data = {"name": "Workflow Test Key"}
        response = await async_client.post("/api/v1/api-keys", json=api_key_data)
        assert response.status_code == status.HTTP_201_CREATED
        api_key = response.json()["key"]
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # 2. Create user
        user_data = {
            "nome": "Workflow User",
            "email": "workflow@email.com",
            "data_nascimento": "1990-01-01"
        }
        response = await async_client.post("/api/v1/users", json=user_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        user_id = response.json()["id"]
        
        # 3. Get user
        response = await async_client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # 4. Update user
        update_data = {"nome": "Updated Workflow User"}
        response = await async_client.put(f"/api/v1/users/{user_id}", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # 5. List users
        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # 6. Delete user
        response = await async_client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    async def test_concurrent_requests(self, async_client: AsyncClient, test_db, auth_headers):
        """Test handling concurrent requests."""
        import asyncio
        
        async def create_user(i):
            user_data = {
                "nome": f"Concurrent User {i}",
                "email": f"concurrent{i}@email.com",
                "data_nascimento": "1990-01-01"
            }
            return await async_client.post("/api/v1/users", json=user_data, headers=auth_headers)
        
        # Create multiple users concurrently
        tasks = [create_user(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED
    
    async def test_api_key_usage_tracking(self, async_client: AsyncClient, test_db, test_api_key, auth_headers):
        """Test that API key usage is tracked."""
        # Get initial last_used
        initial_key = await test_db.api_keys.find_one({"key_hash": test_api_key["key_hash"]})
        initial_last_used = initial_key.get("last_used")
        
        # Make an API call
        response = await async_client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Check that last_used was updated
        updated_key = await test_db.api_keys.find_one({"key_hash": test_api_key["key_hash"]})
        updated_last_used = updated_key.get("last_used")
        
        assert updated_last_used != initial_last_used
        assert updated_last_used is not None