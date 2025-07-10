# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based REST API for user management with MongoDB integration. The project features API key authentication, async operations, and comprehensive testing with pytest.

## Development Commands

### Running the Application
```bash
# Using Docker Compose (recommended)
docker-compose up --build

# Local development (requires MongoDB running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api_endpoints.py

# Run with coverage (if coverage package is available)
pytest --cov=app

# Run async tests specifically
pytest -k "async" -v
```

### Database Operations
```bash
# Connect to MongoDB container
docker exec -it user-mongodb mongosh

# Check MongoDB logs
docker logs user-mongodb
```

## Architecture

### Core Components

**app/main.py**: FastAPI application entry point with lifespan management for MongoDB connections. Includes router registration and root health check endpoint.

**app/models.py**: Pydantic models for data validation and serialization:
- User models (UserCreate, UserUpdate, UserResponse, UserInDB)
- API Key models (APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreated, APIKeyInDB)
- Custom PyObjectId class for MongoDB ObjectId handling
- API key generation and hashing utilities

**app/database.py**: MongoDB connection management using Motor (async MongoDB driver). Provides singleton database instance and connection lifecycle functions.

**app/routes.py**: API endpoints for both user and API key management. All endpoints require API key authentication except API key creation.

**app/auth.py**: API key authentication system using FastAPI Security with Bearer tokens. Validates keys against hashed values stored in database and updates last_used timestamps.

### Authentication Flow

1. Create API key via POST `/api/v1/api-keys` (no auth required)
2. Use returned API key in Authorization header: `Bearer <api_key>`
3. All other endpoints validate API key through `verify_api_key_dependency`
4. System tracks last_used timestamp for each API key

### Database Schema

**users collection**:
- `_id`: ObjectId
- `nome`: string (1-100 chars)
- `email`: EmailStr (unique)
- `data_nascimento`: datetime

**api_keys collection**:
- `_id`: ObjectId
- `name`: string (1-100 chars)
- `description`: optional string (max 500 chars)
- `is_active`: boolean
- `key_hash`: SHA256 hash of API key
- `created_at`: datetime
- `last_used`: optional datetime

### Environment Variables

Required environment variables (see README.md for defaults):
- `MONGO_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name
- `API_HOST`: API host address
- `API_PORT`: API port
- `API_DEBUG`: Debug mode flag

### Testing Strategy

Tests use a separate test database (`test_user_db`) with automatic cleanup after each test. Key fixtures:
- `test_db`: Test database connection with cleanup
- `test_api_key`: Creates valid API key for authenticated requests
- `auth_headers`: Authorization headers with test API key
- `async_client`: AsyncClient for testing async endpoints

## Key Patterns

- All operations are async using Motor for MongoDB
- Custom ObjectId validation and serialization with Pydantic
- API key authentication on all endpoints except key creation
- Comprehensive error handling with appropriate HTTP status codes
- Date handling: frontend sends dates as strings, converted to datetime for MongoDB storage
- Email uniqueness validation across user operations