from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from ...shared.database import get_db
from ...shared.api_key_route import verify_api_key
from ...models import OrderTracking, Order, Rider
from datetime import datetime

router = APIRouter(prefix="/tracking", tags=["tracking views"])


@router.get("/order/{order_id}/latest", dependencies=[Depends(verify_api_key)])
def get_latest_tracking(order_id: int, db: Session = Depends(get_db)):
    tracking = db.query(OrderTracking).filter(OrderTracking.order_id == order_id).order_by(OrderTracking.timestamp.desc()).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="No tracking found for this order")
    return tracking


@router.get("/order/{order_id}", dependencies=[Depends(verify_api_key)])
def get_tracking_history(order_id: int, db: Session = Depends(get_db)):
    records = db.query(OrderTracking).filter(OrderTracking.order_id == order_id).order_by(OrderTracking.timestamp.asc()).all()
    return records


class RiderLocationUpdate(BaseModel := object):
    pass


@router.post("/rider/{rider_id}/location", dependencies=[Depends(verify_api_key)])
def update_rider_location(rider_id: int, latitude: float, longitude: float, db: Session = Depends(get_db)):
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    rider.latitude = latitude
    rider.longitude = longitude
    rider.updated_at = datetime.utcnow()
    db.commit()
    return {"msg": "Location updated"}
