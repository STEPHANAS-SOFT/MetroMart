from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from ...shared.api_key_route import verify_api_key

router = APIRouter(prefix="/notifications", tags=["notification views"])


class PushNotification(BaseModel):
    title: str
    body: str
    user_id: Optional[int] = None


@router.post("/push", dependencies=[Depends(verify_api_key)])
def send_push(notification: PushNotification):
    # Placeholder: integrate with FCM or another push provider
    return {"sent": True, "title": notification.title}


@router.get("/user/{user_id}", dependencies=[Depends(verify_api_key)])
def get_user_notifications(user_id: int):
    # Placeholder
    return {"user_id": user_id, "notifications": []}


@router.post("/support/chat/start", dependencies=[Depends(verify_api_key)])
def start_support_chat(user_id: int):
    # Placeholder for chat creation
    return {"chat_id": f"chat_{user_id}", "started": True}


@router.get("/orders/{order_id}/chat-history", dependencies=[Depends(verify_api_key)])
def get_order_chat_history(order_id: int):
    return {"order_id": order_id, "messages": []}
