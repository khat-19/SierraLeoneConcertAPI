from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ActorBase(BaseModel):
    name: str
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    plays: List[str] = []

class ActorCreate(ActorBase):
    pass

class ActorUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    plays: Optional[List[str]] = None

class ActorInDB(ActorBase):
    id: str
    created_at: datetime
    updated_at: datetime

class ActorResponse(ActorInDB):
    pass

class ActorSearchParams(BaseModel):
    name: Optional[str] = None
    play_id: Optional[str] = None