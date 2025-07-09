# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based REST API for user management with MongoDB integration. The API includes API key authentication and provides CRUD operations for users. All operations are asynchronous using Motor (async MongoDB driver).

## Development Commands

### Running the Application

```bash
# Development with Docker Compose (recommended)
docker-compose up --build

# Local development (requires MongoDB running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production with Docker Compose
docker-compose -f docker-compose.prod.yml up --build
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

### Database

- MongoDB is required and runs on port 27017
- Database name: `user_db` (configurable via `DATABASE_NAME` env var)
- Collections: `users`, `api_keys`

## Architecture

### Core Components

- **app/main.py**: FastAPI application setup with lifespan management for MongoDB connections
- **app/models.py**: Pydantic models for request/response validation and MongoDB document schemas
- **app/database.py**: MongoDB connection management using Motor async driver
- **app/routes.py**: API endpoints for users and API keys with authentication
- **app/auth.py**: API key authentication system using Bearer tokens

### Key Features

- **API Key Authentication**: All endpoints require valid API key in Authorization header
- **Async Operations**: All database operations are asynchronous using Motor
- **ObjectId Handling**: Custom PyObjectId class for proper MongoDB ObjectId serialization
- **Data Validation**: Pydantic models with comprehensive validation rules
- **Error Handling**: Standardized HTTP error responses (400, 401, 404)

### API Structure

- Base URL: `/api/v1`
- API Keys: `/api/keys` (create, list, get, update, delete)
- Users: `/users` (create, list, get, update, delete)
- Health check: `/` (root endpoint)

### Authentication Flow

1. Create API key via `POST /api/v1/api-keys` (unprotected)
2. Use API key in `Authorization: Bearer <key>` header for all other endpoints
3. API keys are hashed using SHA256 and stored securely
4. `last_used` timestamp is updated on each successful authentication

### Data Models

- **User**: nome (string), email (EmailStr), data_nascimento (date)
- **API Key**: name, description, is_active, key_hash, created_at, last_used
- MongoDB ObjectIds are properly handled with custom PyObjectId class

## Environment Variables

- `MONGO_URL`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `DATABASE_NAME`: Database name (default: `user_db`)
- `API_HOST`: API host (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)
- `API_DEBUG`: Debug mode (default: `true`)

## API Documentation

Once running, access interactive documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc