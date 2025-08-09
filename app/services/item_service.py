from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.user import Item
from app.schemas.user import ItemCreate, ItemUpdate

def get_items(db: Session, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None):
    query = db.query(Item)
    if owner_id is not None:
        query = query.filter(Item.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()

def get_item(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()

def create_user_item(db: Session, item: ItemCreate, user_id: int) -> Item:
    db_item = Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item: ItemUpdate) -> Optional[Item]:
    db_item = get_item(db, item_id=item_id)
    if db_item is None:
        return None
    
    update_data = item.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int) -> Optional[Item]:
    db_item = get_item(db, item_id=item_id)
    if db_item is None:
        return None
    db.delete(db_item)
    db.commit()
    return db_item
