import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime
from app.auth import get_current_api_key, verify_api_key_dependency
from app.models import hash_api_key, generate_api_key

class TestAuthentication:
    """Test authentication functionality."""
    
    async def test_get_current_api_key_valid(self, test_db, test_api_key):
        """Test get_current_api_key with valid API key."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_api_key["key"]
        )
        
        result = await get_current_api_key(credentials)
        
        assert result is not None
        assert result["name"] == "Test API Key"
        assert result["is_active"] is True
        assert result["key_hash"] == test_api_key["key_hash"]
    
    async def test_get_current_api_key_invalid(self, test_db):
        """Test get_current_api_key with invalid API key."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_api_key"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired API key" in str(exc_info.value.detail)
    
    async def test_get_current_api_key_missing_credentials(self, test_db):
        """Test get_current_api_key with missing credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(None)
        
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)
    
    async def test_get_current_api_key_empty_credentials(self, test_db):
        """Test get_current_api_key with empty credentials."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key format" in str(exc_info.value.detail)
    
    async def test_get_current_api_key_inactive(self, test_db):
        """Test get_current_api_key with inactive API key."""
        # Create inactive API key
        key = generate_api_key()
        key_hash = hash_api_key(key)
        
        api_key_data = {
            "name": "Inactive API Key",
            "description": "Inactive key for testing",
            "is_active": False,  # Inactive
            "key_hash": key_hash,
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        
        await test_db.api_keys.insert_one(api_key_data)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=key
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired API key" in str(exc_info.value.detail)
    
    async def test_get_current_api_key_updates_last_used(self, test_db, test_api_key):
        """Test that get_current_api_key updates last_used timestamp."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_api_key["key"]
        )
        
        # Get initial state
        initial_key = await test_db.api_keys.find_one({"_id": test_api_key["data"]["_id"]})
        initial_last_used = initial_key.get("last_used")
        
        # Authenticate
        await get_current_api_key(credentials)
        
        # Check that last_used was updated
        updated_key = await test_db.api_keys.find_one({"_id": test_api_key["data"]["_id"]})
        updated_last_used = updated_key.get("last_used")
        
        assert updated_last_used is not None
        assert updated_last_used != initial_last_used
        assert isinstance(updated_last_used, datetime)
    
    async def test_verify_api_key_dependency_valid(self, test_db, test_api_key):
        """Test verify_api_key_dependency with valid API key."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_api_key["key"]
        )
        
        # Mock the dependency call
        api_key_data = await get_current_api_key(credentials)
        result = await verify_api_key_dependency(api_key_data)
        
        assert result is not None
        assert result["name"] == "Test API Key"
        assert result["is_active"] is True
    
    async def test_verify_api_key_dependency_invalid(self, test_db):
        """Test verify_api_key_dependency with invalid API key."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_key"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401
    
    async def test_multiple_api_keys(self, test_db):
        """Test authentication with multiple API keys."""
        # Create multiple API keys
        keys = []
        for i in range(3):
            key = generate_api_key()
            key_hash = hash_api_key(key)
            
            api_key_data = {
                "name": f"Test API Key {i}",
                "description": f"Test description {i}",
                "is_active": True,
                "key_hash": key_hash,
                "created_at": datetime.utcnow(),
                "last_used": None
            }
            
            result = await test_db.api_keys.insert_one(api_key_data)
            keys.append({"key": key, "id": result.inserted_id})
        
        # Test that all keys work
        for i, key_data in enumerate(keys):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=key_data["key"]
            )
            
            result = await get_current_api_key(credentials)
            assert result["name"] == f"Test API Key {i}"
    
    async def test_api_key_not_found_after_deletion(self, test_db, test_api_key):
        """Test that deleted API keys cannot be used."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_api_key["key"]
        )
        
        # Verify key works initially
        result = await get_current_api_key(credentials)
        assert result is not None
        
        # Delete the API key
        await test_db.api_keys.delete_one({"_id": test_api_key["data"]["_id"]})
        
        # Try to use the deleted key
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired API key" in str(exc_info.value.detail)
    
    async def test_concurrent_api_key_usage(self, test_db, test_api_key):
        """Test concurrent usage of the same API key."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_api_key["key"]
        )
        
        # Simulate concurrent requests
        import asyncio
        
        async def authenticate():
            return await get_current_api_key(credentials)
        
        # Run multiple concurrent authentications
        results = await asyncio.gather(
            authenticate(),
            authenticate(),
            authenticate(),
            return_exceptions=True
        )
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert result["name"] == "Test API Key"
    
    async def test_api_key_case_sensitivity(self, test_db, test_api_key):
        """Test that API keys are case sensitive."""
        # Convert key to uppercase
        uppercase_key = test_api_key["key"].upper()
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=uppercase_key
        )
        
        # Should fail with uppercase key
        with pytest.raises(HTTPException) as exc_info:
            await get_current_api_key(credentials)
        
        assert exc_info.value.status_code == 401