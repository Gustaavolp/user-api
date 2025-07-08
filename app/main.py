from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import connect_to_mongo, close_mongo_connection
from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="User API",
    description="API REST para gerenciar usuários com FastAPI e MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "User API is running!"}