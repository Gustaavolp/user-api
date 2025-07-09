import pytest
from datetime import date, datetime
from pydantic import ValidationError
from bson import ObjectId
from app.models import (
    UserCreate, UserUpdate, UserResponse, UserInDB,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyInDB,
    PyObjectId, generate_api_key, hash_api_key, verify_api_key
)

class TestPyObjectId:
    """Test the custom PyObjectId class."""
    
    def test_valid_objectid_string(self):
        """Test that valid ObjectId strings are accepted."""
        valid_id = str(ObjectId())
        py_id = PyObjectId.validate(valid_id)
        assert isinstance(py_id, ObjectId)
        assert str(py_id) == valid_id
    
    def test_valid_objectid_instance(self):
        """Test that ObjectId instances are accepted."""
        original_id = ObjectId()
        py_id = PyObjectId.validate(original_id)
        assert isinstance(py_id, ObjectId)
        assert py_id == original_id
    
    def test_invalid_objectid_string(self):
        """Test that invalid ObjectId strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")
    
    def test_is_valid_check(self):
        """Test ObjectId.is_valid functionality."""
        assert ObjectId.is_valid(str(ObjectId()))
        assert not ObjectId.is_valid("invalid")

class TestUserModels:
    """Test user-related Pydantic models."""
    
    def test_user_create_valid(self):
        """Test UserCreate with valid data."""
        user_data = {
            "nome": "João Silva",
            "email": "joao@email.com",
            "data_nascimento": date(1990, 1, 15)
        }
        user = UserCreate(**user_data)
        assert user.nome == "João Silva"
        assert user.email == "joao@email.com"
        assert user.data_nascimento == date(1990, 1, 15)
    
    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                nome="João Silva",
                email="invalid-email",
                data_nascimento=date(1990, 1, 15)
            )
    
    def test_user_create_empty_name(self):
        """Test UserCreate with empty name."""
        with pytest.raises(ValidationError):
            UserCreate(
                nome="",
                email="joao@email.com",
                data_nascimento=date(1990, 1, 15)
            )
    
    def test_user_create_long_name(self):
        """Test UserCreate with name too long."""
        with pytest.raises(ValidationError):
            UserCreate(
                nome="x" * 101,  # Max is 100
                email="joao@email.com",
                data_nascimento=date(1990, 1, 15)
            )
    
    def test_user_update_partial(self):
        """Test UserUpdate with partial data."""
        user_update = UserUpdate(nome="João Santos")
        assert user_update.nome == "João Santos"
        assert user_update.email is None
        assert user_update.data_nascimento is None
    
    def test_user_update_all_fields(self):
        """Test UserUpdate with all fields."""
        user_update = UserUpdate(
            nome="João Santos",
            email="joao.santos@email.com",
            data_nascimento=date(1985, 5, 20)
        )
        assert user_update.nome == "João Santos"
        assert user_update.email == "joao.santos@email.com"
        assert user_update.data_nascimento == date(1985, 5, 20)
    
    def test_user_response_with_objectid(self):
        """Test UserResponse with ObjectId."""
        obj_id = ObjectId()
        user_data = {
            "_id": obj_id,
            "nome": "João Silva",
            "email": "joao@email.com",
            "data_nascimento": date(1990, 1, 15)
        }
        user = UserResponse(**user_data)
        assert str(user.id) == str(obj_id)
        assert user.nome == "João Silva"
    
    def test_user_response_serialization(self):
        """Test UserResponse serialization."""
        obj_id = ObjectId()
        user_data = {
            "_id": obj_id,
            "nome": "João Silva",
            "email": "joao@email.com",
            "data_nascimento": datetime(1990, 1, 15)
        }
        user = UserResponse(**user_data)
        
        # Test date serialization
        assert user.serialize_date(datetime(1990, 1, 15)) == date(1990, 1, 15)
        assert user.serialize_date(date(1990, 1, 15)) == date(1990, 1, 15)

class TestAPIKeyModels:
    """Test API key-related Pydantic models."""
    
    def test_api_key_create_valid(self):
        """Test APIKeyCreate with valid data."""
        api_key_data = {
            "name": "Test API Key",
            "description": "Test description",
            "is_active": True
        }
        api_key = APIKeyCreate(**api_key_data)
        assert api_key.name == "Test API Key"
        assert api_key.description == "Test description"
        assert api_key.is_active is True
    
    def test_api_key_create_default_active(self):
        """Test APIKeyCreate with default is_active value."""
        api_key = APIKeyCreate(name="Test Key")
        assert api_key.is_active is True
        assert api_key.description is None
    
    def test_api_key_create_invalid_name(self):
        """Test APIKeyCreate with invalid name."""
        with pytest.raises(ValidationError):
            APIKeyCreate(name="")
        
        with pytest.raises(ValidationError):
            APIKeyCreate(name="x" * 101)  # Max is 100
    
    def test_api_key_update_partial(self):
        """Test APIKeyUpdate with partial data."""
        api_key_update = APIKeyUpdate(name="Updated Name")
        assert api_key_update.name == "Updated Name"
        assert api_key_update.description is None
        assert api_key_update.is_active is None
    
    def test_api_key_response_with_objectid(self):
        """Test APIKeyResponse with ObjectId."""
        obj_id = ObjectId()
        api_key_data = {
            "_id": obj_id,
            "name": "Test API Key",
            "description": "Test description",
            "is_active": True,
            "key_preview": "abcd1234...wxyz",
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        api_key = APIKeyResponse(**api_key_data)
        assert str(api_key.id) == str(obj_id)
        assert api_key.name == "Test API Key"
        assert api_key.key_preview == "abcd1234...wxyz"

class TestAPIKeyUtilities:
    """Test API key utility functions."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert len(key1) > 0
        assert len(key2) > 0
        assert key1 != key2  # Should be unique
    
    def test_hash_api_key(self):
        """Test API key hashing."""
        key = "test_api_key"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert hash1 == hash2  # Same key should produce same hash
        assert len(hash1) == 64  # SHA256 produces 64 char hex string
    
    def test_verify_api_key_valid(self):
        """Test API key verification with valid key."""
        key = "test_api_key"
        key_hash = hash_api_key(key)
        
        assert verify_api_key(key, key_hash) is True
    
    def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        key = "test_api_key"
        wrong_key = "wrong_key"
        key_hash = hash_api_key(key)
        
        assert verify_api_key(wrong_key, key_hash) is False
    
    def test_hash_consistency(self):
        """Test that hash function is consistent."""
        key = generate_api_key()
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        assert hash1 == hash2
        assert verify_api_key(key, hash1) is True
        assert verify_api_key(key, hash2) is True