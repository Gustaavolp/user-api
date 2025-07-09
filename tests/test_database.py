import pytest
from app.database import get_database, connect_to_mongo, close_mongo_connection, mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase

class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_get_database_returns_database(self, test_db):
        """Test that get_database returns a database instance."""
        db = get_database()
        assert isinstance(db, AsyncIOMotorDatabase)
    
    async def test_mongodb_singleton(self, test_db):
        """Test that mongodb is a singleton."""
        assert mongodb.database is not None
        assert mongodb.client is not None
        
        # Get database should return the same instance
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2
    
    async def test_database_operations(self, test_db):
        """Test basic database operations."""
        db = get_database()
        
        # Test insert
        test_doc = {"name": "test", "value": 123}
        result = await db.test_collection.insert_one(test_doc)
        assert result.inserted_id is not None
        
        # Test find
        found_doc = await db.test_collection.find_one({"name": "test"})
        assert found_doc is not None
        assert found_doc["name"] == "test"
        assert found_doc["value"] == 123
        
        # Test update
        await db.test_collection.update_one(
            {"name": "test"},
            {"$set": {"value": 456}}
        )
        updated_doc = await db.test_collection.find_one({"name": "test"})
        assert updated_doc["value"] == 456
        
        # Test delete
        delete_result = await db.test_collection.delete_one({"name": "test"})
        assert delete_result.deleted_count == 1
        
        # Verify deletion
        deleted_doc = await db.test_collection.find_one({"name": "test"})
        assert deleted_doc is None
    
    async def test_collection_operations(self, test_db):
        """Test collection-specific operations."""
        db = get_database()
        
        # Test users collection
        user_doc = {
            "nome": "Test User",
            "email": "test@email.com",
            "data_nascimento": "1990-01-01"
        }
        result = await db.users.insert_one(user_doc)
        assert result.inserted_id is not None
        
        # Test api_keys collection
        api_key_doc = {
            "name": "Test API Key",
            "key_hash": "test_hash",
            "is_active": True
        }
        result = await db.api_keys.insert_one(api_key_doc)
        assert result.inserted_id is not None
        
        # Test finding documents
        found_user = await db.users.find_one({"nome": "Test User"})
        assert found_user is not None
        
        found_api_key = await db.api_keys.find_one({"name": "Test API Key"})
        assert found_api_key is not None
    
    async def test_database_indexes(self, test_db):
        """Test database indexes (if any)."""
        db = get_database()
        
        # Test that we can create indexes
        await db.users.create_index("email", unique=True)
        await db.api_keys.create_index("key_hash")
        
        # Test unique constraint
        user1 = {"nome": "User 1", "email": "unique@email.com"}
        user2 = {"nome": "User 2", "email": "unique@email.com"}
        
        await db.users.insert_one(user1)
        
        # Should raise an error due to unique constraint
        with pytest.raises(Exception):
            await db.users.insert_one(user2)
    
    async def test_database_aggregation(self, test_db):
        """Test database aggregation operations."""
        db = get_database()
        
        # Insert test data
        users = [
            {"nome": "User 1", "email": "user1@email.com", "age": 25},
            {"nome": "User 2", "email": "user2@email.com", "age": 30},
            {"nome": "User 3", "email": "user3@email.com", "age": 35}
        ]
        await db.users.insert_many(users)
        
        # Test aggregation
        pipeline = [
            {"$group": {"_id": None, "avg_age": {"$avg": "$age"}}},
            {"$project": {"_id": 0, "avg_age": 1}}
        ]
        
        result = []
        async for doc in db.users.aggregate(pipeline):
            result.append(doc)
        
        assert len(result) == 1
        assert result[0]["avg_age"] == 30.0
    
    async def test_database_transactions(self, test_db):
        """Test database transactions (if supported)."""
        db = get_database()
        
        # Note: Transactions require a replica set in MongoDB
        # This test demonstrates the transaction syntax
        # but may not work in all test environments
        
        try:
            async with mongodb.client.start_session() as session:
                async with session.start_transaction():
                    await db.users.insert_one(
                        {"nome": "Transaction User", "email": "transaction@email.com"},
                        session=session
                    )
                    
                    # This should be part of the transaction
                    user = await db.users.find_one(
                        {"nome": "Transaction User"},
                        session=session
                    )
                    assert user is not None
        except Exception:
            # Skip transaction test if not supported
            pytest.skip("Transactions not supported in this MongoDB setup")
    
    async def test_database_error_handling(self, test_db):
        """Test database error handling."""
        db = get_database()
        
        # Test invalid collection operation
        with pytest.raises(Exception):
            await db.invalid_collection.create_index({"invalid": "index"})
        
        # Test invalid query
        result = await db.users.find_one({"$invalid": "query"})
        # Should return None, not raise an error
        assert result is None