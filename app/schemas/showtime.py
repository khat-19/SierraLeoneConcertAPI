from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ShowtimeBase(BaseModel):
    play_id: str
    date_time: datetime
    venue: str
    available_seats: int
    price: float

class ShowtimeCreate(ShowtimeBase):
    pass

class ShowtimeUpdate(BaseModel):
    play_id: Optional[str] = None
    date_time: Optional[datetime] = None
    venue: Optional[str] = None
    available_seats: Optional[int] = None
    price: Optional[float] = None

class ShowtimeInDB(ShowtimeBase):
    id: str
    created_at: datetime
    updated_at: datetime

class ShowtimeResponse(ShowtimeInDB):
    pass

class ShowtimeSearchParams(BaseModel):
    play_id: Optional[str] = None
    venue: Optional[str] = None
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None