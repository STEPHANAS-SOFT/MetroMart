from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from uuid import UUID
from .. import schemas
from ..shared.api_key_route import verify_api_key
# from .schemas import schemas
from ..services.commands import (
    CreateUserCommand, CreateUserHandler,
    DeleteUserCommand, DeleteUserHandler,
    UpdateUserCommand, UpdateUserHandler,
    CreateVendorCommand, CreateVendorHandler,
    DeleteVendorCommand, DeleteVendorHandler,
    UpdateVendorCommand, UpdateVendorHandler,
    CreateItemCommand, CreateItemHandler,
    DeleteItemCommand, DeleteItemHandler,
    UpdateItemCommand, UpdateItemHandler
)
from ..services.queries import (
    GetAllUserQuery, GetAllUserQueryHandler, GetAllVendorQuery,
    GetUserByIdQuery, GetUserByIdQueryHandler,
    GetAllVendorQuery, GetAllVendorQueryHandler,
    GetVendorByIdQuery, GetVendorByIdQueryHandler,
    GetAllItemQuery, GetAllItemQueryHandler,
    GetItemByIdQuery, GetItemByIdQueryHandler,
    GetItemByNameQuery, GetItemByNameQueryHandler,
    GetItemByVendorIdQuery, GetItemByVendorIdQueryHandler,
    GetVendorByNameQuery, GetVendorByNameQueryHandler,
    GetUserByFirebaseUidQuery, GetUserByFirebaseUidQueryHandler
)


# =================================================================================================================
#                                            USERS ROUTES
# =================================================================================================================
user_router = APIRouter(
    prefix=f"{settings.api_prefix}/user", 
    tags=["User"], 
    dependencies=[Depends(verify_api_key)])


# ==========================
# CREATE USERS
# ==========================
@user_router.post("/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    command = CreateUserCommand(
        firebase_uid=user.firebase_uid,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        fcm_token=user.fcm_token,
        latitude=user.latitude,
        longitude=user.longitude 
    )
    handler = CreateUserHandler(db)
    return handler.handle(command)




# ==========================
# GET ALL USERS
# ==========================
@user_router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetAllUserQuery()
    handler = GetAllUserQueryHandler(db)
    return handler.handle(query)




# ==========================
# GET USER BY ID
# ==========================
@user_router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetUserByIdQuery(user_id=user_id)
    handler = GetUserByIdQueryHandler(db)
    return handler.handle(query)



# ==========================
# GET USER BY FIREBASE_UID
# ==========================
@user_router.get("firebase/{firebase_uid}", response_model=schemas.UserResponse)
def get_user_by_firebase_uid(
    firebase_uid: str,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetUserByFirebaseUidQuery(firebase_uid=firebase_uid)
    handler = GetUserByFirebaseUidQueryHandler(db)
    return handler.handle(query)



# ==========================
# DELETE USER BY ID
# ==========================
@user_router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteUserCommand(user_id=user_id)
    handler = DeleteUserHandler(db)
    return handler.handle(command)




# ==========================
# UPDATE USER BY ID
# ==========================
@user_router.put("/{user_id}", response_model=schemas.UserUpdate)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required([]))
):
    command = UpdateUserCommand(
        user_id=user_id,
        # firebase_uid=user.firebase_uid,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        fcm_token=user.fcm_token,
        latitude=user.latitude,
        longitude=user.longitude
    )
    handler = UpdateUserHandler(db)
    return handler.handle(command)




# =================================================================================================================
#                                            VENDOR ROUTES
# =================================================================================================================
vendor_router = APIRouter(prefix=f"{settings.api_prefix}/vendor", tags=["Vendor"], dependencies=[Depends(verify_api_key)])

# ==========================
# CREATE VENDORS
# ==========================
@vendor_router.post("/", response_model=schemas.VendorResponse)
def create_vendor(
    vendor: schemas.VendorCreate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    command = CreateVendorCommand(
        firebase_uid=vendor.firebase_uid,
        name=vendor.name,
        vendor_type=vendor.vendor_type,
        email=vendor.email,
        phone_number=vendor.phone_number,
        address=vendor.address,
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        description=vendor.description,
        logo_url=vendor.logo_url,
        has_own_delivery=vendor.has_own_delivery,
        is_active=vendor.is_active,
        fcm_token=vendor.fcm_token,
        opening_time=vendor.opening_time,
        closing_time=vendor.closing_time
    )
    handler = CreateVendorHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL VENDORS
# ==========================
@vendor_router.get("/", response_model=List[schemas.VendorResponse])
def get_all_vendors(
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetAllVendorQuery()
    handler = GetAllVendorQueryHandler(db)
    return handler.handle(query)



# ==========================
# GET VENDOR BY ID
# ==========================
@vendor_router.get("/{vendor_id}", response_model=schemas.VendorResponse)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetVendorByIdQuery(vendor_id=vendor_id)
    handler = GetVendorByIdQueryHandler(db)
    return handler.handle(query)



# ==========================
# GET VENDOR BY NAME
# ==========================
@vendor_router.get("/name/{name}", response_model=list[schemas.VendorResponse])
def get_vendor_by_name(
    name: str,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetVendorByNameQuery(name=name)
    handler = GetVendorByNameQueryHandler(db)
    return handler.handle(query)



# ==========================
# DELETE VENDOR BY ID
# ==========================
@vendor_router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(database.get_db), 
                    #  current_user=Depends(oauth2.role_required([]))
    ):
    command = DeleteVendorCommand(vendor_id=vendor_id)
    handler = DeleteVendorHandler(db)
    return handler.handle(command)




# ==========================
# UPDATE VENDOR BY ID
# ==========================
@vendor_router.put("/{vendor_id}", response_model=schemas.VendorResponse)
def update_vendor(
    vendor_id: int, 
    vendor: schemas.VendorCreate, 
    db: Session = Depends(database.get_db), 
                # current_user=Depends(oauth2.role_required([]))
):
    command = UpdateVendorCommand(vendor_id=vendor_id,
                                name=vendor.name,
                                vendor_type=vendor.vendor_type,
                                email=vendor.email,
                                phone_number=vendor.phone_number,
                                address=vendor.address,
                                latitude=vendor.latitude,
                                longitude=vendor.longitude,
                                description=vendor.description,
                                logo_url=vendor.logo_url,
                                has_own_delivery=vendor.has_own_delivery,
                                is_active=vendor.is_active,
                                rating=vendor.rating,
                                fcm_token=vendor.fcm_token,
                                opening_time=vendor.opening_time,
                                closing_time=vendor.closing_time
                                )
    
    handler = UpdateVendorHandler(db)
    return handler.handle(command)





# =================================================================================================================
#                                            ITEM ROUTES
# =================================================================================================================
item_router = APIRouter(prefix=f"{settings.api_prefix}/item", tags=["Item"], dependencies=[Depends(verify_api_key)])

# ==========================
# CREATE ITEM
# ==========================
@item_router.post("/", response_model=schemas.ItemResponse)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    command = CreateItemCommand(
        name=item.name,
        base_price=item.base_price,     
        vendor_id=item.vendor_id,
        category_id=item.category_id,
        description=item.description,
        image_url=item.image_url,
        is_available=item.is_available,
        allows_addons=item.allows_addons,
        addon_group_ids=item.addon_group_ids
    )

    handler = CreateItemHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ITEMS
# ==========================
@item_router.get("/", response_model=List[schemas.ItemResponse])
def get_all_items(
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetAllItemQuery()
    handler = GetAllItemQueryHandler(db)
    return handler.handle(query)



# ==========================
# GET ITEM BY NAME
# ==========================
@item_router.get("/name/{name}", response_model=list[schemas.ItemResponse])
def get_item_by_name(
    name: str,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetItemByNameQuery(name=name)
    handler = GetItemByNameQueryHandler(db)
    return handler.handle(query)



# ==========================
# GET ITEMS BY VENDOR ID
# ==========================
@item_router.get("/vendor/{vendor_id}", response_model=List[schemas.ItemResponse])
def get_items_by_vendor(
    vendor_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetItemByVendorIdQuery(vendor_id=vendor_id)
    handler = GetItemByVendorIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEMS BY ID
# ==========================
@item_router.get("/{item_id}", response_model=schemas.ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetItemByIdQuery(item_id=item_id)
    handler = GetItemByIdQueryHandler(db)
    return handler.handle(query)





# ==========================
# DELETE ITEMS BY ID
# ==========================
@item_router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required([]))
):
    command = DeleteItemCommand(item_id=item_id)
    handler = DeleteItemHandler(db)
    return handler.handle(command)





# ==========================
# UPDATE ITEM BY ID
# ==========================
@item_router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    item: schemas.ItemUpdate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required([]))
):
    command = UpdateItemCommand(
        item_id=item_id,
        name=item.name,
        description=item.description,
        base_price=item.base_price,
        category_id=item.category_id,
        image_url=item.image_url,
        is_available=item.is_available,
        allows_addons=item.allows_addons,
        addon_group_ids=item.addon_group_ids
    )
    handler = UpdateItemHandler(db)
    return handler.handle(command)

