from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DirectorBase(BaseModel):
    name: str
    bio: Optional[str] = None
    plays: List[str] = []

class DirectorCreate(DirectorBase):
    pass

class DirectorUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    plays: Optional[List[str]] = None

class DirectorInDB(DirectorBase):
    id: str
    created_at: datetime
    updated_at: datetime

class DirectorResponse(DirectorInDB):
    pass

class DirectorSearchParams(BaseModel):
    name: Optional[str] = None
    play_id: Optional[str] = None