from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from ...shared.api_key_route import verify_api_key
from ...shared.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/promotions", tags=["promotion views"])


class Coupon(BaseModel):
    code: str
    discount_percent: Optional[float] = None
    amount_off: Optional[float] = None


@router.get("/active", dependencies=[Depends(verify_api_key)])
def get_active_promotions():
    # Placeholder: return static set
    return [{"code": "WELCOME10", "discount_percent": 10}]


@router.post("/validate", dependencies=[Depends(verify_api_key)])
def validate_coupon(code: str):
    # Placeholder validation
    if code.upper() == "WELCOME10":
        return {"valid": True, "discount_percent": 10}
    return {"valid": False}


@router.get("/user/{user_id}", dependencies=[Depends(verify_api_key)])
def get_user_coupons(user_id: int):
    # Placeholder
    return {"user_id": user_id, "coupons": []}


@router.post("/loyalty/earn", dependencies=[Depends(verify_api_key)])
def earn_loyalty_points(user_id: int, points: int):
    # Placeholder
    return {"user_id": user_id, "earned": points}
