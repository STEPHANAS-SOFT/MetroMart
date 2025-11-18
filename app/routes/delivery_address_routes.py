from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateDeliveryAddressCommand, CreateDeliveryAddressHandler,
    UpdateDeliveryAddressCommand, UpdateDeliveryAddressHandler,
    DeleteDeliveryAddressCommand, DeleteDeliveryAddressHandler
)
from ..services.queries import (
    GetAllDeliveryAddressQuery, GetAllDeliveryAddressQueryHandler,
    GetDeliveryAddressByIdQuery, GetDeliveryAddressByIdQueryHandler,
    GetDeliveryAddressByUserIdQuery, GetDeliveryAddressByUserIdQueryHandler,
    GetUserByIdQuery, GetUserByIdQueryHandler
)


# =================================================================================================================
#                                            DELIVERY ADDRESS ROUTES
# =================================================================================================================
delivery_address_router = APIRouter(
    prefix=f"{settings.api_prefix}/delivery-address", 
    tags=["Delivery Address"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE DELIVERY ADDRESS
# ==========================
@delivery_address_router.post("/", response_model=schemas.DeliveryAddressResponse)
def create_delivery_address(
    address: schemas.DeliveryAddressCreate,
    db: Session = Depends(database.get_db),
):
    # Validate user_id
    try:
        user_query = GetUserByIdQuery(user_id=address.user_id)
        user_handler = GetUserByIdQueryHandler(db)
        user_handler.handle(user_query)
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Invalid user_id: User does not exist.")

    command = CreateDeliveryAddressCommand(
        user_id=address.user_id,
        address=address.address,
        latitude=address.latitude,
        longitude=address.longitude,
        is_default=address.is_default,
        name=address.name 
    )
    handler = CreateDeliveryAddressHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL DELIVERY ADDRESSES
# ==========================
@delivery_address_router.get("/", response_model=List[schemas.DeliveryAddressResponse])
def get_all_delivery_addresses(
    db: Session = Depends(database.get_db),
):
    query = GetAllDeliveryAddressQuery()
    handler = GetAllDeliveryAddressQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET DELIVERY ADDRESS BY ID
# ==========================
@delivery_address_router.get("/{address_id}", response_model=schemas.DeliveryAddressResponse)
def get_delivery_address(
    address_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetDeliveryAddressByIdQuery(address_id=address_id)
    handler = GetDeliveryAddressByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET DELIVERY ADDRESSES BY USER ID
# ==========================
@delivery_address_router.get("/user/{user_id}", response_model=List[schemas.DeliveryAddressResponse])
def get_delivery_addresses_by_user(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetDeliveryAddressByUserIdQuery(user_id=user_id)
    handler = GetDeliveryAddressByUserIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE DELIVERY ADDRESS BY ID
# ==========================
@delivery_address_router.put("/{address_id}", response_model=schemas.DeliveryAddressResponse)
def update_delivery_address(
    address_id: int,
    address: schemas.DeliveryAddressUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateDeliveryAddressCommand(
        address_id=address_id,
        address=address.address,
        latitude=address.latitude,
        longitude=address.longitude,
        is_default=address.is_default,
        name=address.name 
    )
    handler = UpdateDeliveryAddressHandler(db)
    return handler.handle(command)


# ==========================
# DELETE DELIVERY ADDRESS BY ID
# ==========================
@delivery_address_router.delete("/{address_id}")
def delete_delivery_address(
    address_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteDeliveryAddressCommand(address_id=address_id)
    handler = DeleteDeliveryAddressHandler(db)
    return handler.handle(command)