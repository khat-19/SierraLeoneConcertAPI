from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Actor
from app.schemas.actor import ActorCreate, ActorUpdate, ActorResponse, ActorSearchParams
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ActorResponse, status_code=201)
async def create_actor(
    actor: ActorCreate, 
    current_user: User = Depends(check_admin_permission)
):
    """
    Create a new actor. Admin only.
    """
    db = get_database()
    
    # Check if plays exist
    for play_id in actor.plays:
        play = await db.plays.find_one({"id": play_id})
        if not play:
            raise HTTPException(status_code=404, detail=f"Play with id {play_id} not found")
    
    # Create actor object
    new_actor = Actor(
        **actor.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert actor
    actor_dict = new_actor.dict()
    await db.actors.insert_one(actor_dict)
    
    # Update plays' actors list
    for play_id in actor.plays:
        await db.plays.update_one(
            {"id": play_id},
            {"$addToSet": {"actors": new_actor.id}}
        )
    
    return actor_dict

@router.get("/", response_model=List[ActorResponse])
async def read_actors(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all actors with pagination.
    """
    db = get_database()
    actors = await db.actors.find().skip(skip).limit(limit).to_list(limit)
    return actors

@router.get("/search", response_model=List[ActorResponse])
async def search_actors(
    name: Optional[str] = None,
    play_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search actors with filters.
    """
    db = get_database()
    
    # Build query
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if play_id:
        query["plays"] = play_id
    
    # Execute query with pagination
    actors = await db.actors.find(query).skip(skip).limit(limit).to_list(limit)
    return actors

@router.get("/{actor_id}", response_model=ActorResponse)
async def read_actor(
    actor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific actor by ID.
    """
    db = get_database()
    actor = await db.actors.find_one({"id": actor_id})
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    return actor

@router.put("/{actor_id}", response_model=ActorResponse)
async def update_actor(
    actor_id: str,
    actor_update: ActorUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update an actor. Admin only.
    """
    db = get_database()
    
    # Check if actor exists
    existing_actor = await db.actors.find_one({"id": actor_id})
    if not existing_actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    # If updating plays, check if all new plays exist
    if actor_update.plays:
        for play_id in actor_update.plays:
            play = await db.plays.find_one({"id": play_id})
            if not play:
                raise HTTPException(status_code=404, detail=f"Play with id {play_id} not found")
    
    # Prepare update data
    update_data = actor_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update actor
        await db.actors.update_one(
            {"id": actor_id},
            {"$set": update_data}
        )
        
        # If plays changed, update relations
        if actor_update.plays:
            # Remove actor from old plays' actors list
            for play_id in existing_actor["plays"]:
                if play_id not in actor_update.plays:
                    await db.plays.update_one(
                        {"id": play_id},
                        {"$pull": {"actors": actor_id}}
                    )
            # Add actor to new plays' actors list
            for play_id in actor_update.plays:
                if play_id not in existing_actor["plays"]:
                    await db.plays.update_one(
                        {"id": play_id},
                        {"$addToSet": {"actors": actor_id}}
                    )
    
    # Get updated actor
    updated_actor = await db.actors.find_one({"id": actor_id})
    return updated_actor

@router.delete("/{actor_id}", status_code=204)
async def delete_actor(
    actor_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete an actor. Admin only.
    """
    db = get_database()
    
    # Check if actor exists
    actor = await db.actors.find_one({"id": actor_id})
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    
    # Remove actor from plays' actors list
    for play_id in actor["plays"]:
        await db.plays.update_one(
            {"id": play_id},
            {"$pull": {"actors": actor_id}}
        )
    
    # Delete actor
    await db.actors.delete_one({"id": actor_id})
    
    return None