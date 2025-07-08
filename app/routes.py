from fastapi import APIRouter, HTTPException, status, Security
from typing import List
from bson import ObjectId
from datetime import datetime
from .models import (
    UserCreate, UserUpdate, UserResponse,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreated,
    generate_api_key, hash_api_key
)
from .database import get_database
from .auth import verify_api_key_dependency

router = APIRouter()

@router.post("/api-keys", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED, tags=["api-keys"])
async def create_api_key(api_key: APIKeyCreate):
    """Create a new API key"""
    db = get_database()
    
    # Generate API key and hash it
    key = generate_api_key()
    key_hash = hash_api_key(key)
    
    # Prepare data for database
    api_key_data = {
        "name": api_key.name,
        "description": api_key.description,
        "is_active": api_key.is_active,
        "key_hash": key_hash,
        "created_at": datetime.utcnow(),
        "last_used": None
    }
    
    # Insert into database
    result = await db.api_keys.insert_one(api_key_data)
    
    # Get the created API key
    created_api_key = await db.api_keys.find_one({"_id": result.inserted_id})
    
    # Return response with the actual key (only shown once)
    return APIKeyCreated(
        **created_api_key,
        key_preview=key[:8] + "..." + key[-4:],
        key=key
    )


@router.get("/api-keys", response_model=List[APIKeyResponse], tags=["api-keys"])
async def get_api_keys(api_key_data: dict = Security(verify_api_key_dependency)):
    """List all API keys"""
    db = get_database()
    api_keys = []
    async for key_doc in db.api_keys.find().sort("created_at", -1):
        api_keys.append(APIKeyResponse(
            **key_doc,
            key_preview=key_doc.get("key_preview", "********")
        ))
    return api_keys


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse, tags=["api-keys"])
async def get_api_key(key_id: str, api_key_data: dict = Security(verify_api_key_dependency)):
    """Get a specific API key"""
    if not ObjectId.is_valid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    db = get_database()
    key_doc = await db.api_keys.find_one({"_id": ObjectId(key_id)})
    
    if not key_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse(
        **key_doc,
        key_preview=key_doc.get("key_preview", "********")
    )


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse, tags=["api-keys"])
async def update_api_key(key_id: str, api_key_update: APIKeyUpdate, api_key_data: dict = Security(verify_api_key_dependency)):
    """Update an API key"""
    if not ObjectId.is_valid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    db = get_database()
    
    existing_key = await db.api_keys.find_one({"_id": ObjectId(key_id)})
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    update_data = {k: v for k, v in api_key_update.model_dump().items() if v is not None}
    
    if update_data:
        await db.api_keys.update_one(
            {"_id": ObjectId(key_id)},
            {"$set": update_data}
        )
    
    updated_key = await db.api_keys.find_one({"_id": ObjectId(key_id)})
    return APIKeyResponse(
        **updated_key,
        key_preview=updated_key.get("key_preview", "********")
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["api-keys"])
async def delete_api_key(key_id: str, api_key_data: dict = Security(verify_api_key_dependency)):
    """Delete an API key"""
    if not ObjectId.is_valid(key_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    db = get_database()
    
    result = await db.api_keys.delete_one({"_id": ObjectId(key_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return None


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
async def create_user(user: UserCreate, api_key_data: dict = Security(verify_api_key_dependency)):
    db = get_database()
    
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = user.model_dump()
    # Convert date to datetime for MongoDB compatibility
    if "data_nascimento" in user_dict and user_dict["data_nascimento"]:
        from datetime import datetime
        user_dict["data_nascimento"] = datetime.combine(user_dict["data_nascimento"], datetime.min.time())
    
    result = await db.users.insert_one(user_dict)
    
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserResponse(**created_user)

@router.get("/users", response_model=List[UserResponse], tags=["users"])
async def get_users(api_key_data: dict = Security(verify_api_key_dependency)):
    db = get_database()
    users = []
    async for user in db.users.find():
        users.append(UserResponse(**user))
    return users

@router.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: str, api_key_data: dict = Security(verify_api_key_dependency)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)

@router.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(user_id: str, user_update: UserUpdate, api_key_data: dict = Security(verify_api_key_dependency)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db = get_database()
    
    existing_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    # Convert date to datetime for MongoDB compatibility
    if "data_nascimento" in update_data and update_data["data_nascimento"]:
        from datetime import datetime
        update_data["data_nascimento"] = datetime.combine(update_data["data_nascimento"], datetime.min.time())
    
    if "email" in update_data:
        email_exists = await db.users.find_one({
            "email": update_data["email"],
            "_id": {"$ne": ObjectId(user_id)}
        })
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    if update_data:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return UserResponse(**updated_user)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user(user_id: str, api_key_data: dict = Security(verify_api_key_dependency)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    db = get_database()
    
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None