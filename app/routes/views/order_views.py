from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...models import Item, ItemVariation, Order, OrderItem, OrderStatus
from decimal import Decimal

router = APIRouter(prefix="/orders", tags=["order views"])


class OrderLine(BaseModel):
    item_id: int
    variation_id: Optional[int] = None
    quantity: int = 1


class CalculateTotalRequest(BaseModel):
    lines: List[OrderLine]
    delivery_fee: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    discount: Optional[float] = 0.0


class CalculateTotalResponse(BaseModel):
    subtotal: float
    tax: float
    delivery_fee: float
    discount: float
    total: float


@router.post("/calculate-total", response_model=CalculateTotalResponse, dependencies=[Depends(verify_api_key)])
def calculate_order_total(request: CalculateTotalRequest, db: Session = Depends(get_db)):
    """Calculate subtotal, tax, delivery fee and total for an order client-side helper"""
    subtotal = Decimal('0')
    for line in request.lines:
        item = db.query(Item).filter(Item.id == line.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {line.item_id} not found")
        price = Decimal(str(item.price))
        # Optionally handle variation price
        if line.variation_id:
            variation = db.query(ItemVariation).filter(ItemVariation.id == line.variation_id).first()
            if variation and getattr(variation, 'price', None) is not None:
                price = Decimal(str(variation.price))
        subtotal += price * line.quantity

    tax = (subtotal * Decimal(str(request.tax_percent or 0))) / Decimal('100')
    delivery_fee = Decimal(str(request.delivery_fee or 0))
    discount = Decimal(str(request.discount or 0))
    total = subtotal + tax + delivery_fee - discount

    return CalculateTotalResponse(
        subtotal=float(subtotal),
        tax=float(tax),
        delivery_fee=float(delivery_fee),
        discount=float(discount),
        total=float(total)
    )


@router.post("/{order_id}/cancel", dependencies=[Depends(verify_api_key)])
def cancel_order(order_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Allow cancellation only in certain states
    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled at this stage")
    order.status = OrderStatus.CANCELLED
    db.commit()
    # TODO: enqueue refund and notifications
    return {"msg": "Order cancelled", "order_id": order_id}


@router.get("/user/{user_id}/history", dependencies=[Depends(verify_api_key)])
def get_user_order_history(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    return orders


@router.post("/{order_id}/rate", dependencies=[Depends(verify_api_key)])
def rate_order(order_id: int, rating: int = 5, comment: Optional[str] = None):
    # Placeholder: ratings/reviews model not implemented in current schema
    return {"msg": "Thank you for your rating", "order_id": order_id, "rating": rating}
