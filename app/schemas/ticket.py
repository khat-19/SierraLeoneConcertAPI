from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    showtime_id: str
    customer_id: str
    seat_number: str
    price: float
    is_used: bool = False

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    showtime_id: Optional[str] = None
    customer_id: Optional[str] = None
    seat_number: Optional[str] = None
    price: Optional[float] = None
    is_used: Optional[bool] = None

class TicketInDB(TicketBase):
    id: str
    purchase_date: datetime
    created_at: datetime
    updated_at: datetime

class TicketResponse(TicketInDB):
    pass

class TicketSearchParams(BaseModel):
    showtime_id: Optional[str] = None
    customer_id: Optional[str] = None
    is_used: Optional[bool] = None