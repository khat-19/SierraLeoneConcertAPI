from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.endpoints.auth import get_current_active_user, check_admin_permission
from app.db.database import get_database
from app.db.models import User, Director
from app.schemas.director import DirectorCreate, DirectorUpdate, DirectorResponse, DirectorSearchParams
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=DirectorResponse, status_code=201)
async def create_director(
    director: DirectorCreate, 
    current_user: User = Depends(check_admin_permission)
):
    """
    Create a new director. Admin only.
    """
    db = get_database()
    
    # Check if plays exist
    for play_id in director.plays:
        play = await db.plays.find_one({"id": play_id})
        if not play:
            raise HTTPException(status_code=404, detail=f"Play with id {play_id} not found")
    
    # Create director object
    new_director = Director(
        **director.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert director
    director_dict = new_director.dict()
    await db.directors.insert_one(director_dict)
    
    # Update plays' director_id
    for play_id in director.plays:
        await db.plays.update_one(
            {"id": play_id},
            {"$set": {"director_id": new_director.id}}
        )
    
    return director_dict

@router.get("/", response_model=List[DirectorResponse])
async def read_directors(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all directors with pagination.
    """
    db = get_database()
    directors = await db.directors.find().skip(skip).limit(limit).to_list(limit)
    return directors

@router.get("/search", response_model=List[DirectorResponse])
async def search_directors(
    name: Optional[str] = None,
    play_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search directors with filters.
    """
    db = get_database()
    
    # Build query
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if play_id:
        query["plays"] = play_id
    
    # Execute query with pagination
    directors = await db.directors.find(query).skip(skip).limit(limit).to_list(limit)
    return directors

@router.get("/{director_id}", response_model=DirectorResponse)
async def read_director(
    director_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific director by ID.
    """
    db = get_database()
    director = await db.directors.find_one({"id": director_id})
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    return director

@router.put("/{director_id}", response_model=DirectorResponse)
async def update_director(
    director_id: str,
    director_update: DirectorUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """
    Update a director. Admin only.
    """
    db = get_database()
    
    # Check if director exists
    existing_director = await db.directors.find_one({"id": director_id})
    if not existing_director:
        raise HTTPException(status_code=404, detail="Director not found")
    
    # If updating plays, check if all new plays exist
    if director_update.plays:
        for play_id in director_update.plays:
            play = await db.plays.find_one({"id": play_id})
            if not play:
                raise HTTPException(status_code=404, detail=f"Play with id {play_id} not found")
    
    # Prepare update data
    update_data = director_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update director
        await db.directors.update_one(
            {"id": director_id},
            {"$set": update_data}
        )
        
        # If plays changed, update relations
        if director_update.plays:
            # For plays that are no longer directed by this director
            for play_id in existing_director["plays"]:
                if play_id not in director_update.plays:
                    await db.plays.update_one(
                        {"id": play_id, "director_id": director_id},
                        {"$set": {"director_id": ""}}
                    )
            
            # For new plays directed by this director
            for play_id in director_update.plays:
                if play_id not in existing_director["plays"]:
                    # Check current director of the play
                    play = await db.plays.find_one({"id": play_id})
                    if play and play.get("director_id"):
                        # Remove play from old director's plays list
                        await db.directors.update_one(
                            {"id": play["director_id"]},
                            {"$pull": {"plays": play_id}}
                        )
                    
                    # Update play's director
                    await db.plays.update_one(
                        {"id": play_id},
                        {"$set": {"director_id": director_id}}
                    )
    
    # Get updated director
    updated_director = await db.directors.find_one({"id": director_id})
    return updated_director

@router.delete("/{director_id}", status_code=204)
async def delete_director(
    director_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """
    Delete a director. Admin only.
    """
    db = get_database()
    
    # Check if director exists
    director = await db.directors.find_one({"id": director_id})
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")
    
    # Update plays to remove this director
    for play_id in director["plays"]:
        await db.plays.update_one(
            {"id": play_id},
            {"$set": {"director_id": ""}}
        )
    
    # Delete director
    await db.directors.delete_one({"id": director_id})
    
    return None