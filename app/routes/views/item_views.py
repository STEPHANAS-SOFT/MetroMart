from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import any_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...schemas import ItemResponse, ItemCreate, ItemUpdate
from ...models import Item, ItemCategory, ItemVariation, ItemAddon, Vendor, ItemAddonGroup

router = APIRouter(prefix="/items", tags=["item views"])


class ItemAvailabilityUpdate(BaseModel):
    is_available: bool
    reason: Optional[str] = None


class ItemPriceUpdate(BaseModel):
    new_price: float
    effective_date: Optional[datetime] = None


class ItemSearchFilters(BaseModel):
    category_id: Optional[int] = None
    vendor_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_available: Optional[bool] = True
    has_variations: Optional[bool] = None
    has_addons: Optional[bool] = None


class ItemWithDetails(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    is_available: bool
    vendor_id: int
    vendor_name: str
    category_id: Optional[int]
    category_name: Optional[str]
    image_url: Optional[str]
    preparation_time: Optional[int]
    variations_count: int
    addons_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ItemAddonResponse(BaseModel):
    id: int
    name: str
    price: float
    is_available: bool
    image_url: Optional[str]
    description: Optional[str]


class ItemAddonGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    addons: List[ItemAddonResponse]  # Include addons in the response


class ItemWithAddonGroupsResponse(ItemResponse):
    addon_groups: List[ItemAddonGroupResponse]


class ItemVariationResponse(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]


class ItemWithAddonGroupsAndVariationsResponse(ItemWithAddonGroupsResponse):
    variations: List[ItemVariationResponse]  # Include variations in the response


@router.get("/", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def get_all_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    db: Session = Depends(get_db)
):
    """Get all items with optional filtering"""
    query = db.query(Item)
    
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    if vendor_id:
        query = query.filter(Item.vendor_id == vendor_id)
    
    if is_available is not None:
        query = query.filter(Item.is_available == is_available)
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/detailed", response_model=List[ItemWithDetails], dependencies=[Depends(verify_api_key)])
def get_items_with_details(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get items with detailed information including vendor and category names"""
    items_query = """
    SELECT 
        i.id, i.name, i.description, i.price, i.is_available, 
        i.vendor_id, v.name as vendor_name,
        i.category_id, ic.name as category_name,
        i.image_url, i.preparation_time,
        i.created_at, i.updated_at,
        COUNT(DISTINCT iv.id) as variations_count,
        COUNT(DISTINCT ia.id) as addons_count
    FROM items i
    LEFT JOIN vendors v ON i.vendor_id = v.id
    LEFT JOIN item_categories ic ON i.category_id = ic.id
    LEFT JOIN item_variations iv ON i.id = iv.item_id
    LEFT JOIN item_addon_groups iag ON i.id = iag.item_id
    LEFT JOIN item_addons ia ON iag.id = ia.group_id
    GROUP BY i.id, v.name, ic.name
    ORDER BY i.created_at DESC
    OFFSET :skip LIMIT :limit
    """
    
    result = db.execute(items_query, {"skip": skip, "limit": limit})
    items_data = []
    
    for row in result:
        items_data.append(ItemWithDetails(
            id=row.id,
            name=row.name,
            description=row.description,
            price=float(row.price),
            is_available=row.is_available,
            vendor_id=row.vendor_id,
            vendor_name=row.vendor_name or "Unknown",
            category_id=row.category_id,
            category_name=row.category_name,
            image_url=row.image_url,
            preparation_time=row.preparation_time,
            variations_count=row.variations_count or 0,
            addons_count=row.addons_count or 0,
            created_at=row.created_at,
            updated_at=row.updated_at
        ))
    
    return items_data


@router.get("/{item_id}", response_model=ItemWithAddonGroupsAndVariationsResponse, dependencies=[Depends(verify_api_key)])
def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID with addon group data and variations"""
    # Query the item
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")

    # Query addon groups
    addon_groups = (
        db.query(ItemAddonGroup)
        .join(Item, ItemAddonGroup.id == any_(Item.addon_group_ids))
        .filter(Item.id == item_id)
        .all()
    )

    # Query addons for each group
    addon_groups_with_addons = []
    for group in addon_groups:
        addons = db.query(ItemAddon).filter(ItemAddon.group_id == group.id).all()
        addon_groups_with_addons.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "addons": [
                {
                    "id": addon.id,
                    "name": addon.name,
                    "price": addon.price,
                    "image_url": addon.image_url,
                    "is_available": addon.is_available,
                    "description": addon.description
                }
                for addon in addons
            ]
        })

    # Query variations
    variations = db.query(ItemVariation).filter(ItemVariation.item_id == item_id).all()

    # Construct the response
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "base_price": item.base_price,
        "image_url": item.image_url,
        "is_available": item.is_available,
        "allows_addons": item.allows_addons,
        "vendor_id": item.vendor_id,
        "category_id": item.category_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "addon_groups": addon_groups_with_addons,
        "variations": [
            {
                "id": variation.id,
                "name": variation.name,
                "price": variation.price,
                "description": variation.description
            }
            for variation in variations
        ]
    }


@router.get("/vendor/{vendor_id}/menu", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def get_vendor_menu_items(
    vendor_id: int, 
    include_unavailable: bool = Query(False, description="Include unavailable items"),
    db: Session = Depends(get_db)
):
    """Get all items for a specific vendor (menu items)"""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    query = db.query(Item).filter(Item.vendor_id == vendor_id)
    
    if not include_unavailable:
        query = query.filter(Item.is_available == True)
    
    items = query.order_by(Item.name).all()
    return items


@router.get("/category/{category_id}/items", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def get_items_by_category(
    category_id: int,
    include_unavailable: bool = Query(False, description="Include unavailable items"),
    db: Session = Depends(get_db)
):
    """Get all items in a specific category"""
    # Verify category exists
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
    
    query = db.query(Item).filter(Item.category_id == category_id)
    
    if not include_unavailable:
        query = query.filter(Item.is_available == True)
    
    items = query.order_by(Item.name).all()
    return items


@router.post("/{item_id}/toggle-availability", dependencies=[Depends(verify_api_key)])
def toggle_item_availability(
    item_id: int,
    availability_update: ItemAvailabilityUpdate,
    db: Session = Depends(get_db)
):
    """Toggle item availability (enable/disable for ordering)"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    old_status = item.is_available
    item.is_available = availability_update.is_available
    item.updated_at = datetime.utcnow()
    
    db.commit()
    
    status_text = "enabled" if availability_update.is_available else "disabled"
    
    return {
        "message": f"Item '{item.name}' {status_text} successfully",
        "item_id": item_id,
        "old_status": old_status,
        "new_status": availability_update.is_available,
        "reason": availability_update.reason
    }


@router.put("/{item_id}/price", dependencies=[Depends(verify_api_key)])
def update_item_price(
    item_id: int,
    price_update: ItemPriceUpdate,
    db: Session = Depends(get_db)
):
    """Update item price"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    if price_update.new_price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than 0")
    
    old_price = float(item.price)
    item.price = price_update.new_price
    item.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Price updated for item '{item.name}'",
        "item_id": item_id,
        "item_name": item.name,
        "old_price": old_price,
        "new_price": float(item.price),
        "effective_date": price_update.effective_date or datetime.utcnow()
    }


@router.get("/search/advanced", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def advanced_item_search(
    q: Optional[str] = Query(None, description="Search query for item name/description"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor"), 
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    is_available: Optional[bool] = Query(True, description="Filter by availability"),
    has_variations: Optional[bool] = Query(None, description="Filter items with variations"),
    preparation_time_max: Optional[int] = Query(None, ge=0, description="Max preparation time in minutes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Advanced search for items with multiple filters"""
    query = db.query(Item)
    
    # Text search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Item.name.ilike(search_term)) | 
            (Item.description.ilike(search_term))
        )
    
    # Filter by category
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    # Filter by vendor
    if vendor_id:
        query = query.filter(Item.vendor_id == vendor_id)
    
    # Price range filter
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    
    # Availability filter
    if is_available is not None:
        query = query.filter(Item.is_available == is_available)
    
    # Preparation time filter
    if preparation_time_max is not None:
        query = query.filter(Item.preparation_time <= preparation_time_max)
    
    # Variations filter (requires join)
    if has_variations is not None:
        if has_variations:
            query = query.join(ItemVariation).distinct()
        else:
            # Items without variations - this is more complex, simplified for now
            pass
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}/variations", dependencies=[Depends(verify_api_key)])
def get_item_variations(item_id: int, db: Session = Depends(get_db)):
    """Get all variations for a specific item"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    variations = db.query(ItemVariation).filter(ItemVariation.item_id == item_id).all()
    return variations


@router.get("/{item_id}/addons", dependencies=[Depends(verify_api_key)])
def get_item_addons(item_id: int, db: Session = Depends(get_db)):
    """Get all addon groups and their addons for a specific item"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    
    # This would require proper joins - simplified for now
    # In a real implementation, you'd join ItemAddonGroup and ItemAddon tables
    addon_groups = []  # Placeholder
    
    return {
        "item_id": item_id,
        "item_name": item.name,
        "addon_groups": addon_groups
    }


@router.get("/popular/trending", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def get_trending_items(
    limit: int = Query(20, ge=1, le=100, description="Number of trending items to return"),
    days_back: int = Query(7, ge=1, le=30, description="Days to look back for trending calculation"),
    db: Session = Depends(get_db)
):
    """Get trending/popular items based on recent order frequency"""
    # This would typically require joining with OrderItem table to get actual order counts
    # For now, return recent items as a placeholder
    
    trending_items = (
        db.query(Item)
        .filter(Item.is_available == True)
        .order_by(Item.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return trending_items


@router.post("/bulk-update-availability", dependencies=[Depends(verify_api_key)])
def bulk_update_item_availability(
    item_ids: List[int],
    is_available: bool,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Bulk update availability for multiple items"""
    if not item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")
    
    if len(item_ids) > 100:  # Limit bulk operations
        raise HTTPException(status_code=400, detail="Maximum 100 items can be updated at once")
    
    # Update items
    updated_count = (
        db.query(Item)
        .filter(Item.id.in_(item_ids))
        .update({
            Item.is_available: is_available,
            Item.updated_at: datetime.utcnow()
        }, synchronize_session=False)
    )
    
    db.commit()
    
    status_text = "enabled" if is_available else "disabled"
    
    return {
        "message": f"Bulk update completed: {updated_count} items {status_text}",
        "items_updated": updated_count,
        "items_requested": len(item_ids),
        "new_availability_status": is_available,
        "reason": reason
    }