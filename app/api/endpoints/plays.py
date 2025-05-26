from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Play
from app.schemas.play import PlayCreate, PlayUpdate, PlayResponse, PlaySearchParams
from typing import List, Optional
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=PlayResponse, status_code=201)
async def create_play(
    play: PlayCreate, 
    current_user: User = Depends(check_admin_permission)
):
    """
    Create a new play. Admin only.
    """
    db = get_database()
    
    # Check if director exists
    director = await db.directors.find_one({"id": play.director_id})
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    
    # Check if all actors exist
    for actor_id in play.actors:
        actor = await db.actors.find_one({"id": actor_id})
        if not actor:
            raise HTTPException(status_code=404, detail=f"Actor with id {actor_id} not found")
    
    # Create play object
    new_play = Play(
        **play.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert play
    play_dict = new_play.dict()
    await db.plays.insert_one(play_dict)
    
    # Update director's plays list
    await db.directors.update_one(
        {"id": play.director_id},
        {"$addToSet": {"plays": new_play.id}}
    )
    
    # Update actors' plays list
    for actor_id in play.actors:
        await db.actors.update_one(
            {"id": actor_id},
            {"$addToSet": {"plays": new_play.id}}
        )
    
    return play_dict

@router.get("/", response_model=List[PlayResponse])
async def read_plays(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all plays with pagination.
    """
    db = get_database()
    plays = await db.plays.find().skip(skip).limit(limit).to_list(limit)
    return plays

@router.get("/search", response_model=List[PlayResponse])
async def search_plays(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    director_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search plays with various filters.
    """
    db = get_database()
    
    # Build query
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if genre:
        query["genre"] = {"$regex": genre, "$options": "i"}
    if director_id:
        query["director_id"] = director_id
    if actor_id:
        query["actors"] = actor_id
    
    # Duration range
    if min_duration is not None or max_duration is not None:
        query["duration_minutes"] = {}
        if min_duration is not None:
            query["duration_minutes"]["$gte"] = min_duration
        if max_duration is not None:
            query["duration_minutes"]["$lte"] = max_duration
    
    # Execute query with pagination
    plays = await db.plays.find(query).skip(skip).limit(limit).to_list(limit)
    return plays

@router.get("/{play_id}", response_model=PlayResponse)
async def read_play(
    play_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific play by ID.
    """
    db = get_database()
    play = await db.plays.find_one({"id": play_id})
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    return play

@router.put("/{play_id}", response_model=PlayResponse)
async def update_play(
    play_id: str,
    play_update: PlayUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update a play. Admin only.
    """
    db = get_database()
    
    # Check if play exists
    existing_play = await db.plays.find_one({"id": play_id})
    if not existing_play:
        raise HTTPException(status_code=404, detail="Play not found")
    
    # If updating director, check if new director exists
    if play_update.director_id:
        director = await db.directors.find_one({"id": play_update.director_id})
        if not director:
            raise HTTPException(status_code=404, detail="Director not found")
    
    # If updating actors, check if all new actors exist
    if play_update.actors:
        for actor_id in play_update.actors:
            actor = await db.actors.find_one({"id": actor_id})
            if not actor:
                raise HTTPException(status_code=404, detail=f"Actor with id {actor_id} not found")
    
    # Prepare update data
    update_data = play_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update play
        await db.plays.update_one(
            {"id": play_id},
            {"$set": update_data}
        )
        
        # If director changed, update relations
        if play_update.director_id:
            # Remove play from old director's plays list
            await db.directors.update_one(
                {"id": existing_play["director_id"]},
                {"$pull": {"plays": play_id}}
            )
            # Add play to new director's plays list
            await db.directors.update_one(
                {"id": play_update.director_id},
                {"$addToSet": {"plays": play_id}}
            )
        
        # If actors changed, update relations
        if play_update.actors:
            # Remove play from old actors' plays list
            for actor_id in existing_play["actors"]:
                if actor_id not in play_update.actors:
                    await db.actors.update_one(
                        {"id": actor_id},
                        {"$pull": {"plays": play_id}}
                    )
            # Add play to new actors' plays list
            for actor_id in play_update.actors:
                if actor_id not in existing_play["actors"]:
                    await db.actors.update_one(
                        {"id": actor_id},
                        {"$addToSet": {"plays": play_id}}
                    )
    
    # Get updated play
    updated_play = await db.plays.find_one({"id": play_id})
    return updated_play

@router.delete("/{play_id}", status_code=204)
async def delete_play(
    play_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete a play. Admin only.
    """
    db = get_database()
    
    # Check if play exists
    play = await db.plays.find_one({"id": play_id})
    if not play:
        raise HTTPException(status_code=404, detail="Play not found")
    
    # Remove play from director's plays list
    await db.directors.update_one(
        {"id": play["director_id"]},
        {"$pull": {"plays": play_id}}
    )
    
    # Remove play from actors' plays list
    for actor_id in play["actors"]:
        await db.actors.update_one(
            {"id": actor_id},
            {"$pull": {"plays": play_id}}
        )
    
    # Delete showtimes for this play
    await db.showtimes.delete_many({"play_id": play_id})
    
    # Get tickets associated with this play's showtimes
    showtimes = await db.showtimes.find({"play_id": play_id}).to_list(1000)
    showtime_ids = [s["id"] for s in showtimes]
    
    # Delete tickets for these showtimes
    if showtime_ids:
        await db.tickets.delete_many({"showtime_id": {"$in": showtime_ids}})
    
    # Delete play
    await db.plays.delete_one({"id": play_id})
    
    return None