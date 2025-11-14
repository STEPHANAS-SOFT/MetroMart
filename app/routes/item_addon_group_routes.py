from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateItemAddonGroupCommand, CreateItemAddonGroupHandler,
    UpdateItemAddonGroupCommand, UpdateItemAddonGroupHandler,
    DeleteItemAddonGroupCommand, DeleteItemAddonGroupHandler
)
from ..services.queries import (
    GetAllItemAddonGroupQuery, GetAllItemAddonGroupQueryHandler,
    GetItemAddonGroupByIdQuery, GetItemAddonGroupByIdQueryHandler,
    GetItemAddonGroupByVendorIdQuery, GetItemAddonGroupByVendorIdQueryHandler
)


# =================================================================================================================
#                                            ITEM ADDON GROUP ROUTES
# =================================================================================================================
item_addon_group_router = APIRouter(
    prefix=f"{settings.api_prefix}/item-addon-group", 
    tags=["Item Addon Group"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE ITEM ADDON GROUP
# ==========================
@item_addon_group_router.post("/", response_model=schemas.ItemAddonGroupResponse)
def create_item_addon_group(
    group: schemas.ItemAddonGroupCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateItemAddonGroupCommand(
        vendor_id=group.vendor_id,
        name=group.name,
        description=group.description,
        is_required=group.is_required,
        min_selections=group.min_selections,
        max_selections=group.max_selections
    )
    handler = CreateItemAddonGroupHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ITEM ADDON GROUPS
# ==========================
@item_addon_group_router.get("/", response_model=List[schemas.ItemAddonGroupResponse])
def get_all_item_addon_groups(
    db: Session = Depends(database.get_db),
):
    query = GetAllItemAddonGroupQuery()
    handler = GetAllItemAddonGroupQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM ADDON GROUP BY ID
# ==========================
@item_addon_group_router.get("/{group_id}", response_model=schemas.ItemAddonGroupResponse)
def get_item_addon_group(
    group_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemAddonGroupByIdQuery(group_id=group_id)
    handler = GetItemAddonGroupByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM ADDON GROUPS BY VENDOR ID
# ==========================
@item_addon_group_router.put("/{group_id}", response_model=schemas.ItemAddonGroupResponse)
def update_item_addon_group(
    group_id: int,
    group: schemas.ItemAddonGroupUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateItemAddonGroupCommand(
        group_id=group_id,
        name=group.name,
        description=group.description,
        is_required=group.is_required,
        min_selections=group.min_selections,
        max_selections=group.max_selections
    )
    handler = UpdateItemAddonGroupHandler(db)
    return handler.handle(command)


# ==========================
# GET ITEM ADDON GROUPS BY VENDOR ID
# ==========================
@item_addon_group_router.get("/vendor/{vendor_id}", response_model=List[schemas.ItemAddonGroupResponse])
def get_item_addon_groups_by_vendor(
    vendor_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemAddonGroupByVendorIdQuery(vendor_id=vendor_id)
    handler = GetItemAddonGroupByVendorIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# DELETE ITEM ADDON GROUP BY ID
# ==========================
@item_addon_group_router.delete("/{group_id}")
def delete_item_addon_group(
    group_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteItemAddonGroupCommand(group_id=group_id)
    handler = DeleteItemAddonGroupHandler(db)
    return handler.handle(command)