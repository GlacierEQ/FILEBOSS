from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import Item, ItemCreate, ItemUpdate
from app.services import item_service

router = APIRouter()

@router.post("/", response_model=Item)
def create_item(
    item: ItemCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_active_user)
):
    """Create new item"""
    return item_service.create_user_item(db=db, item=item, user_id=current_user.id)

@router.get("/", response_model=List[Item])
def read_items(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_active_user)
):
    """Retrieve items"""
    items = item_service.get_items(db, skip=skip, limit=limit, owner_id=current_user.id)
    return items

@router.get("/{item_id}", response_model=Item)
def read_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_active_user)
):
    """Get item by ID"""
    db_item = item_service.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return db_item

@router.put("/{item_id}", response_model=Item)
def update_item(
    item_id: int, 
    item: ItemUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_active_user)
):
    """Update an item"""
    db_item = item_service.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item_service.update_item(db=db, item_id=item_id, item=item)

@router.delete("/{item_id}", response_model=Item)
def delete_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_active_user)
):
    """Delete an item"""
    db_item = item_service.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item_service.delete_item(db=db, item_id=item_id)
