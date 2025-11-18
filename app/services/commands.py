from fastapi import HTTPException, status
from datetime import datetime
from pydantic import EmailStr, HttpUrl
from sqlalchemy.orm import Session
from ..models import (
    User, Vendor, VendorType, Item, ItemCategory, DeliveryAddress, 
    Rider, RiderStatus, Order, OrderStatus, ItemAddonGroup, ItemAddon, 
    ItemVariation, OrderItem, OrderItemAddon, OrderTracking, 
    Cart, CartItem, CartItemAddon, UserWallet, VendorWallet, 
    RiderWallet, WalletTransaction, WalletTransactionType, WalletTransactionStatus
)
from ..utils.errors import ErrorHandler, ErrorMessages
from dataclasses import dataclass
from typing import Optional, List
from ..schemas import ItemBase
from ..models import order_items_association


# =============================================================================================================
# USER COMMANDS
# =============================================================================================================

# ==================
# CREATE USERS
# ==================
@dataclass
class CreateUserCommand:
    firebase_uid: str
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 


class CreateUserHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateUserCommand):
        # Validate required fields
        if not command.firebase_uid or not command.firebase_uid.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Firebase UID is required and cannot be empty"
            )
        
        if not command.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email address is required"
            )
            
        if not command.full_name or not command.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Full name is required and cannot be empty"
            )
        
        # Check if user already exists by email
        existing_user = self.db.query(User).filter(User.email == command.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"A user account with email '{command.email}' already exists. Please use a different email address or try signing in instead."
            )
        
        # Check if user already exists by firebase_uid
        existing_firebase_user = self.db.query(User).filter(User.firebase_uid == command.firebase_uid).first()
        if existing_firebase_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="This Firebase account is already linked to another user profile. Please contact support if you believe this is an error."
            )

        try:
            # create user
            user = User(
                firebase_uid=command.firebase_uid,
                email=command.email,
                phone_number=command.phone_number,
                full_name=command.full_name,
                fcm_token=command.fcm_token,
                latitude=command.latitude,  
                longitude=command.longitude,
            )
            self.db.add(user)
            self.db.commit() 
            self.db.refresh(user)
            
            # Automatically create user wallet
            create_user_wallet(self.db, user.id)
            
            return user
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"We encountered an error while creating your account. Please try again. If the problem persists, contact support. Error: {str(e)}"
            )
    


# ==========================
# UPDATE USER BY ID
# ==========================
@dataclass(frozen=True)
class UpdateUserCommand:
    user_id: int
    # firebase_uid: str
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 

class UpdateUserHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateUserCommand):
        # Validate user ID
        if command.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid user ID. User ID must be a positive number."
            )
        
        user_query = self.db.query(User).filter(User.id == command.user_id)
        user = user_query.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"User with ID {command.user_id} not found. Please verify the user ID and try again."
            )

        # Validate required fields
        if not command.full_name or not command.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Full name is required and cannot be empty"
            )

        try:
            user_query.update({
                # User.firebase_uid: command.firebase_uid,
                User.email: command.email,
                User.phone_number: command.phone_number,
                User.full_name: command.full_name,
                User.fcm_token: command.fcm_token,
                User.latitude: command.latitude,
                User.longitude: command.longitude,
            })
            
            self.db.commit()
            return user_query.first()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to update user profile. Please try again. Error: {str(e)}"
            )





# =======================
# DELETE USER BY ID
# =======================
@dataclass(frozen=True)
class DeleteUserCommand:
    user_id: int

class DeleteUserHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteUserCommand):
        # Validate user ID
        if command.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid user ID. User ID must be a positive number."
            )
        
        user = self.db.query(User).filter(User.id == command.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"User with ID {command.user_id} not found. The user may have already been deleted or the ID is incorrect."
            )

        try:
            self.db.delete(user)
            self.db.commit()
            return {"message": f"User account for '{user.full_name}' (ID: {command.user_id}) has been successfully deleted."}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to delete user account. Please try again. Error: {str(e)}"
            )


# =============================================================================================================
# VENDOR COMMANDS
# =============================================================================================================

# ======================
# CREATE VENDORS
# ======================
@dataclass
class CreateVendorCommand:
    firebase_uid: str
    name: str
    vendor_type: VendorType  
    email: EmailStr
    phone_number: str
    address: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = False
    is_active: Optional[bool] = True
    rating: Optional[float] = 0.0
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    items: Optional[List[dict]] = None 

class CreateVendorHandler:
        def __init__(self, db: Session):
            self.db = db

        def handle(self, command: CreateVendorCommand):
            # Validate required fields
            if not command.firebase_uid or not command.firebase_uid.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Firebase UID is required and cannot be empty"
                )
            
            if not command.name or not command.name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Vendor name is required and cannot be empty"
                )
            
            if not command.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Email address is required for vendor registration"
                )
            
            if not command.address or not command.address.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Business address is required"
                )
            
            # Validate coordinates
            if not isinstance(command.latitude, (int, float)) or not isinstance(command.longitude, (int, float)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Valid latitude and longitude coordinates are required for business location"
                )
            
            # Check if vendor already exists by email
            existing_vendor = self.db.query(Vendor).filter(Vendor.email == command.email).first()
            if existing_vendor:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"A vendor account with email '{command.email}' already exists. Please use a different email address or try signing in instead."
                )
            
            # Check if vendor already exists by firebase_uid
            existing_firebase_vendor = self.db.query(Vendor).filter(Vendor.firebase_uid == command.firebase_uid).first()
            if existing_firebase_vendor:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="This Firebase account is already linked to another vendor profile. Please contact support if you believe this is an error."
                )

            # Ensure vendor_type is Enum instance
            if isinstance(command.vendor_type, str):
                try:
                    command.vendor_type = VendorType(command.vendor_type.lower())
                except ValueError:
                    valid_types = [v.value for v in VendorType]
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid vendor type '{command.vendor_type}'. Please choose from: {', '.join(valid_types)}"
                    )

            try:            
                # create vendor
                vendor = Vendor(
                    firebase_uid=command.firebase_uid,
                    name=command.name,
                    vendor_type=command.vendor_type,
                    description=command.description,
                    email=command.email,
                    phone_number=command.phone_number,
                    address=command.address,
                    latitude=command.latitude,
                    longitude=command.longitude,
                    logo_url=command.logo_url,
                    has_own_delivery=command.has_own_delivery,
                    is_active=command.is_active,
                    rating=command.rating,
                    fcm_token=command.fcm_token,
                    opening_time=command.opening_time,
                    closing_time=command.closing_time,
                )
                self.db.add(vendor)
                self.db.commit() 
                self.db.refresh(vendor)
                
                # Automatically create vendor wallet
                create_vendor_wallet(self.db, vendor.id)
                
                return vendor
            except Exception as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail=f"We encountered an error while registering your business. Please try again. If the problem persists, contact support. Error: {str(e)}"
                )
        




# ==========================
# UPDATE VENDOR BY ID
# ==========================
@dataclass(frozen=True)
class UpdateVendorCommand:
    vendor_id: int
    name: str
    vendor_type: VendorType
    email: EmailStr
    phone_number: str
    address: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = False
    is_active: Optional[bool] = True
    rating: Optional[float] = 0.0
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class UpdateVendorHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateVendorCommand):
        vendor_query = self.db.query(Vendor).filter(Vendor.id == command.vendor_id)
        vendor = vendor_query.first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor with ID: {command.vendor_id} not found")

        vendor_query.update({
            Vendor.name: command.name,
            Vendor.vendor_type: command.vendor_type,
            Vendor.email: command.email,
            Vendor.phone_number: command.phone_number,
            Vendor.address: command.address,
            Vendor.latitude: command.latitude,
            Vendor.longitude: command.longitude,
            Vendor.description: command.description,
            Vendor.logo_url: command.logo_url,
            Vendor.has_own_delivery: command.has_own_delivery,
            Vendor.is_active: command.is_active,
            Vendor.rating: command.rating,
            Vendor.fcm_token: command.fcm_token,
            Vendor.opening_time: command.opening_time,
            Vendor.closing_time: command.closing_time,
        })
        self.db.commit()
        return vendor_query.first()
    




# =======================
# DELETE VENDOR BY ID
# =======================
@dataclass(frozen=True)
class DeleteVendorCommand:
    vendor_id: int

class DeleteVendorHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteVendorCommand):
        vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor with ID: {command.vendor_id} not found")

        self.db.delete(vendor)
        self.db.commit()
        return {"msg": f"Vendor with id: {command.vendor_id} deleted successfully"}
    






# =============================================================================================================
# ITEM COMMANDS
# =============================================================================================================

# ======================
# CREATE ITEMS
# ======================
@dataclass
class CreateItemCommand:
    name: str
    base_price: float
    vendor_id: int
    category_id: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = True
    allows_addons: Optional[bool] = False
    addon_group_ids: Optional[List[int]] = None

# class OrderItemCommand(BaseModel):
#     item_id: int
#     quantity: int
#     unit_price: float

# class CreateOrderCommand:
#     user_id: int
#     vendor_id: int
#     status: str
#     subtotal: float
#     delivery_fee: float
#     total: float
#     items: List[ItemBase]
#     rider_id: int | None = None
#     delivery_address_id: int | None = None
#     notes: str | None = None
#     estimated_delivery_time: str | None = None
    

class CreateItemHandler:
        def __init__(self, db: Session):
            self.db = db

        def handle(self, command):
            # Validate required fields
            if not command.name or not command.name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Item name is required and cannot be empty"
                )

            if command.base_price is None or command.base_price < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Base price is required and must be a positive number"
                )

            if command.vendor_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Valid vendor ID is required"
                )

            if command.category_id and command.category_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid category ID. Category ID must be a positive number"
                )

            # Verify vendor exists
            vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Vendor with ID {command.vendor_id} not found. Please verify the vendor exists."
                )

            # Verify category exists if provided
            if command.category_id:
                category = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id).first()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail=f"Category with ID {command.category_id} not found. Please select a valid category."
                    )

            # Verify addon groups exist and belong to vendor if provided
            addon_group_ids = []
            if command.addon_group_ids:
                for group_id in command.addon_group_ids:
                    addon_group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == group_id).first()
                    if not addon_group:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Addon group with ID {group_id} not found. Please select a valid addon group."
                        )
                    if addon_group.vendor_id != command.vendor_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Addon group with ID {group_id} does not belong to vendor with ID {command.vendor_id}."
                        )
                    addon_group_ids.append(group_id)

            try:
                # Create item with addon_group_ids as array
                item = Item(
                    name=command.name,
                    base_price=command.base_price,
                    description=command.description,
                    image_url=command.image_url,
                    is_available=command.is_available,
                    allows_addons=command.allows_addons,
                    category_id=command.category_id,
                    vendor_id=command.vendor_id,
                    addon_group_ids=addon_group_ids  # <-- assign the array here
                )

                self.db.add(item)
                self.db.commit()
                self.db.refresh(item)
                return item
            except Exception as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create menu item. Please try again. Error: {str(e)}"
                )



# class CreateItemHandler:
#         def __init__(self, db: Session):
#             self.db = db

#         def handle(self, command: CreateItemCommand):
#             # Validate required fields
#             if not command.name or not command.name.strip():
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST, 
#                     detail="Item name is required and cannot be empty"
#                 )
            
#             if command.base_price is None or command.base_price < 0:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST, 
#                     detail="Base price is required and must be a positive number"
#                 )
            
#             if command.vendor_id <= 0:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST, 
#                     detail="Valid vendor ID is required"
#                 )
            
#             if command.category_id and command.category_id <= 0:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST, 
#                     detail="Invalid category ID. Category ID must be a positive number"
#                 )
            
#             # Verify vendor exists
#             vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
#             if not vendor:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND, 
#                     detail=f"Vendor with ID {command.vendor_id} not found. Please verify the vendor exists."
#                 )
            
#             # Verify category exists if provided
#             if command.category_id:
#                 category = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id).first()
#                 if not category:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND, 
#                         detail=f"Category with ID {command.category_id} not found. Please select a valid category."
#                     )
            
#             # Verify addon groups exist and belong to vendor if provided
#             addon_groups = []
#             if command.addon_group_ids:
#                 for addon_group_id in command.addon_group_ids:
#                     addon_group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == addon_group_id).first()
#                     if not addon_group:
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND, 
#                             detail=f"Addon group with ID {addon_group_id} not found. Please select a valid addon group."
#                         )
#                     if addon_group.vendor_id != command.vendor_id:
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST, 
#                             detail=f"Addon group with ID {addon_group_id} does not belong to vendor with ID {command.vendor_id}."
#                         )
#                     addon_groups.append(addon_group)

#             try:
#                 # create item
#                 item = Item(
#                     name=command.name,
#                     base_price=command.base_price,
#                     description=command.description,
#                     image_url=command.image_url,
#                     is_available=command.is_available,
#                     allows_addons=command.allows_addons,
#                     category_id=command.category_id,
#                     vendor_id=command.vendor_id,
#                 )
                
#                 # Add addon groups to the item
#                 if addon_groups:
#                     item.addon_groups = addon_groups

#                 self.db.add(item)
#                 self.db.commit()
#                 self.db.refresh(item)
#                 return item
#             except Exception as e:
#                 self.db.rollback()
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
#                     detail=f"Failed to create menu item. Please try again. Error: {str(e)}"
#                 )





# ==========================
# UPDATE ITEM BY ID
# ==========================
@dataclass(frozen=True)
class UpdateItemCommand:
    item_id: int
    name: Optional[str] = None
    base_price: Optional[float] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    allows_addons: Optional[bool] = None
    addon_group_ids: Optional[List[int]] = None


class UpdateItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemCommand):
        item_query = self.db.query(Item).filter(Item.id == command.item_id)
        item = item_query.first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Item with ID: {command.item_id} not found"
            )

        # Verify category if being updated
        if command.category_id is not None and command.category_id > 0:
            category = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Category with ID {command.category_id} not found."
                )

        # Verify addon groups if provided
        addon_group_ids = []
        if command.addon_group_ids is not None:
            for addon_group_id in command.addon_group_ids:
                addon_group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == addon_group_id).first()
                if not addon_group:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail=f"Addon group with ID {addon_group_id} not found."
                    )
                if addon_group.vendor_id != item.vendor_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail=f"Addon group with ID {addon_group_id} does not belong to the same vendor as the item."
                    )
                addon_group_ids.append(addon_group_id)

        # Prepare update data
        update_data = {}
        if command.name is not None:
            update_data[Item.name] = command.name
        if command.base_price is not None:
            update_data[Item.base_price] = command.base_price
        if command.category_id is not None:
            update_data[Item.category_id] = command.category_id
        if command.description is not None:
            update_data[Item.description] = command.description
        if command.image_url is not None:
            update_data[Item.image_url] = command.image_url
        if command.is_available is not None:
            update_data[Item.is_available] = command.is_available
        if command.allows_addons is not None:
            update_data[Item.allows_addons] = command.allows_addons
        if command.addon_group_ids is not None:
            update_data[Item.addon_group_ids] = addon_group_ids  # <-- set ARRAY field directly

        # Perform the update
        item_query.update(update_data)
        self.db.commit()
        self.db.refresh(item)
        return item


# class UpdateItemHandler:
#     def __init__(self, db: Session):
#         self.db = db

#     def handle(self, command: UpdateItemCommand):
#         item_query = self.db.query(Item).filter(Item.id == command.item_id)
#         item = item_query.first()
#         if not item:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID: {command.item_id} not found")

#         # Verify addon group exists and belongs to same vendor if being updated
#         if command.addon_group_id is not None:
#             if command.category_id and command.category_id > 0:
#                 category = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id).first()
#                 if not category:
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND, 
#                         detail=f"Category with ID {command.category_id} not found."
#                     )
            
#             # Verify addon groups if provided
#             addon_groups = []
#             if command.addon_group_ids is not None:
#                 for addon_group_id in command.addon_group_ids:
#                     addon_group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == addon_group_id).first()
#                     if not addon_group:
#                         raise HTTPException(
#                             status_code=status.HTTP_404_NOT_FOUND, 
#                             detail=f"Addon group with ID {addon_group_id} not found."
#                         )
#                     if addon_group.vendor_id != item.vendor_id:
#                         raise HTTPException(
#                             status_code=status.HTTP_400_BAD_REQUEST, 
#                             detail=f"Addon group with ID {addon_group_id} does not belong to the same vendor as the item."
#                         )
#                     addon_groups.append(addon_group)

#         update_data = {}
#         if command.name is not None:
#             update_data[Item.name] = command.name
#         if command.base_price is not None:
#             update_data[Item.base_price] = command.base_price
#         if command.category_id is not None:
#             update_data[Item.category_id] = command.category_id
#         if command.description is not None:
#             update_data[Item.description] = command.description
#         if command.image_url is not None:
#             update_data[Item.image_url] = command.image_url
#         if command.is_available is not None:
#             update_data[Item.is_available] = command.is_available
#         if command.allows_addons is not None:
#             update_data[Item.allows_addons] = command.allows_addons
        
#         # Update addon groups if provided
#         if command.addon_group_ids is not None:
#             item.addon_groups = addon_groups
        
#         item_query.update(update_data)
#         self.db.commit()
#         self.db.refresh(item)
#         return item





# =======================
# DELETE ITEM BY ID
# =======================
@dataclass(frozen=True)
class DeleteItemCommand:
    item_id: int

class DeleteItemHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteItemCommand):
        item = self.db.query(Item).filter(Item.id == command.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID: {command.item_id} not found")

        self.db.delete(item)
        self.db.commit()
        return {"msg": f"Item with id: {command.item_id} deleted successfully"}


# =============================================================================================================
# ITEM CATEGORY COMMANDS
# =============================================================================================================

@dataclass
class CreateItemCategoryCommand:
    # vendor_id: int
    name: str
    description: Optional[str] = None

class CreateItemCategoryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateItemCategoryCommand):
        # Verify vendor exists
        # vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
        # if not vendor:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND, 
        #         detail=f"Vendor with ID {command.vendor_id} not found. Please verify the vendor exists."
        #     )
        
        category = ItemCategory(
            # vendor_id=command.vendor_id,
            name=command.name,
            description=command.description
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

@dataclass(frozen=True)
class UpdateItemCategoryCommand:
    category_id: int
    name: Optional[str] = None
    description: Optional[str] = None

class UpdateItemCategoryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemCategoryCommand):
        category_query = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id)
        category = category_query.first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID: {command.category_id} not found")

        update_data = {}
        if command.name is not None:
            update_data[ItemCategory.name] = command.name
        if command.description is not None:
            update_data[ItemCategory.description] = command.description
        
        category_query.update(update_data)
        self.db.commit()
        return category_query.first()

@dataclass(frozen=True)
class DeleteItemCategoryCommand:
    category_id: int

class DeleteItemCategoryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteItemCategoryCommand):
        category = self.db.query(ItemCategory).filter(ItemCategory.id == command.category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID: {command.category_id} not found")

        self.db.delete(category)
        self.db.commit()
        return {"msg": f"Category with id: {command.category_id} deleted successfully"}


# =============================================================================================================
# DELIVERY ADDRESS COMMANDS
# =============================================================================================================

@dataclass
class CreateDeliveryAddressCommand:
    user_id: int
    address: str
    latitude: float
    longitude: float
    is_default: Optional[bool] = False
    name: Optional[str] = None

class CreateDeliveryAddressHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateDeliveryAddressCommand):
        delivery_address = DeliveryAddress(
            user_id=command.user_id,
            address=command.address,
            latitude=command.latitude,
            longitude=command.longitude,
            is_default=command.is_default,
            name=command.name
        )
        self.db.add(delivery_address)
        self.db.commit()
        self.db.refresh(delivery_address)
        return delivery_address

@dataclass(frozen=True)
class UpdateDeliveryAddressCommand:
    address_id: int
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[bool] = None
    name: Optional[str] = None

class UpdateDeliveryAddressHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateDeliveryAddressCommand):
        address_query = self.db.query(DeliveryAddress).filter(DeliveryAddress.id == command.address_id)
        address = address_query.first()
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID: {command.address_id} not found")

        update_data = {}
        if command.address is not None:
            update_data[DeliveryAddress.address] = command.address
        if command.latitude is not None:
            update_data[DeliveryAddress.latitude] = command.latitude
        if command.longitude is not None:
            update_data[DeliveryAddress.longitude] = command.longitude
        if command.is_default is not None:
            update_data[DeliveryAddress.is_default] = command.is_default
        if command.name is not None:
            update_data[DeliveryAddress.name] = command.name
        
        address_query.update(update_data)
        self.db.commit()
        return address_query.first()

@dataclass(frozen=True)
class DeleteDeliveryAddressCommand:
    address_id: int

class DeleteDeliveryAddressHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteDeliveryAddressCommand):
        address = self.db.query(DeliveryAddress).filter(DeliveryAddress.id == command.address_id).first()
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID: {command.address_id} not found")

        self.db.delete(address)
        self.db.commit()
        return {"msg": f"Address with id: {command.address_id} deleted successfully"}


# =============================================================================================================
# RIDER COMMANDS
# =============================================================================================================

@dataclass
class CreateRiderCommand:
    firebase_uid: str
    full_name: str
    email: EmailStr
    phone_number: str
    vehicle_type: str
    vehicle_number: str
    license_number: str
    is_verified: Optional[bool] = False
    is_active: Optional[bool] = True
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    fcm_token: Optional[str] = None
    status: Optional[RiderStatus] = RiderStatus.OFFLINE

class CreateRiderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateRiderCommand):
        rider = Rider(
            firebase_uid=command.firebase_uid,
            full_name=command.full_name,
            email=command.email,
            phone_number=command.phone_number,
            vehicle_type=command.vehicle_type,
            vehicle_number=command.vehicle_number,
            license_number=command.license_number,
            is_verified=command.is_verified,
            is_active=command.is_active,
            current_latitude=command.current_latitude,
            current_longitude=command.current_longitude,
            fcm_token=command.fcm_token,
            status=command.status
        )
        self.db.add(rider)
        self.db.commit()
        self.db.refresh(rider)
        
        # Automatically create rider wallet
        create_rider_wallet(self.db, rider.id)
        
        return rider

@dataclass(frozen=True)
class UpdateRiderCommand:
    rider_id: int
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    license_number: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    fcm_token: Optional[str] = None
    status: Optional[RiderStatus] = None

class UpdateRiderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateRiderCommand):
        rider_query = self.db.query(Rider).filter(Rider.id == command.rider_id)
        rider = rider_query.first()
        if not rider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rider with ID: {command.rider_id} not found")

        update_data = {}
        if command.full_name is not None:
            update_data[Rider.full_name] = command.full_name
        if command.email is not None:
            update_data[Rider.email] = command.email
        if command.phone_number is not None:
            update_data[Rider.phone_number] = command.phone_number
        if command.vehicle_type is not None:
            update_data[Rider.vehicle_type] = command.vehicle_type
        if command.vehicle_number is not None:
            update_data[Rider.vehicle_number] = command.vehicle_number
        if command.license_number is not None:
            update_data[Rider.license_number] = command.license_number
        if command.is_verified is not None:
            update_data[Rider.is_verified] = command.is_verified
        if command.is_active is not None:
            update_data[Rider.is_active] = command.is_active
        if command.current_latitude is not None:
            update_data[Rider.current_latitude] = command.current_latitude
        if command.current_longitude is not None:
            update_data[Rider.current_longitude] = command.current_longitude
        if command.fcm_token is not None:
            update_data[Rider.fcm_token] = command.fcm_token
        if command.status is not None:
            update_data[Rider.status] = command.status
        
        rider_query.update(update_data)
        self.db.commit()
        return rider_query.first()

@dataclass(frozen=True)
class DeleteRiderCommand:
    rider_id: int

class DeleteRiderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteRiderCommand):
        rider = self.db.query(Rider).filter(Rider.id == command.rider_id).first()
        if not rider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rider with ID: {command.rider_id} not found")

        self.db.delete(rider)
        self.db.commit()
        return {"msg": f"Rider with id: {command.rider_id} deleted successfully"}


# =============================================================================================================
# ITEM ADDON GROUP COMMANDS
# =============================================================================================================

@dataclass
class CreateItemAddonGroupCommand:
    vendor_id: int
    name: str
    description: Optional[str] = None
    is_required: Optional[bool] = False
    min_selections: Optional[int] = 0
    max_selections: Optional[int] = 1

class CreateItemAddonGroupHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateItemAddonGroupCommand):
        # Verify vendor exists
        vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Vendor with ID {command.vendor_id} not found. Please verify the vendor exists."
            )
        
        addon_group = ItemAddonGroup(
            vendor_id=command.vendor_id,
            name=command.name,
            description=command.description,
            is_required=command.is_required,
            min_selections=command.min_selections,
            max_selections=command.max_selections
        )
        self.db.add(addon_group)
        self.db.commit()
        self.db.refresh(addon_group)
        return addon_group

@dataclass(frozen=True)
class UpdateItemAddonGroupCommand:
    group_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    min_selections: Optional[int] = None
    max_selections: Optional[int] = None

class UpdateItemAddonGroupHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemAddonGroupCommand):
        group_query = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == command.group_id)
        group = group_query.first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon group with ID: {command.group_id} not found")

        update_data = {}
        if command.name is not None:
            update_data[ItemAddonGroup.name] = command.name
        if command.description is not None:
            update_data[ItemAddonGroup.description] = command.description
        if command.is_required is not None:
            update_data[ItemAddonGroup.is_required] = command.is_required
        if command.min_selections is not None:
            update_data[ItemAddonGroup.min_selections] = command.min_selections
        if command.max_selections is not None:
            update_data[ItemAddonGroup.max_selections] = command.max_selections
        
        group_query.update(update_data)
        self.db.commit()
        return group_query.first()

@dataclass(frozen=True)
class DeleteItemAddonGroupCommand:
    group_id: int

class DeleteItemAddonGroupHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteItemAddonGroupCommand):
        group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == command.group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon group with ID: {command.group_id} not found")

        self.db.delete(group)
        self.db.commit()
        return {"msg": f"Addon group with id: {command.group_id} deleted successfully"}


# =============================================================================================================
# ITEM ADDON COMMANDS
# =============================================================================================================

@dataclass
class CreateItemAddonCommand:
    group_id: int
    name: str
    price: float
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_available: Optional[bool] = True

class CreateItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateItemAddonCommand):
        addon = ItemAddon(
            group_id=command.group_id,
            name=command.name,
            description=command.description,
            price=command.price,
            image_url=command.image_url,
            is_available=command.is_available
        )
        self.db.add(addon)
        self.db.commit()
        self.db.refresh(addon)
        return addon

@dataclass(frozen=True)
class UpdateItemAddonCommand:
    addon_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class UpdateItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemAddonCommand):
        addon_query = self.db.query(ItemAddon).filter(ItemAddon.id == command.addon_id)
        addon = addon_query.first()
        if not addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon with ID: {command.addon_id} not found")

        update_data = {}
        if command.name is not None:
            update_data[ItemAddon.name] = command.name
        if command.description is not None:
            update_data[ItemAddon.description] = command.description
        if command.price is not None:
            update_data[ItemAddon.price] = command.price
        if command.image_url is not None:
            update_data[ItemAddon.image_url] = command.image_url
        if command.is_available is not None:
            update_data[ItemAddon.is_available] = command.is_available
        
        addon_query.update(update_data)
        self.db.commit()
        return addon_query.first()

@dataclass(frozen=True)
class DeleteItemAddonCommand:
    addon_id: int

class DeleteItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteItemAddonCommand):
        addon = self.db.query(ItemAddon).filter(ItemAddon.id == command.addon_id).first()
        if not addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Addon with ID: {command.addon_id} not found")

        self.db.delete(addon)
        self.db.commit()
        return {"msg": f"Addon with id: {command.addon_id} deleted successfully"}


# =============================================================================================================
# ITEM VARIATION COMMANDS
# =============================================================================================================

@dataclass
class CreateItemVariationCommand:
    item_id: int
    name: str
    price: float
    description: Optional[str] = None
    is_available: Optional[bool] = True

class CreateItemVariationHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateItemVariationCommand):
        variation = ItemVariation(
            item_id=command.item_id,
            name=command.name,
            description=command.description,
            price=command.price,
            is_available=command.is_available
        )
        self.db.add(variation)
        self.db.commit()
        self.db.refresh(variation)
        return variation

@dataclass(frozen=True)
class UpdateItemVariationCommand:
    variation_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None

class UpdateItemVariationHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemVariationCommand):
        variation_query = self.db.query(ItemVariation).filter(ItemVariation.id == command.variation_id)
        variation = variation_query.first()
        if not variation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variation with ID: {command.variation_id} not found")

        update_data = {}
        if command.name is not None:
            update_data[ItemVariation.name] = command.name
        if command.description is not None:
            update_data[ItemVariation.description] = command.description
        if command.price is not None:
            update_data[ItemVariation.price] = command.price
        if command.is_available is not None:
            update_data[ItemVariation.is_available] = command.is_available
        
        variation_query.update(update_data)
        self.db.commit()
        return variation_query.first()

@dataclass(frozen=True)
class DeleteItemVariationCommand:
    variation_id: int

class DeleteItemVariationHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteItemVariationCommand):
        variation = self.db.query(ItemVariation).filter(ItemVariation.id == command.variation_id).first()
        if not variation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variation with ID: {command.variation_id} not found")

        self.db.delete(variation)
        self.db.commit()
        return {"msg": f"Variation with id: {command.variation_id} deleted successfully"}


# =============================================================================================================
# ORDER COMMANDS
# =============================================================================================================

@dataclass
class CreateOrderCommand:
    user_id: int
    vendor_id: int
    status: str
    subtotal: float
    delivery_fee: float
    total: float
    items: List[ItemBase]
    rider_id: int | None = None
    delivery_address_id: int | None = None
    notes: str | None = None
    estimated_delivery_time: str | None = None


class CreateOrderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateOrderCommand):

        # Validate OrderStatus
        if isinstance(command.status, str):
            try:
                command.status = OrderStatus(command.status.lower())
            except ValueError:
                valid = [v.value for v in OrderStatus]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status '{command.status}'. Allowed: {', '.join(valid)}"
                )

        # Validate user, vendor, delivery address
        from ..models import User, Vendor, DeliveryAddress

        if not self.db.query(User).filter(User.id == command.user_id).first():
            raise HTTPException(404, "User not found")

        if not self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first():
            raise HTTPException(404, "Vendor not found")

        if command.delivery_address_id and \
            not self.db.query(DeliveryAddress).filter(DeliveryAddress.id == command.delivery_address_id).first():
            raise HTTPException(404, "Delivery address not found")

        rider_id = command.rider_id if command.rider_id not in [0, "0", None, ""] else None
        delivery_address_id = command.delivery_address_id if command.delivery_address_id not in [0, "0", None, ""] else None
        

        # ----------------------------
        # 1. Create Order
        # ----------------------------
        order = Order(
            user_id=command.user_id,
            vendor_id=command.vendor_id,
            rider_id=rider_id,
            delivery_address_id=delivery_address_id,
            status=command.status,
            subtotal=command.subtotal,
            delivery_fee=command.delivery_fee,
            total=command.total,
            notes=command.notes,
            estimated_delivery_time=command.estimated_delivery_time
        )

        self.db.add(order)
        self.db.flush()   # IMPORTANT: generates order.id

        # ----------------------------
        # 2. Add Items (Many-to-Many)
        # ----------------------------
        for item_cmd in command.items:

            item = self.db.query(Item).filter(Item.id == item_cmd.id).first()
            if not item:
                raise HTTPException(404, f"Item {item_cmd.id} not found")

            self.db.execute(
                order_items_association.insert().values(
                    order_id=order.id,
                    item_id=item_cmd.id,
                    quantity=item_cmd.quantity,
                    # unit_price=item_cmd.unit_price
                )
            )

        # ----------------------------
        # 3. Commit
        # ----------------------------
        try:
            self.db.commit()
            self.db.refresh(order)
            return order

        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Error creating order: {str(e)}")



@dataclass(frozen=True)
class UpdateOrderCommand:
    order_id: int
    rider_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    delivery_fee: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None

class UpdateOrderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateOrderCommand):
        order_query = self.db.query(Order).filter(Order.id == command.order_id)
        order = order_query.first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID: {command.order_id} not found")

        update_data = {}
        if command.rider_id is not None:
            update_data[Order.rider_id] = command.rider_id
        if command.status is not None:
            update_data[Order.status] = command.status
        if command.delivery_fee is not None:
            update_data[Order.delivery_fee] = command.delivery_fee
        if command.total is not None:
            update_data[Order.total] = command.total
        if command.notes is not None:
            update_data[Order.notes] = command.notes
        if command.estimated_delivery_time is not None:
            update_data[Order.estimated_delivery_time] = command.estimated_delivery_time
        
        order_query.update(update_data)
        self.db.commit()
        return order_query.first()

@dataclass(frozen=True)
class DeleteOrderCommand:
    order_id: int

class DeleteOrderHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteOrderCommand):
        order = self.db.query(Order).filter(Order.id == command.order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID: {command.order_id} not found")

        self.db.delete(order)
        self.db.commit()
        return {"msg": f"Order with id: {command.order_id} deleted successfully"}


# =============================================================================================================
# CART COMMANDS
# =============================================================================================================

@dataclass
class CreateCartCommand:
    user_id: int
    vendor_id: int
    subtotal: Optional[float] = 0.0
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None

class CreateCartHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateCartCommand):
        cart = Cart(
            user_id=command.user_id,
            vendor_id=command.vendor_id,
            subtotal=command.subtotal,
            notes=command.notes,
            expires_at=command.expires_at
        )
        self.db.add(cart)
        self.db.commit()
        self.db.refresh(cart)
        return cart

@dataclass(frozen=True)
class UpdateCartCommand:
    cart_id: int
    subtotal: Optional[float] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None

class UpdateCartHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateCartCommand):
        cart_query = self.db.query(Cart).filter(Cart.id == command.cart_id)
        cart = cart_query.first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart with ID: {command.cart_id} not found")

        update_data = {}
        if command.subtotal is not None:
            update_data[Cart.subtotal] = command.subtotal
        if command.notes is not None:
            update_data[Cart.notes] = command.notes
        if command.expires_at is not None:
            update_data[Cart.expires_at] = command.expires_at
        
        cart_query.update(update_data)
        self.db.commit()
        return cart_query.first()

@dataclass(frozen=True)
class DeleteCartCommand:
    cart_id: int

class DeleteCartHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteCartCommand):
        cart = self.db.query(Cart).filter(Cart.id == command.cart_id).first()
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart with ID: {command.cart_id} not found")

        self.db.delete(cart)
        self.db.commit()
        return {"msg": f"Cart with id: {command.cart_id} deleted successfully"}


# =============================================================================================================
# WALLET COMMANDS  
# =============================================================================================================

# ==================
# CREATE WALLETS (Auto-created with user/vendor/rider registration)
# ==================

def create_user_wallet(db: Session, user_id: int) -> UserWallet:
    """Automatically create a wallet when a user registers"""
    wallet = UserWallet(user_id=user_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def create_vendor_wallet(db: Session, vendor_id: int) -> VendorWallet:
    """Automatically create a wallet when a vendor registers"""
    wallet = VendorWallet(vendor_id=vendor_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def create_rider_wallet(db: Session, rider_id: int) -> RiderWallet:
    """Automatically create a wallet when a rider registers"""
    wallet = RiderWallet(rider_id=rider_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

# ==================
# WALLET FUNDING
# ==================

@dataclass(frozen=True)
class FundUserWalletCommand:
    user_id: int
    amount: float
    description: str
    payment_method: str

class FundUserWalletHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: FundUserWalletCommand):
        if command.amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
        
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == command.user_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User wallet not found")
        
        if not wallet.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet is not active")
        
        if wallet.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet is locked")
        
        # Record the transaction
        balance_before = wallet.balance
        balance_after = balance_before + command.amount
        
        transaction = WalletTransaction(
            user_wallet_id=wallet.id,
            transaction_type=WalletTransactionType.DEPOSIT,
            status=WalletTransactionStatus.COMPLETED,
            amount=command.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=command.description,
            reference_type="funding",
            processed_at=datetime.utcnow()
        )
        
        # Update wallet balance
        wallet.balance = balance_after
        wallet.last_transaction_at = datetime.utcnow()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction

# ==================
# WALLET WITHDRAWAL
# ==================

@dataclass(frozen=True)
class WithdrawFromWalletCommand:
    wallet_type: str  # "user", "vendor", or "rider"
    owner_id: int
    amount: float
    description: str
    withdrawal_method: str
    account_details: dict

class WithdrawFromWalletHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: WithdrawFromWalletCommand):
        if command.amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
        
        # Get the appropriate wallet
        wallet = None
        wallet_id_field = None
        
        if command.wallet_type == "user":
            wallet = self.db.query(UserWallet).filter(UserWallet.user_id == command.owner_id).first()
            wallet_id_field = "user_wallet_id"
        elif command.wallet_type == "vendor":
            wallet = self.db.query(VendorWallet).filter(VendorWallet.vendor_id == command.owner_id).first()
            wallet_id_field = "vendor_wallet_id"
            if wallet and command.amount < wallet.minimum_withdrawal:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                  detail=f"Minimum withdrawal amount is {wallet.minimum_withdrawal}")
        elif command.wallet_type == "rider":
            wallet = self.db.query(RiderWallet).filter(RiderWallet.rider_id == command.owner_id).first()
            wallet_id_field = "rider_wallet_id"
            if wallet and command.amount < wallet.minimum_withdrawal:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                  detail=f"Minimum withdrawal amount is {wallet.minimum_withdrawal}")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet type")
        
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{command.wallet_type.title()} wallet not found")
        
        if not wallet.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet is not active")
        
        if wallet.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet is locked")
        
        if wallet.balance < command.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")
        
        # Record the transaction
        balance_before = wallet.balance
        balance_after = balance_before - command.amount
        
        transaction_data = {
            wallet_id_field: wallet.id,
            "transaction_type": WalletTransactionType.WITHDRAWAL,
            "status": WalletTransactionStatus.PENDING,  # Withdrawals start as pending
            "amount": command.amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "description": command.description,
            "reference_type": "withdrawal",
        }
        
        transaction = WalletTransaction(**transaction_data)
        
        # Update wallet balance
        wallet.balance = balance_after
        wallet.last_transaction_at = datetime.utcnow()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction

# ==================
# WALLET TRANSFERS
# ==================

@dataclass(frozen=True)
class TransferBetweenWalletsCommand:
    sender_type: str  # "user", "vendor", or "rider"
    sender_id: int
    recipient_type: str  # "user", "vendor", or "rider"
    recipient_id: int
    amount: float
    description: str

class TransferBetweenWalletsHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: TransferBetweenWalletsCommand):
        if command.amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero")
        
        # Get sender wallet
        sender_wallet = self._get_wallet(command.sender_type, command.sender_id)
        if not sender_wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender wallet not found")
        
        # Get recipient wallet
        recipient_wallet = self._get_wallet(command.recipient_type, command.recipient_id)
        if not recipient_wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient wallet not found")
        
        # Validate sender wallet
        if not sender_wallet.is_active or sender_wallet.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sender wallet is not available")
        
        if sender_wallet.balance < command.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient sender wallet balance")
        
        # Validate recipient wallet
        if not recipient_wallet.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient wallet is not active")
        
        # Process transfer
        sender_balance_before = sender_wallet.balance
        sender_balance_after = sender_balance_before - command.amount
        
        recipient_balance_before = recipient_wallet.balance
        recipient_balance_after = recipient_balance_before + command.amount
        
        # Create sender transaction (debit)
        sender_transaction_data = {
            f"{command.sender_type}_wallet_id": sender_wallet.id,
            "transaction_type": WalletTransactionType.TRANSFER,
            "status": WalletTransactionStatus.COMPLETED,
            "amount": -command.amount,  # Negative for debit
            "balance_before": sender_balance_before,
            "balance_after": sender_balance_after,
            "description": f"Transfer to {command.recipient_type} ID {command.recipient_id}: {command.description}",
            "reference_type": "transfer_out",
            "processed_at": datetime.utcnow()
        }
        
        # Create recipient transaction (credit)
        recipient_transaction_data = {
            f"{command.recipient_type}_wallet_id": recipient_wallet.id,
            "transaction_type": WalletTransactionType.TRANSFER,
            "status": WalletTransactionStatus.COMPLETED,
            "amount": command.amount,  # Positive for credit
            "balance_before": recipient_balance_before,
            "balance_after": recipient_balance_after,
            "description": f"Transfer from {command.sender_type} ID {command.sender_id}: {command.description}",
            "reference_type": "transfer_in",
            "processed_at": datetime.utcnow()
        }
        
        sender_transaction = WalletTransaction(**sender_transaction_data)
        recipient_transaction = WalletTransaction(**recipient_transaction_data)
        
        # Update wallet balances
        sender_wallet.balance = sender_balance_after
        sender_wallet.last_transaction_at = datetime.utcnow()
        
        recipient_wallet.balance = recipient_balance_after
        recipient_wallet.last_transaction_at = datetime.utcnow()
        
        self.db.add_all([sender_transaction, recipient_transaction])
        self.db.commit()
        
        return {
            "sender_transaction": sender_transaction,
            "recipient_transaction": recipient_transaction,
            "message": "Transfer completed successfully"
        }
    
    def _get_wallet(self, wallet_type: str, owner_id: int):
        """Helper method to get wallet by type and owner ID"""
        if wallet_type == "user":
            return self.db.query(UserWallet).filter(UserWallet.user_id == owner_id).first()
        elif wallet_type == "vendor":
            return self.db.query(VendorWallet).filter(VendorWallet.vendor_id == owner_id).first()
        elif wallet_type == "rider":
            return self.db.query(RiderWallet).filter(RiderWallet.rider_id == owner_id).first()
        return None

# ==================
# PAYMENT PROCESSING
# ==================

@dataclass(frozen=True)
class ProcessOrderPaymentCommand:
    order_id: int
    user_id: int
    amount: float

class ProcessOrderPaymentHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: ProcessOrderPaymentCommand):
        # Get user wallet
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == command.user_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User wallet not found")
        
        if not wallet.is_active or wallet.is_locked:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet is not available")
        
        if wallet.balance < command.amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")
        
        # Process payment
        balance_before = wallet.balance
        balance_after = balance_before - command.amount
        
        transaction = WalletTransaction(
            user_wallet_id=wallet.id,
            transaction_type=WalletTransactionType.PAYMENT,
            status=WalletTransactionStatus.COMPLETED,
            amount=command.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Payment for order #{command.order_id}",
            reference_id=str(command.order_id),
            reference_type="order",
            processed_at=datetime.utcnow()
        )
        
        # Update wallet balance
        wallet.balance = balance_after
        wallet.last_transaction_at = datetime.utcnow()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction

# ==================
# SET TRANSACTION PIN
# ==================

@dataclass(frozen=True)
class SetTransactionPinCommand:
    user_id: int
    transaction_pin: str

class SetTransactionPinHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: SetTransactionPinCommand):
        wallet = self.db.query(UserWallet).filter(UserWallet.user_id == command.user_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User wallet not found")
        
        # In a real app, you'd hash the PIN before storing
        wallet.transaction_pin = command.transaction_pin
        self.db.commit()
        
        return {"message": "Transaction PIN set successfully"}


# =============================================================================================================
# ORDER ITEM COMMANDS
# =============================================================================================================

@dataclass(frozen=True)
class CreateOrderItemCommand:
    order_id: int
    item_id: int
    unit_price: float
    subtotal: float
    variation_id: Optional[int] = None
    quantity: int = 1
    notes: Optional[str] = None

class CreateOrderItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateOrderItemCommand):
        order_item = OrderItem(
            order_id=command.order_id,
            item_id=command.item_id,
            variation_id=command.variation_id,
            quantity=command.quantity,
            unit_price=command.unit_price,
            subtotal=command.subtotal,
            notes=command.notes
        )
        self.db.add(order_item)
        self.db.commit()
        self.db.refresh(order_item)
        return order_item

@dataclass(frozen=True)
class UpdateOrderItemCommand:
    order_item_id: int
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    notes: Optional[str] = None

class UpdateOrderItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateOrderItemCommand):
        order_item_query = self.db.query(OrderItem).filter(OrderItem.id == command.order_item_id)
        order_item = order_item_query.first()
        
        if not order_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order item with ID: {command.order_item_id} not found")
        
        update_data = {}
        if command.quantity is not None:
            update_data["quantity"] = command.quantity
        if command.unit_price is not None:
            update_data["unit_price"] = command.unit_price
        if command.subtotal is not None:
            update_data["subtotal"] = command.subtotal
        if command.notes is not None:
            update_data["notes"] = command.notes
            
        if update_data:
            order_item_query.update(update_data)
            self.db.commit()
        
        return order_item_query.first()

@dataclass(frozen=True)
class DeleteOrderItemCommand:
    order_item_id: int

class DeleteOrderItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteOrderItemCommand):
        order_item = self.db.query(OrderItem).filter(OrderItem.id == command.order_item_id).first()
        if not order_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order item with ID: {command.order_item_id} not found")

        self.db.delete(order_item)
        self.db.commit()
        return {"msg": f"Order item with id: {command.order_item_id} deleted successfully"}


# =============================================================================================================
# ORDER ITEM ADDON COMMANDS
# =============================================================================================================

@dataclass(frozen=True)
class CreateOrderItemAddonCommand:
    order_item_id: int
    addon_id: int
    price: float

class CreateOrderItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateOrderItemAddonCommand):
        order_item_addon = OrderItemAddon(
            order_item_id=command.order_item_id,
            addon_id=command.addon_id,
            price=command.price
        )
        self.db.add(order_item_addon)
        self.db.commit()
        self.db.refresh(order_item_addon)
        return order_item_addon

@dataclass(frozen=True)
class DeleteOrderItemAddonCommand:
    order_item_addon_id: int

class DeleteOrderItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteOrderItemAddonCommand):
        order_item_addon = self.db.query(OrderItemAddon).filter(OrderItemAddon.id == command.order_item_addon_id).first()
        if not order_item_addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order item addon with ID: {command.order_item_addon_id} not found")

        self.db.delete(order_item_addon)
        self.db.commit()
        return {"msg": f"Order item addon with id: {command.order_item_addon_id} deleted successfully"}


# =============================================================================================================
# ORDER TRACKING COMMANDS
# =============================================================================================================

@dataclass(frozen=True)
class CreateOrderTrackingCommand:
    order_id: int
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CreateOrderTrackingHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateOrderTrackingCommand):
        # Convert string status to enum
        try:
            status_enum = OrderStatus(command.status.lower())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                              detail=f"Invalid status: {command.status}")
        
        order_tracking = OrderTracking(
            order_id=command.order_id,
            status=status_enum,
            latitude=command.latitude,
            longitude=command.longitude
        )
        self.db.add(order_tracking)
        self.db.commit()
        self.db.refresh(order_tracking)
        return order_tracking

@dataclass(frozen=True)
class DeleteOrderTrackingCommand:
    order_tracking_id: int

class DeleteOrderTrackingHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteOrderTrackingCommand):
        order_tracking = self.db.query(OrderTracking).filter(OrderTracking.id == command.order_tracking_id).first()
        if not order_tracking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order tracking with ID: {command.order_tracking_id} not found")

        self.db.delete(order_tracking)
        self.db.commit()
        return {"msg": f"Order tracking with id: {command.order_tracking_id} deleted successfully"}


# =============================================================================================================
# CART ITEM COMMANDS  
# =============================================================================================================

@dataclass(frozen=True)
class CreateCartItemCommand:
    cart_id: int
    item_id: int
    unit_price: float
    subtotal: float
    variation_id: Optional[int] = None
    quantity: int = 1
    notes: Optional[str] = None

class CreateCartItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateCartItemCommand):
        cart_item = CartItem(
            cart_id=command.cart_id,
            item_id=command.item_id,
            variation_id=command.variation_id,
            quantity=command.quantity,
            unit_price=command.unit_price,
            subtotal=command.subtotal,
            notes=command.notes
        )
        self.db.add(cart_item)
        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item

@dataclass(frozen=True)
class UpdateCartItemCommand:
    cart_item_id: int
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    notes: Optional[str] = None

class UpdateCartItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateCartItemCommand):
        cart_item_query = self.db.query(CartItem).filter(CartItem.id == command.cart_item_id)
        cart_item = cart_item_query.first()
        
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart item with ID: {command.cart_item_id} not found")
        
        update_data = {}
        if command.quantity is not None:
            update_data["quantity"] = command.quantity
        if command.unit_price is not None:
            update_data["unit_price"] = command.unit_price
        if command.subtotal is not None:
            update_data["subtotal"] = command.subtotal
        if command.notes is not None:
            update_data["notes"] = command.notes
            
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            cart_item_query.update(update_data)
            self.db.commit()
        
        return cart_item_query.first()

@dataclass(frozen=True)
class DeleteCartItemCommand:
    cart_item_id: int

class DeleteCartItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteCartItemCommand):
        cart_item = self.db.query(CartItem).filter(CartItem.id == command.cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart item with ID: {command.cart_item_id} not found")

        self.db.delete(cart_item)
        self.db.commit()
        return {"msg": f"Cart item with id: {command.cart_item_id} deleted successfully"}


# =============================================================================================================
# CART ITEM ADDON COMMANDS
# =============================================================================================================

@dataclass(frozen=True)
class CreateCartItemAddonCommand:
    cart_item_id: int
    addon_id: int
    price: float

class CreateCartItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateCartItemAddonCommand):
        cart_item_addon = CartItemAddon(
            cart_item_id=command.cart_item_id,
            addon_id=command.addon_id,
            price=command.price
        )
        self.db.add(cart_item_addon)
        self.db.commit()
        self.db.refresh(cart_item_addon)
        return cart_item_addon

@dataclass(frozen=True)
class DeleteCartItemAddonCommand:
    cart_item_addon_id: int

class DeleteCartItemAddonHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: DeleteCartItemAddonCommand):
        cart_item_addon = self.db.query(CartItemAddon).filter(CartItemAddon.id == command.cart_item_addon_id).first()
        if not cart_item_addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart item addon with ID: {command.cart_item_addon_id} not found")

        self.db.delete(cart_item_addon)
        self.db.commit()
        return {"msg": f"Cart item addon with id: {command.cart_item_addon_id} deleted successfully"}