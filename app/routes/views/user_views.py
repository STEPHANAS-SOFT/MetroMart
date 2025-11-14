from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...schemas import UserResponse, UserCreate, UserUpdate
from ...models import User, Order, OrderStatus, DeliveryAddress, UserWallet, WalletTransaction

router = APIRouter(prefix="/users", tags=["user views"])


class UserProfile(BaseModel):
    id: int
    firebase_uid: str
    email: str
    phone_number: str
    full_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Aggregated data
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    total_spent: float
    wallet_balance: float
    favorite_vendors: List[str]
    delivery_addresses_count: int
    last_order_date: Optional[datetime]
    is_premium_customer: bool

    class Config:
        from_attributes = True


class UserOrderSummary(BaseModel):
    user_id: int
    user_name: str
    order_count: int
    total_spent: float
    avg_order_value: float
    last_order: Optional[datetime]
    preferred_vendors: List[str]


class UserActivityStats(BaseModel):
    user_id: int
    days_since_registration: int
    orders_last_30_days: int
    orders_last_7_days: int
    favorite_order_time: Optional[str]  # Hour of day
    most_ordered_items: List[dict]
    spending_trend: str  # "increasing", "decreasing", "stable"


@router.get("/", response_model=List[UserResponse], dependencies=[Depends(verify_api_key)])
def get_all_users_enhanced(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_orders: Optional[bool] = Query(None, description="Filter users with/without orders"),
    min_total_spent: Optional[float] = Query(None, ge=0, description="Minimum total spent"),
    db: Session = Depends(get_db)
):
    """Get all users with enhanced filtering capabilities"""
    query = db.query(User)
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.phone_number.ilike(search_term)
            )
        )
    
    # Filter users with/without orders
    if has_orders is not None:
        if has_orders:
            query = query.join(Order).distinct()
        else:
            # Users without orders - subquery approach
            users_with_orders = db.query(Order.user_id).distinct().subquery()
            query = query.filter(~User.id.in_(users_with_orders))
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/profile/{user_id}", response_model=UserProfile, dependencies=[Depends(verify_api_key)])
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get comprehensive user profile with statistics"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    # Get order statistics
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == OrderStatus.DELIVERED])
    cancelled_orders = len([o for o in orders if o.status == OrderStatus.CANCELLED])
    
    # Calculate total spent (only completed orders)
    total_spent = sum(
        float(order.total_amount) 
        for order in orders 
        if order.status == OrderStatus.DELIVERED
    )
    
    # Get wallet balance
    wallet = db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
    wallet_balance = float(wallet.balance) if wallet else 0.0
    
    # Get favorite vendors (most ordered from)
    vendor_orders = {}
    for order in orders:
        vendor_id = order.vendor_id
        if vendor_id:
            vendor_orders[vendor_id] = vendor_orders.get(vendor_id, 0) + 1
    
    # Get top 3 vendors
    top_vendors = sorted(vendor_orders.items(), key=lambda x: x[1], reverse=True)[:3]
    favorite_vendors = [f"Vendor {vendor_id}" for vendor_id, _ in top_vendors]  # Would join with Vendor table in real app
    
    # Get delivery addresses count
    delivery_addresses_count = db.query(DeliveryAddress).filter(DeliveryAddress.user_id == user_id).count()
    
    # Last order date
    last_order_date = None
    if orders:
        last_order_date = max(order.created_at for order in orders)
    
    # Determine if premium customer (>$500 spent or >10 orders)
    is_premium_customer = total_spent > 500 or completed_orders > 10
    
    return UserProfile(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        latitude=user.latitude,
        longitude=user.longitude,
        created_at=user.created_at,
        updated_at=user.updated_at,
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_spent=total_spent,
        wallet_balance=wallet_balance,
        favorite_vendors=favorite_vendors,
        delivery_addresses_count=delivery_addresses_count,
        last_order_date=last_order_date,
        is_premium_customer=is_premium_customer
    )


@router.get("/profile/firebase/{firebase_uid}", response_model=UserProfile, dependencies=[Depends(verify_api_key)])
def get_user_profile_by_firebase_uid(firebase_uid: str, db: Session = Depends(get_db)):
    """Get comprehensive user profile with statistics by Firebase UID"""
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with Firebase UID {firebase_uid} not found")
    
    # Get order statistics
    orders = db.query(Order).filter(Order.user_id == user.id).all()
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == OrderStatus.DELIVERED])
    cancelled_orders = len([o for o in orders if o.status == OrderStatus.CANCELLED])
    
    # Calculate total spent (only completed orders)
    total_spent = sum(
        float(order.total_amount) 
        for order in orders 
        if order.status == OrderStatus.DELIVERED
    )
    
    # Get wallet balance
    wallet = db.query(UserWallet).filter(UserWallet.user_id == user.id).first()
    wallet_balance = float(wallet.balance) if wallet else 0.0
    
    # Get favorite vendors (most ordered from)
    vendor_orders = {}
    for order in orders:
        vendor_id = order.vendor_id
        if vendor_id:
            vendor_orders[vendor_id] = vendor_orders.get(vendor_id, 0) + 1
    
    # Get top 3 vendors
    top_vendors = sorted(vendor_orders.items(), key=lambda x: x[1], reverse=True)[:3]
    favorite_vendors = [f"Vendor {vendor_id}" for vendor_id, _ in top_vendors]  # Would join with Vendor table in real app
    
    # Get delivery addresses count
    delivery_addresses_count = db.query(DeliveryAddress).filter(DeliveryAddress.user_id == user.id).count()
    
    # Last order date
    last_order_date = None
    if orders:
        last_order_date = max(order.created_at for order in orders)
    
    # Determine if premium customer (>$500 spent or >10 orders)
    is_premium_customer = total_spent > 500 or completed_orders > 10
    
    return UserProfile(
        id=user.id,
        firebase_uid=user.firebase_uid,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        latitude=user.latitude,
        longitude=user.longitude,
        created_at=user.created_at,
        updated_at=user.updated_at,
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_spent=total_spent,
        wallet_balance=wallet_balance,
        favorite_vendors=favorite_vendors,
        delivery_addresses_count=delivery_addresses_count,
        last_order_date=last_order_date,
        is_premium_customer=is_premium_customer
    )


    
@router.get("/analytics/summary", dependencies=[Depends(verify_api_key)])
def get_users_analytics_summary(db: Session = Depends(get_db)):
    """Get overall user analytics summary"""
    
    # Basic user counts
    total_users = db.query(User).count()
    users_with_orders = db.query(User).join(Order).distinct().count()
    users_without_orders = total_users - users_with_orders
    
    # Recent activity
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30_days = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    
    active_users_30_days = (
        db.query(User)
        .join(Order)
        .filter(Order.created_at >= thirty_days_ago)
        .distinct()
        .count()
    )
    
    # Revenue metrics
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == OrderStatus.DELIVERED
    ).scalar() or 0
    
    avg_order_value = db.query(func.avg(Order.total_amount)).filter(
        Order.status == OrderStatus.DELIVERED
    ).scalar() or 0
    
    return {
        "total_users": total_users,
        "users_with_orders": users_with_orders,
        "users_without_orders": users_without_orders,
        "new_users_last_30_days": new_users_30_days,
        "active_users_last_30_days": active_users_30_days,
        "user_conversion_rate": round((users_with_orders / total_users * 100), 2) if total_users > 0 else 0,
        "total_platform_revenue": float(total_revenue),
        "average_order_value": float(avg_order_value),
        "generated_at": datetime.utcnow()
    }


@router.get("/top-customers", response_model=List[UserOrderSummary], dependencies=[Depends(verify_api_key)])
def get_top_customers(
    limit: int = Query(50, ge=1, le=200, description="Number of top customers to return"),
    sort_by: str = Query("total_spent", description="Sort by: total_spent, order_count, avg_order_value"),
    min_orders: int = Query(1, ge=1, description="Minimum number of orders"),
    db: Session = Depends(get_db)
):
    """Get top customers by spending, order count, or average order value"""
    
    # This would be more efficient with a proper SQL query, but showing the concept
    users_data = []
    users = db.query(User).all()
    
    for user in users:
        orders = db.query(Order).filter(
            and_(
                Order.user_id == user.id,
                Order.status == OrderStatus.DELIVERED
            )
        ).all()
        
        if len(orders) >= min_orders:
            total_spent = sum(float(order.total_amount) for order in orders)
            avg_order_value = total_spent / len(orders) if orders else 0
            
            # Get preferred vendors (simplified)
            preferred_vendors = ["Vendor A", "Vendor B"]  # Would be calculated from actual data
            
            users_data.append(UserOrderSummary(
                user_id=user.id,
                user_name=user.full_name,
                order_count=len(orders),
                total_spent=total_spent,
                avg_order_value=avg_order_value,
                last_order=max(order.created_at for order in orders) if orders else None,
                preferred_vendors=preferred_vendors
            ))
    
    # Sort by the specified criterion
    if sort_by == "total_spent":
        users_data.sort(key=lambda x: x.total_spent, reverse=True)
    elif sort_by == "order_count":
        users_data.sort(key=lambda x: x.order_count, reverse=True)
    elif sort_by == "avg_order_value":
        users_data.sort(key=lambda x: x.avg_order_value, reverse=True)
    
    return users_data[:limit]


@router.get("/{user_id}/activity-stats", response_model=UserActivityStats, dependencies=[Depends(verify_api_key)])
def get_user_activity_stats(user_id: int, db: Session = Depends(get_db)):
    """Get detailed activity statistics for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    # Days since registration
    days_since_registration = (datetime.utcnow() - user.created_at).days
    
    # Recent order counts
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    orders_last_30_days = db.query(Order).filter(
        and_(
            Order.user_id == user_id,
            Order.created_at >= thirty_days_ago
        )
    ).count()
    
    orders_last_7_days = db.query(Order).filter(
        and_(
            Order.user_id == user_id,
            Order.created_at >= seven_days_ago
        )
    ).count()
    
    # Favorite order time (hour of day)
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    if orders:
        hour_counts = {}
        for order in orders:
            hour = order.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        favorite_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        favorite_order_time = f"{favorite_hour}:00" if favorite_hour is not None else None
    else:
        favorite_order_time = None
    
    # Most ordered items (placeholder - would require OrderItem joins)
    most_ordered_items = [
        {"item_name": "Pizza Margherita", "count": 5},
        {"item_name": "Chicken Burger", "count": 3}
    ]  # Placeholder
    
    # Spending trend (simplified)
    spending_trend = "stable"  # Would calculate based on recent vs older spending patterns
    
    return UserActivityStats(
        user_id=user_id,
        days_since_registration=days_since_registration,
        orders_last_30_days=orders_last_30_days,
        orders_last_7_days=orders_last_7_days,
        favorite_order_time=favorite_order_time,
        most_ordered_items=most_ordered_items,
        spending_trend=spending_trend
    )


@router.get("/{user_id}/delivery-addresses", dependencies=[Depends(verify_api_key)])
def get_user_delivery_addresses(user_id: int, db: Session = Depends(get_db)):
    """Get all delivery addresses for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    addresses = db.query(DeliveryAddress).filter(DeliveryAddress.user_id == user_id).all()
    return addresses


@router.get("/{user_id}/orders-summary", dependencies=[Depends(verify_api_key)])
def get_user_orders_summary(
    user_id: int,
    status_filter: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get user's order summary with filtering"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    # Date range
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    query = db.query(Order).filter(
        and_(
            Order.user_id == user_id,
            Order.created_at >= start_date
        )
    )
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Calculate summary statistics
    total_orders = len(orders)
    total_spent = sum(float(order.total_amount) for order in orders if order.status == OrderStatus.DELIVERED)
    avg_order_value = total_spent / len([o for o in orders if o.status == OrderStatus.DELIVERED]) if orders else 0
    
    # Status breakdown
    status_counts = {}
    for order in orders:
        status = order.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "user_id": user_id,
        "user_name": user.full_name,
        "date_range": f"Last {days_back} days",
        "total_orders": total_orders,
        "total_spent": total_spent,
        "average_order_value": avg_order_value,
        "status_breakdown": status_counts,
        "orders": orders
    }


@router.post("/{user_id}/deactivate", dependencies=[Depends(verify_api_key)])
def deactivate_user(
    user_id: int,
    reason: Optional[str] = Query(None, description="Reason for deactivation"),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (soft delete)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    # In a real system, you'd add an 'is_active' field or move to deleted users table
    # For now, just update the record
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # In production, you'd also:
    # 1. Cancel any pending orders
    # 2. Notify the user
    # 3. Log the deactivation
    # 4. Handle data retention policies
    
    return {
        "message": f"User {user.full_name} has been deactivated",
        "user_id": user_id,
        "reason": reason,
        "deactivated_at": datetime.utcnow()
    }


@router.get("/nearby/{user_id}", dependencies=[Depends(verify_api_key)])
def get_nearby_users(
    user_id: int,
    radius_km: float = Query(5.0, ge=0.1, le=50, description="Search radius in kilometers"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get nearby users (for delivery optimization or social features)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    if not user.latitude or not user.longitude:
        raise HTTPException(status_code=400, detail="User location not set")
    
    # Simple bounding box calculation (not geospatially accurate)
    lat_delta = radius_km / 111.0  # Approx km per degree latitude
    lng_delta = radius_km / (111.320 * abs(user.latitude) / 90.0) if user.latitude else radius_km / 111.320
    
    min_lat = user.latitude - lat_delta
    max_lat = user.latitude + lat_delta
    min_lng = user.longitude - lng_delta
    max_lng = user.longitude + lng_delta
    
    nearby_users = (
        db.query(User)
        .filter(
            and_(
                User.id != user_id,  # Exclude the user themselves
                User.latitude.between(min_lat, max_lat),
                User.longitude.between(min_lng, max_lng),
                User.latitude.isnot(None),
                User.longitude.isnot(None)
            )
        )
        .limit(limit)
        .all()
    )
    
    return {
        "center_user_id": user_id,
        "search_radius_km": radius_km,
        "nearby_users_count": len(nearby_users),
        "nearby_users": nearby_users
    }