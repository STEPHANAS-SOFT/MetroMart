from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...schemas import VendorResponse, ItemResponse
from ...models import Vendor, Item, ItemCategory

router = APIRouter(prefix="/search", tags=["search views"])


@router.get("/vendors", response_model=List[VendorResponse], dependencies=[Depends(verify_api_key)])
def search_vendors(q: Optional[str] = Query(None), limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """Search vendors by name or description"""
    query = db.query(Vendor)
    if q:
        q_ilike = f"%{q}%"
        query = query.filter((Vendor.name.ilike(q_ilike)) | (Vendor.description.ilike(q_ilike)))
    vendors = query.offset(offset).limit(limit).all()
    return vendors


@router.get("/items", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def search_items(q: Optional[str] = Query(None), vendor_id: Optional[int] = None, limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """Search items by name, description or filter by vendor"""
    query = db.query(Item)
    if vendor_id:
        query = query.filter(Item.vendor_id == vendor_id)
    if q:
        q_ilike = f"%{q}%"
        query = query.filter((Item.name.ilike(q_ilike)) | (Item.description.ilike(q_ilike)))
    items = query.offset(offset).limit(limit).all()
    return items


@router.get("/vendors/nearby", response_model=List[VendorResponse], dependencies=[Depends(verify_api_key)])
def get_nearby_vendors(lat: float, lng: float, radius_km: float = 5.0, limit: int = 20, db: Session = Depends(get_db)):
    """Naive nearby implementation: filter by bounding box. For production use geospatial queries."""
    # Very simple latitude/longitude box (not accurate at scale)
    lat_delta = radius_km / 111.0  # approx degrees latitude per km
    lng_delta = radius_km / max(0.0001, (111.320 * abs(lat) / 90.0))
    min_lat, max_lat = lat - lat_delta, lat + lat_delta
    min_lng, max_lng = lng - lng_delta, lng + lng_delta
    vendors = db.query(Vendor).filter(Vendor.latitude >= min_lat, Vendor.latitude <= max_lat,
                                       Vendor.longitude >= min_lng, Vendor.longitude <= max_lng).limit(limit).all()
    return vendors


@router.get("/vendors/{vendor_id}/menu", response_model=List[ItemResponse], dependencies=[Depends(verify_api_key)])
def get_vendor_menu(vendor_id: int, db: Session = Depends(get_db)):
    """Return all items for a vendor"""
    items = db.query(Item).filter(Item.vendor_id == vendor_id).all()
    return items


@router.get("/categories/{category_id}/vendors", response_model=List[VendorResponse], dependencies=[Depends(verify_api_key)])
def get_vendors_by_category(category_id: int, db: Session = Depends(get_db)):
    """List vendors that have items in the specified category"""
    vendors = db.query(Vendor).join(Item).filter(Item.category_id == category_id).distinct().all()
    return vendors
