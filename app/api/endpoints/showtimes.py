from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Showtime, Ticket
from app.schemas.showtime import ShowtimeCreate, ShowtimeUpdate, ShowtimeResponse, ShowtimeSearchParams
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ShowtimeResponse, status_code=201)
async def create_showtime(
    showtime: ShowtimeCreate, 
    current_user: User = Depends(check_admin_permission)
):
    """
    Create a new showtime. Admin only.
    """
    db = get_database()
    
    # Check if play exists
    play = await db.plays.find_one({"id": showtime.play_id})
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    
    # Create showtime object
    new_showtime = Showtime(
        **showtime.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert showtime
    showtime_dict = new_showtime.dict()
    await db.showtimes.insert_one(showtime_dict)
    
    return showtime_dict

@router.get("/", response_model=List[ShowtimeResponse])
async def read_showtimes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all showtimes with pagination.
    """
    db = get_database()
    showtimes = await db.showtimes.find().skip(skip).limit(limit).to_list(limit)
    return showtimes

@router.get("/search", response_model=List[ShowtimeResponse])
async def search_showtimes(
    play_id: Optional[str] = None,
    venue: Optional[str] = None,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search showtimes with various filters.
    """
    db = get_database()
    
    # Build query
    query = {}
    if play_id:
        query["play_id"] = play_id
    if venue:
        query["venue"] = {"$regex": venue, "$options": "i"}
    
    # Date range
    if min_date is not None or max_date is not None:
        query["date_time"] = {}
        if min_date is not None:
            query["date_time"]["$gte"] = min_date
        if max_date is not None:
            query["date_time"]["$lte"] = max_date
    
    # Price range
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    # Execute query with pagination
    showtimes = await db.showtimes.find(query).skip(skip).limit(limit).to_list(limit)
    return showtimes

@router.get("/upcoming", response_model=List[ShowtimeResponse])
async def get_upcoming_showtimes(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get upcoming showtimes (showtimes scheduled in the future).
    """
    db = get_database()
    current_time = datetime.utcnow()
    
    # Query showtimes with date_time greater than current time, sorted by date
    showtimes = await db.showtimes.find(
        {"date_time": {"$gte": current_time}}
    ).sort("date_time", 1).limit(limit).to_list(limit)
    
    return showtimes

@router.get("/{showtime_id}", response_model=ShowtimeResponse)
async def read_showtime(
    showtime_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific showtime by ID.
    """
    db = get_database()
    showtime = await db.showtimes.find_one({"id": showtime_id})
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    return showtime

@router.get("/{showtime_id}/available_seats", response_model=int)
async def get_available_seats(
    showtime_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the number of available seats for a specific showtime.
    """
    db = get_database()
    showtime = await db.showtimes.find_one({"id": showtime_id})
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    return showtime["available_seats"]

@router.put("/{showtime_id}", response_model=ShowtimeResponse)
async def update_showtime(
    showtime_id: str,
    showtime_update: ShowtimeUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update a showtime. Admin only.
    """
    db = get_database()
    
    # Check if showtime exists
    existing_showtime = await db.showtimes.find_one({"id": showtime_id})
    if not existing_showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # If updating play, check if new play exists
    if showtime_update.play_id:
        play = await db.plays.find_one({"id": showtime_update.play_id})
        if not play:
            raise HTTPException(status_code=404, detail="Play not found")
    
    # Prepare update data
    update_data = showtime_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update showtime
        await db.showtimes.update_one(
            {"id": showtime_id},
            {"$set": update_data}
        )
    
    # Get updated showtime
    updated_showtime = await db.showtimes.find_one({"id": showtime_id})
    return updated_showtime

@router.put("/{showtime_id}/update_seats", response_model=ShowtimeResponse)
async def update_available_seats(
    showtime_id: str,
    seats_change: int,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update the number of available seats for a showtime. Admin only.
    
    This endpoint can be used to adjust the available seats (e.g., after adding more seats
    or removing seats due to maintenance).
    
    Parameters:
    - seats_change: The number of seats to add (positive) or remove (negative)
    """
    db = get_database()
    
    # Check if showtime exists
    showtime = await db.showtimes.find_one({"id": showtime_id})
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Update available seats
    new_seats = showtime["available_seats"] + seats_change
    
    # Ensure seats don't go below 0
    if new_seats < 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot reduce seats below 0. Current available seats: " + 
                   str(showtime["available_seats"])
        )
    
    # Update the showtime
    await db.showtimes.update_one(
        {"id": showtime_id},
        {
            "$set": {
                "available_seats": new_seats,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Return updated showtime
    updated_showtime = await db.showtimes.find_one({"id": showtime_id})
    return updated_showtime

@router.delete("/{showtime_id}", status_code=204)
async def delete_showtime(
    showtime_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete a showtime. Admin only.
    
    This will also delete all tickets associated with this showtime.
    """
    db = get_database()
    
    # Check if showtime exists
    showtime = await db.showtimes.find_one({"id": showtime_id})
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Delete tickets for this showtime
    await db.tickets.delete_many({"showtime_id": showtime_id})
    
    # Delete showtime
    await db.showtimes.delete_one({"id": showtime_id})
    
    return None