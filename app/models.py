from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, field_serializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from datetime import date, datetime
from typing import Optional, Annotated, Any
from bson import ObjectId
import secrets
import hashlib


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid"}


class UserBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    data_nascimento: date


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    data_nascimento: Optional[date] = None


class UserResponse(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @field_serializer('data_nascimento')
    def serialize_date(self, value):
        if isinstance(value, datetime):
            return value.date()
        return value


class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class APIKeyResponse(APIKeyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    key_preview: str = Field(..., description="First 8 characters of the key")
    created_at: datetime
    last_used: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class APIKeyInDB(APIKeyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    key_hash: str = Field(..., description="SHA256 hash of the API key")
    created_at: datetime
    last_used: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class APIKeyCreated(APIKeyResponse):
    key: str = Field(..., description="The actual API key - only shown once")


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    return hashlib.sha256(key.encode()).hexdigest() == key_hash