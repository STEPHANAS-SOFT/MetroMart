from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...models import Rider, Order, OrderStatus

router = APIRouter(prefix="/riders", tags=["rider views"])


@router.get("/{rider_id}/available-orders", dependencies=[Depends(verify_api_key)])
def get_available_orders(rider_id: int, db: Session = Depends(get_db)):
    # Very simple: orders ready for pickup and not assigned to a rider
    orders = db.query(Order).filter(Order.status == OrderStatus.READY_FOR_PICKUP).all()
    return orders


@router.post("/{rider_id}/accept/{order_id}", dependencies=[Depends(verify_api_key)])
def accept_delivery_order(rider_id: int, order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # check it's available
    if order.status != OrderStatus.READY_FOR_PICKUP:
        raise HTTPException(status_code=400, detail="Order not available for pickup")
    order.rider_id = rider_id
    order.status = OrderStatus.IN_TRANSIT
    db.commit()
    return {"msg": "Order assigned to rider", "order_id": order_id}


@router.get("/{rider_id}/current-deliveries", dependencies=[Depends(verify_api_key)])
def get_current_deliveries(rider_id: int, db: Session = Depends(get_db)):
    deliveries = db.query(Order).filter(Order.rider_id == rider_id, Order.status == OrderStatus.IN_TRANSIT).all()
    return deliveries


@router.post("/{rider_id}/complete/{order_id}", dependencies=[Depends(verify_api_key)])
def complete_delivery(rider_id: int, order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.rider_id == rider_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not assigned to this rider")
    order.status = OrderStatus.DELIVERED
    db.commit()
    return {"msg": "Delivery completed", "order_id": order_id}


@router.get("/{rider_id}/earnings", dependencies=[Depends(verify_api_key)])
def get_rider_earnings(rider_id: int, db: Session = Depends(get_db)):
    # Simple placeholder: No earnings model exists; return wallet if any
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    # If RiderWallet exists, would return balance; otherwise placeholder
    return {"rider_id": rider_id, "earnings": 0.0}


@router.post("/{rider_id}/toggle-availability", dependencies=[Depends(verify_api_key)])
def toggle_rider_availability(rider_id: int, is_available: bool, db: Session = Depends(get_db)):
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    rider.status = 'available' if is_available else 'offline'
    db.commit()
    return {"msg": "Rider availability updated", "is_available": is_available}
