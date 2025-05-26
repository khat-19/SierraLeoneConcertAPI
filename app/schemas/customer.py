from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class CustomerBase(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    tickets: List[str] = []

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tickets: Optional[List[str]] = None

class CustomerInDB(CustomerBase):
    id: str
    created_at: datetime
    updated_at: datetime

class CustomerResponse(CustomerInDB):
    pass

class CustomerSearchParams(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None