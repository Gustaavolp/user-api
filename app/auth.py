from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from bson import ObjectId
from .database import get_database
from .models import verify_api_key

security = HTTPBearer()

async def get_current_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Validates API key and returns the key data from database.
    Raises HTTPException if key is invalid or inactive.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = get_database()
    
    # Find all active API keys and check against the provided key
    async for key_doc in db.api_keys.find({"is_active": True}):
        if verify_api_key(api_key, key_doc["key_hash"]):
            # Update last_used timestamp
            await db.api_keys.update_one(
                {"_id": key_doc["_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            return key_doc
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_api_key_dependency(api_key_data: dict = Security(get_current_api_key)) -> dict:
    """
    Dependency that can be used to protect endpoints.
    Returns the API key data if valid.
    """
    return api_key_data