from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerSearchParams
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer: CustomerCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new customer profile.
    """
    db = get_database()
    
    # Check if user exists
    user = await db.users.find_one({"id": customer.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if customer with this user_id already exists
    existing_customer = await db.customers.find_one({"user_id": customer.user_id})
    if existing_customer:
        raise HTTPException(status_code=400, detail="Customer profile already exists for this user")
    
    # Create customer object
    new_customer = Customer(
        **customer.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert customer
    customer_dict = new_customer.dict()
    await db.customers.insert_one(customer_dict)
    
    return customer_dict

@router.get("/", response_model=List[CustomerResponse])
async def read_customers(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_permission)
):
    """
    Retrieve all customers with pagination. Admin only.
    """
    db = get_database()
    customers = await db.customers.find().skip(skip).limit(limit).to_list(limit)
    return customers

@router.get("/me", response_model=CustomerResponse)
async def read_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the customer profile for the currently logged-in user.
    """
    db = get_database()
    customer = await db.customers.find_one({"user_id": current_user.id})
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    
    return customer

@router.get("/search", response_model=List[CustomerResponse])
async def search_customers(
    name: Optional[str] = None,
    email: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_permission)
):
    """
    Search customers with filters. Admin only.
    """
    db = get_database()
    
    # Build query
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if email:
        query["email"] = {"$regex": email, "$options": "i"}
    
    # Execute query with pagination
    customers = await db.customers.find(query).skip(skip).limit(limit).to_list(limit)
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
async def read_customer(
    customer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific customer by ID.
    """
    db = get_database()
    customer = await db.customers.find_one({"id": customer_id})
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Allow access to own profile or admin access to any profile
    if current_user.id != customer["user_id"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this customer profile")
    
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a customer profile.
    """
    db = get_database()
    
    # Check if customer exists
    existing_customer = await db.customers.find_one({"id": customer_id})
    if not existing_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Allow updates to own profile or admin updates to any profile
    if current_user.id != existing_customer["user_id"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this customer profile")
    
    # Prepare update data
    update_data = customer_update.dict(exclude_unset=True)
    if update_data:
        # Don't allow updating user_id or tickets directly
        if "user_id" in update_data:
            del update_data["user_id"]
        if "tickets" in update_data:
            del update_data["tickets"]
            
        update_data["updated_at"] = datetime.utcnow()
        
        # Update customer
        await db.customers.update_one(
            {"id": customer_id},
            {"$set": update_data}
        )
    
    # Get updated customer
    updated_customer = await db.customers.find_one({"id": customer_id})
    return updated_customer

@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete a customer profile. Admin only.
    
    This will also delete all tickets associated with this customer.
    """
    db = get_database()
    
    # Check if customer exists
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get tickets for this customer
    tickets = await db.tickets.find({"customer_id": customer_id}).to_list(1000)
    
    # For each ticket, increase available seats for the associated showtime
    for ticket in tickets:
        await db.showtimes.update_one(
            {"id": ticket["showtime_id"]},
            {"$inc": {"available_seats": 1}}
        )
    
    # Delete tickets for this customer
    await db.tickets.delete_many({"customer_id": customer_id})
    
    # Delete customer
    await db.customers.delete_one({"id": customer_id})
    
    return None