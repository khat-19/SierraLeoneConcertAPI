from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketSearchParams
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(
    ticket: TicketCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new ticket (book a seat).
    """
    db = get_database()
    
    # Check if showtime exists
    showtime = await db.showtimes.find_one({"id": ticket.showtime_id})
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Check if customer exists
    customer = await db.customers.find_one({"id": ticket.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if seat is available
    if showtime["available_seats"] <= 0:
        raise HTTPException(status_code=400, detail="No seats available for this showtime")
    
    # Check if seat number is already taken
    existing_ticket = await db.tickets.find_one({
        "showtime_id": ticket.showtime_id,
        "seat_number": ticket.seat_number
    })
    if existing_ticket:
        raise HTTPException(status_code=400, detail=f"Seat {ticket.seat_number} is already booked")
    
    # Create ticket object
    new_ticket = Ticket(
        **ticket.dict(),
        purchase_date=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert ticket
    ticket_dict = new_ticket.dict()
    await db.tickets.insert_one(ticket_dict)
    
    # Update showtime's available seats
    await db.showtimes.update_one(
        {"id": ticket.showtime_id},
        {"$inc": {"available_seats": -1}}
    )
    
    # Update customer's tickets list
    await db.customers.update_one(
        {"id": ticket.customer_id},
        {"$addToSet": {"tickets": new_ticket.id}}
    )
    
    return ticket_dict

@router.get("/", response_model=List[TicketResponse])
async def read_tickets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_permission)
):
    """
    Retrieve all tickets with pagination. Admin only.
    """
    db = get_database()
    tickets = await db.tickets.find().skip(skip).limit(limit).to_list(limit)
    return tickets

@router.get("/my-tickets", response_model=List[TicketResponse])
async def read_my_tickets(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get tickets for the currently logged-in user.
    """
    db = get_database()
    
    # Find customer record for current user
    customer = await db.customers.find_one({"user_id": current_user.id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    
    # Get tickets for this customer
    tickets = await db.tickets.find({"customer_id": customer["id"]}).to_list(100)
    return tickets

@router.get("/search", response_model=List[TicketResponse])
async def search_tickets(
    showtime_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    is_used: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_admin_permission)
):
    """
    Search tickets with filters. Admin only.
    """
    db = get_database()
    
    # Build query
    query = {}
    if showtime_id:
        query["showtime_id"] = showtime_id
    if customer_id:
        query["customer_id"] = customer_id
    if is_used is not None:
        query["is_used"] = is_used
    
    # Execute query with pagination
    tickets = await db.tickets.find(query).skip(skip).limit(limit).to_list(limit)
    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
async def read_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific ticket by ID.
    """
    db = get_database()
    ticket = await db.tickets.find_one({"id": ticket_id})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if the ticket belongs to the current user or user is admin
    if current_user.role != "admin":
        customer = await db.customers.find_one({"user_id": current_user.id})
        if not customer or ticket["customer_id"] != customer["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to access this ticket")
    
    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update a ticket. Admin only.
    """
    db = get_database()
    
    # Check if ticket exists
    existing_ticket = await db.tickets.find_one({"id": ticket_id})
    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Prepare update data
    update_data = ticket_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update ticket
        await db.tickets.update_one(
            {"id": ticket_id},
            {"$set": update_data}
        )
    
    # Get updated ticket
    updated_ticket = await db.tickets.find_one({"id": ticket_id})
    return updated_ticket

@router.put("/{ticket_id}/mark-used", response_model=TicketResponse)
async def mark_ticket_used(
    ticket_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Mark a ticket as used. Admin only.
    """
    db = get_database()
    
    # Check if ticket exists
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # If ticket is already used, return an error
    if ticket["is_used"]:
        raise HTTPException(status_code=400, detail="Ticket is already marked as used")
    
    # Mark ticket as used
    await db.tickets.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "is_used": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Return updated ticket
    updated_ticket = await db.tickets.find_one({"id": ticket_id})
    return updated_ticket

@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete a ticket. Admin only.
    
    This will also increase the available seats for the associated showtime.
    """
    db = get_database()
    
    # Check if ticket exists
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Increase available seats for the showtime
    await db.showtimes.update_one(
        {"id": ticket["showtime_id"]},
        {"$inc": {"available_seats": 1}}
    )
    
    # Remove ticket from customer's tickets list
    await db.customers.update_one(
        {"id": ticket["customer_id"]},
        {"$pull": {"tickets": ticket_id}}
    )
    
    # Delete ticket
    await db.tickets.delete_one({"id": ticket_id})
    
    return None