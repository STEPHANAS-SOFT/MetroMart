from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateItemAddonCommand, CreateItemAddonHandler,
    UpdateItemAddonCommand, UpdateItemAddonHandler,
    DeleteItemAddonCommand, DeleteItemAddonHandler
)
from ..services.queries import (
    GetAllItemAddonQuery, GetAllItemAddonQueryHandler,
    GetItemAddonByIdQuery, GetItemAddonByIdQueryHandler,
    GetItemAddonByGroupIdQuery, GetItemAddonByGroupIdQueryHandler
)


# =================================================================================================================
#                                            ITEM ADDON ROUTES
# =================================================================================================================
item_addon_router = APIRouter(
    prefix=f"{settings.api_prefix}/item-addon", 
    tags=["Item Addon"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE ITEM ADDON
# ==========================
@item_addon_router.post("/", response_model=schemas.ItemAddonResponse)
def create_item_addon(
    addon: schemas.ItemAddonCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateItemAddonCommand(
        group_id=addon.group_id,
        name=addon.name,
        description=addon.description,
        price=addon.price,
        image_url=addon.image_url,
        is_available=addon.is_available
    )
    handler = CreateItemAddonHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ITEM ADDONS
# ==========================
@item_addon_router.get("/", response_model=List[schemas.ItemAddonResponse])
def get_all_item_addons(
    db: Session = Depends(database.get_db),
):
    query = GetAllItemAddonQuery()
    handler = GetAllItemAddonQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM ADDON BY ID
# ==========================
@item_addon_router.get("/{addon_id}", response_model=schemas.ItemAddonResponse)
def get_item_addon(
    addon_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemAddonByIdQuery(addon_id=addon_id)
    handler = GetItemAddonByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM ADDONS BY GROUP ID
# ==========================
@item_addon_router.get("/group/{group_id}", response_model=List[schemas.ItemAddonResponse])
def get_item_addons_by_group(
    group_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemAddonByGroupIdQuery(group_id=group_id)
    handler = GetItemAddonByGroupIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE ITEM ADDON BY ID
# ==========================
@item_addon_router.put("/{addon_id}", response_model=schemas.ItemAddonResponse)
def update_item_addon(
    addon_id: int,
    addon: schemas.ItemAddonUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateItemAddonCommand(
        addon_id=addon_id,
        name=addon.name,
        description=addon.description,
        price=addon.price,
        image_url=addon.image_url,
        is_available=addon.is_available
    )
    handler = UpdateItemAddonHandler(db)
    return handler.handle(command)


# ==========================
# DELETE ITEM ADDON BY ID
# ==========================
@item_addon_router.delete("/{addon_id}")
def delete_item_addon(
    addon_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteItemAddonCommand(addon_id=addon_id)
    handler = DeleteItemAddonHandler(db)
    return handler.handle(command)