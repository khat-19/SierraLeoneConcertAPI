from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, plays, actors, directors, tickets, customers, showtimes
from app.db.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Sierra Leone Concert Association API",
    description="API for managing the Sierra Leone Concert Association's database",
    version="1.0.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(plays.router, prefix="/plays", tags=["Plays"])
app.include_router(actors.router, prefix="/actors", tags=["Actors"])
app.include_router(directors.router, prefix="/directors", tags=["Directors"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(showtimes.router, prefix="/showtimes", tags=["Showtimes"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the Sierra Leone Concert Association API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }