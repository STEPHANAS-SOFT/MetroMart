from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from enum import Enum


# ====================================================
# ENUM SCHEMAS
# ====================================================

class VendorType(str, Enum):
    RESTAURANT = "restaurant"
    SUPERMARKET = "supermarket"
    PHARMACY = "pharmacy"

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class RiderStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


# ====================================================
# USER SCHEMAS
# ====================================================

class UserBase(BaseModel):
    firebase_uid: str = Field(..., description="Firebase authentication UID")
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None



class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ====================================================
# ITEM SCHEMAS
# ====================================================

class ItemBase(BaseModel):
    name: str
    base_price: float
    vendor_id: int
    category_id: int
    quantity: Optional[int]
    description: Optional[str]
    image_url: Optional[str]
    is_available: Optional[bool]
    allows_addons: Optional[bool]
    # variation_id: Optional[int] 
    addon_group_ids: Optional[List[int]] = []


    class Config:
        from_attributes = True

class ItemCreate(ItemBase):
    pass

    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    base_price: Optional[float]
    image_url: Optional[str]
    is_available: Optional[bool]
    allows_addons: Optional[bool]
    category_id: Optional[int]
    addon_group_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ItemOrder(ItemBase):
    id: int
    

    class Config:
        from_attributes = True

# class ItemAddonGroupResponse(BaseModel):
#     id: int
#     name: str
#     base_price: float
#     description: Optional[str]
#     image_url: Optional[str]
#     is_available: Optional[bool]
#     allows_addons: Optional[bool]
#     vendor_id: int
#     category_id: int
#     # addon_groups: List[ItemAddonGroupResponse]


# class ItemWithAddonGroupsResponse(ItemAddonGroupResponse):
#     addon_groups: List[ItemAddonGroupResponse]

# ====================================================
# ITEM CATEGORY SCHEMAS
# ====================================================

class ItemCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ItemCategoryCreate(ItemCategoryBase):
    pass

class ItemCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ItemCategoryResponse(ItemCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ====================================================
# DELIVERY ADDRESS SCHEMAS
# ====================================================

class DeliveryAddressBase(BaseModel):
    user_id: int
    address: str
    latitude: float
    longitude: float
    name: Optional[str]
    is_default: Optional[bool] = False

    class Config:
        from_attributes = True

class DeliveryAddressCreate(DeliveryAddressBase):
    pass

class DeliveryAddressUpdate(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    name: Optional[str] = None
    is_default: Optional[bool] = None


class DeliveryAddressResponse(DeliveryAddressBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# RIDER SCHEMAS
# ====================================================

class RiderBase(BaseModel):
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

    class Config:
        from_attributes = True

class RiderCreate(RiderBase):
    pass

class RiderUpdate(BaseModel):
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

class RiderResponse(RiderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ====================================================
# VENDOR SCHEMAS
# ====================================================

class VendorBase(BaseModel):
    firebase_uid: str
    name: str
    vendor_type: VendorType
    description: Optional[str] = None
    email: EmailStr
    phone_number: str
    address: str
    latitude: float
    longitude: float
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = False
    is_active: Optional[bool] = True
    rating: Optional[float] = 0.0
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None



class VendorCreate(VendorBase):
    pass



class VendorUpdate(BaseModel):
    name: Optional[str] = None
    vendor_type: Optional[VendorType] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None



class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: Optional[List[ItemResponse]] = []

    class Config:
        from_attributes = True


# ====================================================
# ITEM ADDON GROUP SCHEMAS
# ====================================================

class ItemAddonGroupBase(BaseModel):
    vendor_id: int
    name: str
    description: Optional[str] = None
    is_required: Optional[bool] = False
    min_selections: Optional[int] = 0
    max_selections: Optional[int] = 1

    class Config:
        from_attributes = True

class ItemAddonGroupCreate(ItemAddonGroupBase):
    pass

class ItemAddonGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    min_selections: Optional[int] = None
    max_selections: Optional[int] = None

class ItemAddonGroupResponse(ItemAddonGroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# ITEM ADDON SCHEMAS
# ====================================================

class ItemAddonBase(BaseModel):
    group_id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    is_available: Optional[bool] = True

    class Config:
        from_attributes = True

class ItemAddonCreate(ItemAddonBase):
    pass

class ItemAddonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class ItemAddonResponse(ItemAddonBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# ITEM VARIATION SCHEMAS
# ====================================================

class ItemVariationBase(BaseModel):
    item_id: int
    name: str
    description: Optional[str] = None
    price: float
    is_available: Optional[bool] = True

    class Config:
        from_attributes = True

class ItemVariationCreate(ItemVariationBase):
    pass

class ItemVariationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None

class ItemVariationResponse(ItemVariationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# ORDER ITEM ADDON SCHEMAS
# ====================================================

class OrderItemAddonBase(BaseModel):
    order_item_id: int
    addon_id: int
    price: float

    class Config:
        from_attributes = True

class OrderItemAddonCreate(OrderItemAddonBase):
    pass

class OrderItemAddonResponse(OrderItemAddonBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# ORDER ITEM SCHEMAS
# ====================================================

class OrderItemBase(BaseModel):
    order_id: int
    item_id: int
    # variation_id: Optional[int] = None
    quantity: int
    unit_price: float
    subtotal: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class OrderItemCreate(OrderItemBase):
    addons: Optional[List[OrderItemAddonCreate]] = []

class OrderItemUpdate(BaseModel):
    variation_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    notes: Optional[str] = None

class OrderItemResponse(OrderItemBase):
    id: int
    created_at: datetime
    addons: Optional[List[OrderItemAddonResponse]] = []

    class Config:
        from_attributes = True


# ====================================================
# ORDER TRACKING SCHEMAS
# ====================================================

class OrderTrackingBase(BaseModel):
    order_id: int
    status: OrderStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class OrderTrackingCreate(OrderTrackingBase):
    pass

class OrderTrackingResponse(OrderTrackingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ====================================================
# ORDER SCHEMAS
# ====================================================

class OrderBase(BaseModel):
    user_id: int
    vendor_id: int
    subtotal: float
    total: float
    delivery_fee: Optional[float] = None
    status: Optional[OrderStatus] = OrderStatus.PENDING
    rider_id: Optional[int] = None
    delivery_address_id: Optional[int] = None
    notes: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderCreate(OrderBase):
    items: List[ItemOrder]

    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    rider_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    delivery_fee: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: Optional[List[OrderItemResponse]] = []
    tracking: Optional[List[OrderTrackingResponse]] = []

    class Config:
        from_attributes = True

# class OrderResponse(BaseModel):
#     id: int
#     user_id: int
#     vendor_id: int
#     delivery_address_id: int
#     subtotal: float
#     delivery_fee: float
#     total: float
#     notes: str | None
#     created_at: datetime
#     items: list[OrderItemBase]

#     class Config:
#         orm_mode = True


# ====================================================
# CART ITEM ADDON SCHEMAS
# ====================================================

class CartItemAddonBase(BaseModel):
    cart_item_id: int
    addon_id: int
    price: float

    class Config:
        from_attributes = True

class CartItemAddonCreate(CartItemAddonBase):
    pass

class CartItemAddonResponse(CartItemAddonBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Wallet Schemas =====

class UserWalletBase(BaseModel):
    daily_limit: Optional[float] = 50000.0
    is_active: Optional[bool] = True

class UserWalletResponse(UserWalletBase):
    id: int
    user_id: int
    balance: float
    is_locked: bool
    last_transaction_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class VendorWalletBase(BaseModel):
    commission_rate: Optional[float] = 0.15
    minimum_withdrawal: Optional[float] = 1000.0
    is_active: Optional[bool] = True

class VendorWalletResponse(VendorWalletBase):
    id: int
    vendor_id: int
    balance: float
    pending_balance: float
    is_locked: bool
    last_transaction_at: Optional[datetime]
    last_settlement_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class RiderWalletBase(BaseModel):
    delivery_rate: Optional[float] = 500.0
    minimum_withdrawal: Optional[float] = 500.0
    is_active: Optional[bool] = True

class RiderWalletResponse(RiderWalletBase):
    id: int
    rider_id: int
    balance: float
    pending_balance: float
    is_locked: bool
    last_transaction_at: Optional[datetime]
    last_settlement_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class WalletTransactionBase(BaseModel):
    amount: float
    description: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None

class WalletFundRequest(BaseModel):
    amount: float
    description: Optional[str] = "Wallet funding"
    payment_method: str  # e.g., "bank_transfer", "card", "mobile_money"

class WalletWithdrawRequest(BaseModel):
    amount: float
    description: Optional[str] = "Wallet withdrawal"
    withdrawal_method: str  # e.g., "bank_transfer", "mobile_money"
    account_details: dict  # Account information for withdrawal

class WalletTransferRequest(BaseModel):
    recipient_type: str  # "user", "vendor", or "rider"
    recipient_id: int
    amount: float
    description: Optional[str] = "Wallet transfer"
    transaction_pin: str

class WalletTransactionResponse(WalletTransactionBase):
    id: int
    user_wallet_id: Optional[int]
    vendor_wallet_id: Optional[int]
    rider_wallet_id: Optional[int]
    transaction_type: str
    status: str
    balance_before: float
    balance_after: float
    processed_at: Optional[datetime]
    processor_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class WalletBalanceResponse(BaseModel):
    balance: float
    pending_balance: Optional[float]
    last_transaction_at: Optional[datetime]

class SetTransactionPinRequest(BaseModel):
    transaction_pin: str
    confirm_pin: str


# ====================================================
# CART ITEM SCHEMAS
# ====================================================

class CartItemBase(BaseModel):
    cart_id: int
    item_id: int
    variation_id: Optional[int] = None
    quantity: int = 1
    unit_price: float
    subtotal: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class CartItemCreate(CartItemBase):
    addons: Optional[List[CartItemAddonCreate]] = []

class CartItemUpdate(BaseModel):
    variation_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    subtotal: Optional[float] = None
    notes: Optional[str] = None

class CartItemResponse(CartItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    addons: Optional[List[CartItemAddonResponse]] = []

    class Config:
        from_attributes = True


# ====================================================
# CART SCHEMAS
# ====================================================

class CartBase(BaseModel):
    user_id: int
    vendor_id: int
    subtotal: Optional[float] = 0.0
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CartCreate(CartBase):
    items: Optional[List[CartItemCreate]] = []

class CartUpdate(BaseModel):
    subtotal: Optional[float] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None

class CartResponse(CartBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: Optional[List[CartItemResponse]] = []

    class Config:
        from_attributes = True

