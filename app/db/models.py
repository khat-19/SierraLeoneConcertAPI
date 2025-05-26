import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr

# User model for authentication
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    disabled: bool = False
    role: str = "customer"  # admin, staff, customer
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "johndoe@example.com",
                "username": "johndoe",
                "hashed_password": "hashedpassword",
                "full_name": "John Doe",
                "role": "customer"
            }
        }

# Play model
class Play(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    genre: str
    duration_minutes: int
    director_id: str
    actors: List[str] = []  # list of actor IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Hamlet",
                "description": "The Tragedy of Hamlet, Prince of Denmark",
                "genre": "Tragedy",
                "duration_minutes": 180,
                "director_id": "director_id_here",
                "actors": ["actor_id_1", "actor_id_2"]
            }
        }

# Actor model
class Actor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    plays: List[str] = []  # list of play IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Smith",
                "bio": "An experienced actor with 15 years in the industry",
                "date_of_birth": "1980-01-01T00:00:00",
                "plays": ["play_id_1", "play_id_2"]
            }
        }

# Director model
class Director(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bio: Optional[str] = None
    plays: List[str] = []  # list of play IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Sarah Johnson",
                "bio": "Award-winning director with experience in various genres",
                "plays": ["play_id_1", "play_id_2"]
            }
        }

# Showtime model
class Showtime(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    play_id: str
    date_time: datetime
    venue: str
    available_seats: int
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "play_id": "play_id_here",
                "date_time": "2023-12-31T19:30:00",
                "venue": "National Theatre",
                "available_seats": 200,
                "price": 50.00
            }
        }

# Customer model
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    tickets: List[str] = []  # list of ticket IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_id_here",
                "name": "Jane Doe",
                "email": "janedoe@example.com",
                "phone": "123-456-7890",
                "address": "123 Main St, Freetown",
                "tickets": ["ticket_id_1", "ticket_id_2"]
            }
        }

# Ticket model
class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    showtime_id: str
    customer_id: str
    seat_number: str
    price: float
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    is_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "showtime_id": "showtime_id_here",
                "customer_id": "customer_id_here",
                "seat_number": "A12",
                "price": 50.00,
                "is_used": False
            }
        }