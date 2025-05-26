from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PlayBase(BaseModel):
    title: str
    description: str
    genre: str
    duration_minutes: int
    director_id: str
    actors: List[str] = []

class PlayCreate(PlayBase):
    pass

class PlayUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    duration_minutes: Optional[int] = None
    director_id: Optional[str] = None
    actors: Optional[List[str]] = None

class PlayInDB(PlayBase):
    id: str
    created_at: datetime
    updated_at: datetime

class PlayResponse(PlayInDB):
    pass

class PlaySearchParams(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    director_id: Optional[str] = None
    actor_id: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None