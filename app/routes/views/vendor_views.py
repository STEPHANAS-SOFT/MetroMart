from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...schemas import VendorResponse, VendorCreate, VendorUpdate
from ...models import Vendor, VendorType, Order, OrderStatus, Item, VendorWallet, WalletTransaction, User, ItemCategory

router = APIRouter(prefix="/vendors", tags=["vendor views"])


class VendorProfile(BaseModel):
    id: int
    firebase_uid: str
    name: str
    vendor_type: str
    description: Optional[str]
    email: str
    phone_number: str
    address: str
    latitude: float
    longitude: float
    logo_url: Optional[str]
    has_own_delivery: bool
    is_active: bool
    opening_time: Optional[str]
    closing_time: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Business metrics
    total_orders: int
    completed_orders: int
    pending_orders: int
    total_revenue: float
    avg_order_value: float
    menu_items_count: int
    active_items_count: int
    wallet_balance: float
    rating: float
    total_customers: int
    repeat_customers: int
    last_order_date: Optional[datetime]
    is_premium_vendor: bool

    class Config:
        from_attributes = True


class VendorPerformanceStats(BaseModel):
    vendor_id: int
    vendor_name: str
    performance_period: str
    orders_completed: int
    revenue: float
    avg_order_value: float
    order_acceptance_rate: float
    avg_preparation_time: int
    customer_satisfaction: float
    top_selling_items: List[dict]
    peak_hours: List[str]
    growth_metrics: dict


class VendorComparison(BaseModel):
    vendor_id: int
    vendor_name: str
    vendor_type: str
    is_active: bool
    total_orders: int
    total_revenue: float
    avg_rating: float
    items_count: int
    last_30_days_orders: int
    market_share: float


@router.get("/", response_model=List[VendorResponse], dependencies=[Depends(verify_api_key)])
def get_all_vendors_enhanced(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, description, or address"),
    vendor_type: Optional[VendorType] = Query(None, description="Filter by vendor type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_delivery: Optional[bool] = Query(None, description="Filter by delivery capability"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    near_lat: Optional[float] = Query(None, description="Latitude for nearby search"),
    near_lng: Optional[float] = Query(None, description="Longitude for nearby search"),
    radius_km: Optional[float] = Query(10.0, ge=0.1, le=50, description="Search radius in km"),
    db: Session = Depends(get_db)
):
    """Get all vendors with enhanced filtering and search capabilities"""
    query = db.query(Vendor)
    
    # Text search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vendor.name.ilike(search_term),
                Vendor.description.ilike(search_term),
                Vendor.address.ilike(search_term)
            )
        )
    
    # Filter by vendor type
    if vendor_type:
        query = query.filter(Vendor.vendor_type == vendor_type)
    
    # Filter by active status
    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)
    
    # Filter by delivery capability
    if has_delivery is not None:
        query = query.filter(Vendor.has_own_delivery == has_delivery)
    
    # Location-based filtering
    if near_lat is not None and near_lng is not None:
        # Simple bounding box (for production, use PostGIS or similar)
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.320 * abs(near_lat) / 90.0) if near_lat else radius_km / 111.320
        
        min_lat = near_lat - lat_delta
        max_lat = near_lat + lat_delta
        min_lng = near_lng - lng_delta
        max_lng = near_lng + lng_delta
        
        query = query.filter(
            and_(
                Vendor.latitude.between(min_lat, max_lat),
                Vendor.longitude.between(min_lng, max_lng)
            )
        )
    
    vendors = query.offset(skip).limit(limit).all()

    # Calculate average rating for each vendor
    enhanced_vendors = []
    for v in vendors:
        avg_rating = db.query(func.avg(Vendor.rating)).filter(Vendor.id == v.id).scalar() or 0.0
        v.rating = float(round(avg_rating, 2))  # round to 2 decimal places
        enhanced_vendors.append(v)

    return enhanced_vendors
    # return vendors


@router.get("/profile/{vendor_id}", response_model=VendorProfile, dependencies=[Depends(verify_api_key)])
def get_vendor_profile(vendor_id: int, db: Session = Depends(get_db)):
    """Get comprehensive vendor profile with business metrics"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    # Get order statistics
    orders = db.query(Order).filter(Order.vendor_id == vendor_id).all()
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == OrderStatus.DELIVERED])
    pending_orders = len([o for o in orders if o.status == OrderStatus.PENDING])
    
    # Calculate revenue (only completed orders)
    total_revenue = sum(
        float(order.total_amount) 
        for order in orders 
        if order.status == OrderStatus.DELIVERED
    )
    
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # Get menu items count
    menu_items = db.query(Item).filter(Item.vendor_id == vendor_id).all()
    menu_items_count = len(menu_items)
    active_items_count = len([item for item in menu_items if item.is_available])
    
    # Get wallet balance
    wallet = db.query(VendorWallet).filter(VendorWallet.vendor_id == vendor_id).first()
    wallet_balance = float(wallet.balance) if wallet else 0.0
    
    # Rating (placeholder - would be calculated from actual reviews)
    # rating = 4.2  # Placeholder

    rating = db.query(func.avg(Vendor.rating)).filter(Vendor.id == vendor_id).scalar() or 0.0
    rating = float(round(rating, 2))


    # Customer metrics
    unique_customers = set(order.user_id for order in orders if order.user_id)
    total_customers = len(unique_customers)
    
    # Repeat customers (customers with more than 1 order)
    customer_order_counts = {}
    for order in orders:
        if order.user_id:
            customer_order_counts[order.user_id] = customer_order_counts.get(order.user_id, 0) + 1
    
    repeat_customers = len([count for count in customer_order_counts.values() if count > 1])
    
    # Last order date
    last_order_date = None
    if orders:
        last_order_date = max(order.created_at for order in orders)
    
    # Premium vendor status (>100 orders or >$10k revenue)
    is_premium_vendor = completed_orders > 100 or total_revenue > 10000
    
    return VendorProfile(
        id=vendor.id,
        firebase_uid=vendor.firebase_uid,
        name=vendor.name,
        vendor_type=vendor.vendor_type.value,
        description=vendor.description,
        email=vendor.email,
        phone_number=vendor.phone_number,
        address=vendor.address,
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        logo_url=vendor.logo_url,
        has_own_delivery=vendor.has_own_delivery,
        is_active=vendor.is_active,
        opening_time=vendor.opening_time,
        closing_time=vendor.closing_time,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        avg_order_value=avg_order_value,
        menu_items_count=menu_items_count,
        active_items_count=active_items_count,
        wallet_balance=wallet_balance,
        rating=rating,
        total_customers=total_customers,
        repeat_customers=repeat_customers,
        last_order_date=last_order_date,
        is_premium_vendor=is_premium_vendor
    )


@router.get("/analytics/overview", dependencies=[Depends(verify_api_key)])
def get_vendors_analytics_overview(db: Session = Depends(get_db)):
    """Get platform-wide vendor analytics"""
    
    # Basic vendor counts
    total_vendors = db.query(Vendor).count()
    active_vendors = db.query(Vendor).filter(Vendor.is_active == True).count()
    inactive_vendors = total_vendors - active_vendors
    
    # Vendor type distribution
    vendor_type_counts = (
        db.query(Vendor.vendor_type, func.count(Vendor.id))
        .group_by(Vendor.vendor_type)
        .all()
    )
    
    vendor_types = {vtype.value: count for vtype, count in vendor_type_counts}
    
    # Recent activity
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_vendors_30_days = db.query(Vendor).filter(Vendor.created_at >= thirty_days_ago).count()
    
    # Revenue metrics
    total_platform_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == OrderStatus.DELIVERED
    ).scalar() or 0
    
    # Vendors with recent orders
    vendors_with_recent_orders = (
        db.query(Vendor)
        .join(Order)
        .filter(Order.created_at >= thirty_days_ago)
        .distinct()
        .count()
    )
    
    return {
        "total_vendors": total_vendors,
        "active_vendors": active_vendors,
        "inactive_vendors": inactive_vendors,
        "vendor_type_distribution": vendor_types,
        "new_vendors_last_30_days": new_vendors_30_days,
        "vendors_with_recent_orders": vendors_with_recent_orders,
        "vendor_activation_rate": round((active_vendors / total_vendors * 100), 2) if total_vendors > 0 else 0,
        "total_platform_revenue": float(total_platform_revenue),
        "generated_at": datetime.utcnow()
    }


@router.get("/performance/top", response_model=List[VendorComparison], dependencies=[Depends(verify_api_key)])
def get_top_performing_vendors(
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("revenue", description="Sort by: revenue, orders, rating, growth"),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get top performing vendors with comparison metrics"""
    
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    vendors_data = []
    vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
    
    # Calculate total platform orders for market share
    total_platform_orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_date,
            Order.status == OrderStatus.DELIVERED
        )
    ).count()
    
    for vendor in vendors:
        # Get vendor orders in period
        orders = db.query(Order).filter(
            and_(
                Order.vendor_id == vendor.id,
                Order.created_at >= start_date,
                Order.status == OrderStatus.DELIVERED
            )
        ).all()
        
        total_orders = len(orders)
        total_revenue = sum(float(order.total_amount) for order in orders)
        
        # Get total historical orders for this vendor
        all_orders_count = db.query(Order).filter(Order.vendor_id == vendor.id).count()
        
        # Get items count
        items_count = db.query(Item).filter(Item.vendor_id == vendor.id).count()
        
        # Market share
        market_share = (total_orders / total_platform_orders * 100) if total_platform_orders > 0 else 0
        
        # Placeholder rating
        avg_rating = 4.5  # Would be calculated from actual reviews
        
        vendors_data.append(VendorComparison(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            vendor_type=vendor.vendor_type.value,
            is_active=vendor.is_active,
            total_orders=all_orders_count,
            total_revenue=total_revenue,
            avg_rating=avg_rating,
            items_count=items_count,
            last_30_days_orders=total_orders,
            market_share=market_share
        ))
    
    # Sort by specified criterion
    if sort_by == "revenue":
        vendors_data.sort(key=lambda x: x.total_revenue, reverse=True)
    elif sort_by == "orders":
        vendors_data.sort(key=lambda x: x.last_30_days_orders, reverse=True)
    elif sort_by == "rating":
        vendors_data.sort(key=lambda x: x.avg_rating, reverse=True)
    elif sort_by == "growth":
        vendors_data.sort(key=lambda x: x.last_30_days_orders, reverse=True)  # Simplified
    
    return vendors_data[:limit]


@router.get("/{vendor_id}/performance", response_model=VendorPerformanceStats, dependencies=[Depends(verify_api_key)])
def get_vendor_performance_stats(
    vendor_id: int,
    days_back: int = Query(30, ge=1, le=365, description="Performance period in days"),
    db: Session = Depends(get_db)
):
    """Get detailed performance statistics for a vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    # Date range
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get orders in period
    orders = db.query(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.created_at >= start_date
        )
    ).all()
    
    completed_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
    total_orders = len(orders)
    orders_completed = len(completed_orders)
    
    # Revenue
    revenue = sum(float(order.total_amount) for order in completed_orders)
    avg_order_value = revenue / orders_completed if orders_completed > 0 else 0
    
    # Order acceptance rate
    pending_orders = [o for o in orders if o.status == OrderStatus.PENDING]
    rejected_orders = [o for o in orders if o.status == OrderStatus.REJECTED]
    accepted_orders = [o for o in orders if o.status not in [OrderStatus.PENDING, OrderStatus.REJECTED]]
    
    acceptance_rate = (len(accepted_orders) / total_orders * 100) if total_orders > 0 else 0
    
    # Average preparation time (placeholder)
    avg_preparation_time = 25  # minutes - would be calculated from actual data
    
    # Customer satisfaction (placeholder)
    customer_satisfaction = 4.3  # Would be from actual ratings
    
    # Top selling items (placeholder - would require OrderItem joins)
    top_selling_items = [
        {"item_name": "Chicken Burger", "quantity_sold": 45, "revenue": 675.0},
        {"item_name": "Pizza Margherita", "quantity_sold": 32, "revenue": 480.0}
    ]
    
    # Peak hours analysis
    if orders:
        hour_counts = {}
        for order in orders:
            hour = order.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Get top 3 hours
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hours_list = [f"{hour}:00-{hour+1}:00" for hour, _ in peak_hours]
    else:
        peak_hours_list = []
    
    # Growth metrics
    growth_metrics = {
        "orders_growth": 15.2,  # Placeholder percentage
        "revenue_growth": 22.5,
        "customer_growth": 18.3
    }
    
    return VendorPerformanceStats(
        vendor_id=vendor_id,
        vendor_name=vendor.name,
        performance_period=f"Last {days_back} days",
        orders_completed=orders_completed,
        revenue=revenue,
        avg_order_value=avg_order_value,
        order_acceptance_rate=acceptance_rate,
        avg_preparation_time=avg_preparation_time,
        customer_satisfaction=customer_satisfaction,
        top_selling_items=top_selling_items,
        peak_hours=peak_hours_list,
        growth_metrics=growth_metrics
    )


@router.get("/{vendor_id}/customers", dependencies=[Depends(verify_api_key)])
def get_vendor_customers(
    vendor_id: int,
    include_one_time: bool = Query(True, description="Include one-time customers"),
    sort_by: str = Query("total_spent", description="Sort by: total_spent, order_count, last_order"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get vendor's customer base with ordering statistics"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    # Get all orders for this vendor
    orders = db.query(Order).filter(Order.vendor_id == vendor_id).all()
    
    # Group by customer
    customer_data = {}
    for order in orders:
        if order.user_id:
            if order.user_id not in customer_data:
                customer_data[order.user_id] = {
                    "user_id": order.user_id,
                    "orders": [],
                    "total_spent": 0,
                    "order_count": 0
                }
            
            customer_data[order.user_id]["orders"].append(order)
            if order.status == OrderStatus.DELIVERED:
                customer_data[order.user_id]["total_spent"] += float(order.total_amount)
            customer_data[order.user_id]["order_count"] += 1
    
    # Get user details and format response
    customers_list = []
    for user_id, data in customer_data.items():
        # Skip one-time customers if requested
        if not include_one_time and data["order_count"] == 1:
            continue
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            last_order = max(order.created_at for order in data["orders"]) if data["orders"] else None
            
            customers_list.append({
                "user_id": user_id,
                "user_name": user.full_name,
                "user_email": user.email,
                "order_count": data["order_count"],
                "total_spent": data["total_spent"],
                "avg_order_value": data["total_spent"] / data["order_count"] if data["order_count"] > 0 else 0,
                "last_order_date": last_order,
                "customer_type": "repeat" if data["order_count"] > 1 else "new"
            })
    
    # Sort customers
    if sort_by == "total_spent":
        customers_list.sort(key=lambda x: x["total_spent"], reverse=True)
    elif sort_by == "order_count":
        customers_list.sort(key=lambda x: x["order_count"], reverse=True)
    elif sort_by == "last_order":
        customers_list.sort(key=lambda x: x["last_order_date"] or datetime.min, reverse=True)
    
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "total_customers": len(customers_list),
        "customers": customers_list[:limit]
    }


@router.post("/{vendor_id}/toggle-status", dependencies=[Depends(verify_api_key)])
def toggle_vendor_status(
    vendor_id: int,
    is_active: bool,
    reason: Optional[str] = Query(None, description="Reason for status change"),
    db: Session = Depends(get_db)
):
    """Toggle vendor active/inactive status"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {vendor_id} not found")
    
    old_status = vendor.is_active
    vendor.is_active = is_active
    vendor.updated_at = datetime.utcnow()
    
    db.commit()
    
    # In production, you'd also:
    # 1. Notify pending customers if deactivating
    # 2. Handle pending orders appropriately
    # 3. Send notification to vendor
    # 4. Log the status change
    
    status_text = "activated" if is_active else "deactivated"
    
    return {
        "message": f"Vendor '{vendor.name}' has been {status_text}",
        "vendor_id": vendor_id,
        "old_status": old_status,
        "new_status": is_active,
        "reason": reason,
        "updated_at": datetime.utcnow()
    }


@router.get("/nearby/{lat}/{lng}", response_model=List[VendorResponse], dependencies=[Depends(verify_api_key)])
def get_vendors_near_location(
    lat: float,
    lng: float,
    radius_km: float = Query(10.0, ge=0.1, le=50, description="Search radius in kilometers"),
    vendor_type: Optional[VendorType] = Query(None, description="Filter by vendor type"),
    food_category: Optional[str] = Query(None, description="Filter by food category (e.g., 'Rice Dishes', 'Swallow', 'Soups')"),
    is_open_now: bool = Query(False, description="Filter by currently open vendors"),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get vendors near a specific location with advanced filtering"""
    
    # Simple bounding box calculation
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.320 * abs(lat) / 90.0) if lat else radius_km / 111.320
    
    min_lat = lat - lat_delta
    max_lat = lat + lat_delta
    min_lng = lng - lng_delta
    max_lng = lng + lng_delta
    
    query = db.query(Vendor).filter(
        and_(
            Vendor.is_active == True,
            Vendor.latitude.between(min_lat, max_lat),
            Vendor.longitude.between(min_lng, max_lng)
        )
    )
    
    # Filter by vendor type
    if vendor_type:
        query = query.filter(Vendor.vendor_type == vendor_type)
    
    # # Filter by food category - join with ItemCategory to find vendors selling that category
    # if food_category:
    #     query = query.join(ItemCategory).filter(
    #         ItemCategory.name.ilike(f"%{food_category}%")
    #     ).distinct()

    if food_category:
        query = (
        query.join(Item, Vendor.id == Item.vendor_id)
             .join(ItemCategory, Item.category_id == ItemCategory.id)
             .filter(ItemCategory.name.ilike(f"%{food_category}%"))
             .distinct()
    )

    
    # Filter by operating hours (simplified - would need proper time handling)
    if is_open_now:
        current_hour = datetime.utcnow().hour
        # This is a simplified check - real implementation would parse opening/closing times
        query = query.filter(
            and_(
                Vendor.opening_time.isnot(None),
                Vendor.closing_time.isnot(None)
            )
        )
    
    vendors = query.limit(limit).all()
    
    # Calculate distances and sort by proximity
    # In production, you'd use proper geospatial calculations
    for vendor in vendors:
        # Simplified distance calculation
        vendor.distance_km = ((vendor.latitude - lat) ** 2 + (vendor.longitude - lng) ** 2) ** 0.5 * 111
        # Calculate average rating
        avg_rating = db.query(func.avg(Vendor.rating)).filter(Vendor.id == vendor.id).scalar() or 0.0
        vendor.rating = float(round(avg_rating, 2))
    
    # Sort by distance
    vendors.sort(key=lambda v: getattr(v, 'distance_km', float('inf')))

        # Optional: filter by minimum rating
    if min_rating is not None:
        vendors = [v for v in vendors if v.rating >= min_rating]
    
    return vendors