from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, Boolean, ForeignKey, Enum, Table, ARRAY
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from .shared.database import Base
import enum

class VendorType(enum.Enum):
    """
    Enumeration for different types of vendors in the system.
    Used to categorize vendors based on their business type.
    """
    RESTAURANT = "restaurant"
    SUPERMARKET = "supermarket"
    PHARMACY = "pharmacy"

class OrderStatus(enum.Enum):
    """
    Enumeration for tracking the status of an order throughout its lifecycle.
    Represents all possible states from order creation to delivery.
    """
    PENDING = "pending"          # Order placed but not yet accepted by vendor
    ACCEPTED = "accepted"        # Vendor has accepted the order
    REJECTED = "rejected"        # Vendor has rejected the order
    PREPARING = "preparing"      # Food is being prepared
    READY_FOR_PICKUP = "ready_for_pickup"  # Order ready for rider pickup
    IN_TRANSIT = "in_transit"    # Rider is delivering the order
    DELIVERED = "delivered"      # Order has been delivered successfully
    CANCELLED = "cancelled"      # Order was cancelled by customer or vendor

class RiderStatus(enum.Enum):
    """
    Enumeration for tracking rider availability status.
    Used to determine if a rider can accept new delivery requests.
    """
    AVAILABLE = "available"      # Rider is available for new deliveries
    BUSY = "busy"               # Rider is currently on a delivery
    OFFLINE = "offline"         # Rider is not accepting deliveries

class WalletTransactionType(enum.Enum):
    """
    Enumeration for different types of wallet transactions.
    Used to categorize all wallet-related financial activities.
    """
    DEPOSIT = "deposit"          # Money added to wallet (funding)
    WITHDRAWAL = "withdrawal"    # Money removed from wallet
    PAYMENT = "payment"          # Payment for services (orders, delivery)
    REFUND = "refund"           # Money refunded to wallet
    TRANSFER = "transfer"        # Money transferred between wallets
    COMMISSION = "commission"    # Platform commission earned
    BONUS = "bonus"             # Promotional bonus or reward

class WalletTransactionStatus(enum.Enum):
    """
    Enumeration for transaction processing status.
    Tracks the lifecycle of wallet transactions.
    """
    PENDING = "pending"          # Transaction initiated but not processed
    COMPLETED = "completed"      # Transaction successfully processed
    FAILED = "failed"           # Transaction failed to process
    CANCELLED = "cancelled"      # Transaction was cancelled
    REFUNDED = "refunded"       # Transaction was refunded

class User(Base):
    """
    Represents end-users (customers) of the food delivery system.
    
    This model stores essential user information including:
    - Authentication details (Firebase UID)
    - Personal information (name, contact details)
    - Location data for proximity-based features
    - Push notification token for order updates
    
    Users can have multiple delivery addresses and place multiple orders.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    firebase_uid = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    fcm_token = Column(String)  # Firebase Cloud Messaging token for push notifications
    latitude = Column(Float)    # User's current location for proximity search
    longitude = Column(Float)   # and delivery distance calculation
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="user")
    addresses = relationship("DeliveryAddress", back_populates="user")
    wallet = relationship("UserWallet", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Vendor(Base):
    """
    Represents businesses (restaurants, supermarkets, pharmacies) on the platform.
    
    This model manages all vendor-related information including:
    - Business details (name, type, description)
    - Contact information
    - Location for delivery radius and distance calculation
    - Operating hours
    - Delivery capabilities
    - Notification preferences
    
    Key features:
    - Supports multiple types of vendors (restaurant/supermarket/pharmacy)
    - Tracks whether vendor has their own delivery service
    - Manages business hours
    - Handles location-based services
    - Supports push notifications for new orders
    """
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, nullable=False)
    firebase_uid = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    vendor_type = Column(Enum(VendorType), nullable=False)
    description = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)  # For location-based services
    longitude = Column(Float, nullable=False) # and delivery distance calculation
    logo_url = Column(String)
    has_own_delivery = Column(Boolean, default=False)  # Whether vendor manages own delivery
    is_active = Column(Boolean, default=True)  # Vendor's availability status
    fcm_token = Column(String)  # For order notifications
    opening_time = Column(String)  # Daily opening time
    closing_time = Column(String)  # Daily closing time
    rating = Column(Float, default=0.0)  # Average customer rating
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    items = relationship("Item", back_populates="vendor")
    # item_categories = relationship("ItemCategory", back_populates="vendor", cascade="all, delete-orphan")
    item_addon_groups = relationship("ItemAddonGroup", back_populates="vendor", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="vendor")
    wallet = relationship("VendorWallet", back_populates="vendor", uselist=False)

class ItemCategory(Base):
    """
    Represents categories for menu items (e.g., Swallow, Rice Dishes, Soups, Drinks).
    
    Used to organize items in the menu and make navigation easier for users.
    Categories help in filtering and organizing items within a vendor's menu.
    Each category belongs to a specific vendor.
    """
    __tablename__ = "item_categories"

    id = Column(Integer, primary_key=True, nullable=False)
    # vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)      # e.g., "Swallow", "Rice Dishes"
    description = Column(String)               # Optional category description
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    # vendor = relationship("Vendor", back_populates="item_categories")
    items = relationship("Item", back_populates="category", cascade="all, delete-orphan")


# Association table for many-to-many relationship between Item and ItemAddonGroup
item_addon_group_association = Table(
    'item_addon_group_association',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id', ondelete='CASCADE'), primary_key=True),
    Column('addon_group_id', Integer, ForeignKey('item_addon_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
)


class Item(Base):
    """
    Represents menu items available for order (e.g., Semo, Jollof Rice).
    
    This model is designed to handle the complexity of Nigerian cuisine, including:
    - Base items with customizable options
    - Reference to an addon group for customizable options
    - Different portion sizes/variations
    - Flexible pricing structure
    
    Examples:
    1. Semo (base item) linked to:
       - Addon group for soups (Egusi, Vegetable, Okro)
       - Addon group for proteins (Meat, Fish)
    2. Jollof Rice with:
       - Different portions (small, large)
       - Addon group for proteins
       - Addon group for sides
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=False)
    # variation_id = Column(Integer, ForeignKey("item_variations.id"), nullable=True)
    quantity = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String)
    base_price = Column(Float, nullable=False)  # Base price without add-ons
    image_url = Column(String)
    is_available = Column(Boolean, default=True)
    allows_addons = Column(Boolean, default=False)  # Whether item can have add-ons
    addon_group_ids = Column(ARRAY(Integer), default=list, nullable=True)  # Comma-separated list of addon group IDs
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="items")
    category = relationship("ItemCategory", back_populates="items")
    # addon_groups = relationship("ItemAddonGroup", secondary=item_addon_group_association, back_populates="items")
    # order_items = relationship("OrderItem", back_populates="item")
    variations = relationship("ItemVariation", back_populates="item")
        # Inverse relationship
    orders = relationship("Order", secondary="order_items_association", back_populates="items")


class DeliveryAddress(Base):
    """
    Represents saved delivery addresses for users.
    
    This model manages delivery locations:
    - Multiple addresses per user
    - Geocoding support for delivery routing
    - Default address flagging
    
    Features:
    - Store multiple addresses per user
    - Set default delivery address
    - Geographic coordinates for delivery optimization
    - Address history for quick reordering
    
    Used for:
    - Delivery location selection during ordering
    - Distance calculation for delivery fees
    - Route optimization for riders
    - Quick address selection during checkout
    """
    __tablename__ = "delivery_addresses"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address = Column(String, nullable=False)          # Full text address
    latitude = Column(Float, nullable=False)          # Geographic coordinates
    longitude = Column(Float, nullable=False)         # for delivery routing
    is_default = Column(Boolean, default=False)       # User's default address
    name = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="delivery_address")

class Rider(Base):
    """
    Represents delivery personnel who can pick up and deliver orders.
    
    This model manages all rider-related information:
    - Personal and contact information
    - Vehicle and license details
    - Verification status
    - Real-time location tracking
    - Availability status
    
    Features:
    - Rider verification system
    - Real-time location updates
    - Status tracking (Available/Busy/Offline)
    - Push notifications for new orders
    - Vehicle type tracking for different delivery needs
    
    Used for:
    - Assigning orders to available riders
    - Tracking deliveries in real-time
    - Managing rider verification
    - Calculating delivery distances and ETAs
    """
    __tablename__ = "riders"

    id = Column(Integer, primary_key=True, nullable=False)
    firebase_uid = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)      # e.g., "Motorcycle", "Car"
    vehicle_number = Column(String, nullable=False)    # Vehicle registration number
    license_number = Column(String, nullable=False)    # Driver's license number
    is_verified = Column(Boolean, default=False)       # Verification status
    is_active = Column(Boolean, default=True)         # Account active status
    current_latitude = Column(Float)                  # Real-time location
    current_longitude = Column(Float)                 # tracking
    fcm_token = Column(String)                       # For delivery notifications
    status = Column(Enum(RiderStatus), default=RiderStatus.OFFLINE)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="rider")
    wallet = relationship("RiderWallet", back_populates="rider", uselist=False)


# Association table for many-to-many relationship between orders and items
order_items_association = Table(
    "order_items_association",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("quantity", Integer, nullable=False, default=1),  # optional: store quantity directly here
    # Column("unit_price", Float, nullable=False, default=0.0)  # optional: store price at order time
)



class Order(Base):
    """
    Represents a complete order in the system.
    
    This is the central model that connects all aspects of an order:
    - Customer details
    - Vendor information
    - Delivery details
    - Order items and their customizations
    - Pricing and fees
    - Status tracking
    
    Features:
    - Complete order lifecycle management
    - Complex pricing calculations
    - Delivery tracking and estimation
    - Status history
    - Special instructions handling
    
    Example Order Flow:
    1. User places order (PENDING)
    2. Vendor accepts order (ACCEPTED)
    3. Vendor prepares items (PREPARING)
    4. Order ready for pickup (READY_FOR_PICKUP)
    5. Rider picks up order (IN_TRANSIT)
    6. Delivery completed (DELIVERED)
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    rider_id = Column(Integer, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True)
    # variation_id = Column(Integer, ForeignKey("item_variations.id", ondelete="SET NULL"), nullable=True)
    delivery_address_id = Column(Integer, ForeignKey("delivery_addresses.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float)
    total = Column(Float, nullable=False)
    notes = Column(String)
    estimated_delivery_time = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    vendor = relationship("Vendor", back_populates="orders")
    rider = relationship("Rider", back_populates="orders")
    # variation = relationship("ItemVariation", back_populates="orders")
    delivery_address = relationship("DeliveryAddress", back_populates="orders")

    # Many-to-many with items
    items = relationship("Item", secondary=order_items_association, back_populates="orders")


class ItemAddonGroup(Base):
    """
    Represents a group of related add-ons that can be linked to items (e.g., Soups group, Proteins group).
    
    This model manages collections of related add-ons and their selection rules:
    - Groups similar add-ons (e.g., all available soups, proteins, or drinks)
    - Controls selection requirements (required/optional)
    - Manages selection limits (minimum and maximum choices)
    - Each addon group belongs to a specific vendor
    - Items reference this group to enable add-ons
    
    Examples:
    1. "Soups" addon group:
       - Required selection
       - Min: 1, Max: 1 (must choose exactly one soup)
       - Can be linked to multiple items (Semo, Fufu, etc.)
    2. "Proteins" addon group:
       - Optional selection
       - Min: 0, Max: 3 (can choose up to 3 proteins)
       - Can be linked to multiple items
    3. "Drinks" addon group:
       - Optional selection
       - Min: 0, Max: 1 (can choose one drink)
       - Can be linked to multiple items
    """
    __tablename__ = "item_addon_groups"

    id = Column(Integer, primary_key=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Soups", "Proteins", "Drinks"
    description = Column(String)
    is_required = Column(Boolean, default=False)  # Whether selection is mandatory
    min_selections = Column(Integer, default=0)   # Minimum number of selections required
    max_selections = Column(Integer, default=1)   # Maximum number of selections allowed
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    vendor = relationship("Vendor", back_populates="item_addon_groups")
    # items = relationship("Item", secondary=item_addon_group_association, back_populates="addon_groups")
    addons = relationship("ItemAddon", back_populates="group", cascade="all, delete-orphan")

class ItemAddon(Base):
    """
    Represents individual add-on options within a group (e.g., Egusi Soup within Soups group).
    
    This model handles specific add-on items that can be added to a base item:
    - Individual add-on options (specific soups, proteins, drinks)
    - Separate pricing for each add-on
    - Availability tracking
    
    Examples:
    1. In Soups group:
       - Egusi Soup (+price)
       - Vegetable Soup (+price)
       - Okro Soup (+price)
    2. In Proteins group:
       - Goat Meat (+price)
       - Fish (+price)
       - Chicken (+price)
    3. In Drinks group:
       - Coca-Cola (+price)
       - Fanta (+price)
    """
    __tablename__ = "item_addons"

    id = Column(Integer, primary_key=True, nullable=False)
    group_id = Column(Integer, ForeignKey("item_addon_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Egusi Soup", "Goat Meat", "Coca-Cola"
    description = Column(String)
    price = Column(Float, nullable=False)  # Additional cost for this add-on
    image_url = Column(String)
    is_available = Column(Boolean, default=True)  # Current availability status
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    group = relationship("ItemAddonGroup", back_populates="addons")
    order_item_addons = relationship("OrderItemAddon", back_populates="addon")

class ItemVariation(Base):
    """
    Represents different variations of an item (e.g., different sizes or portions).
    
    This model handles size/portion variations of menu items:
    - Different portion sizes (Small, Medium, Large)
    - Different pricing per variation
    - Availability tracking per variation
    
    Examples:
    1. Semo variations:
       - Small portion (base price)
       - Large portion (higher price)
    2. Rice dish variations:
       - Half portion
       - Full portion
       - Party size
    """
    __tablename__ = "item_variations"

    id = Column(Integer, primary_key=True, nullable=False)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Small", "Medium", "Large"
    description = Column(String)
    price = Column(Float, nullable=False)  # Total price for this variation
    is_available = Column(Boolean, default=True)  # Current availability status
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    item = relationship("Item", back_populates="variations")
    order_items = relationship("OrderItem", back_populates="variation")

class OrderItem(Base):
    """
    Represents individual items within an order with their variations and add-ons.
    
    This model manages the details of each item in an order:
    - Links to the base item and its selected variation
    - Tracks quantity and pricing
    - Manages selected add-ons
    - Calculates subtotal including all add-ons
    
    Examples:
    1. Order for Semo:
       - Large portion variation
       - With Egusi Soup add-on
       - With Goat Meat add-on
       - Quantity: 2
    2. Order for Jollof Rice:
       - Regular portion
       - With Chicken add-on
       - With Coca-Cola drink
       - Quantity: 1
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, nullable=False)
    # order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    # item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    variation_id = Column(Integer, ForeignKey("item_variations.id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Base price or variation price
    subtotal = Column(Float, nullable=False)    # Total including all add-ons
    notes = Column(String)                      # Special instructions
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    # order = relationship("Order", back_populates="items")
    # item = relationship("Item", back_populates="order_items")
    variation = relationship("ItemVariation", back_populates="order_items")
    addons = relationship("OrderItemAddon", back_populates="order_item")

class OrderItemAddon(Base):
    """
    Represents the add-ons selected for a specific item in an order.
    
    This model tracks which add-ons were selected for each order item:
    - Links add-ons to specific order items
    - Records the price at time of order
    - Maintains historical record of selections
    
    Examples:
    1. For a Semo order item:
       - Selected Egusi Soup add-on
       - Selected Goat Meat add-on
    2. For a Rice order item:
       - Selected Chicken add-on
       - Selected Extra Sauce add-on
    
    Note: Price is stored at time of order to handle future price changes
    """
    __tablename__ = "order_item_addons"

    id = Column(Integer, primary_key=True, nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    addon_id = Column(Integer, ForeignKey("item_addons.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float, nullable=False)  # Price at time of order
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    order_item = relationship("OrderItem", back_populates="addons")
    addon = relationship("ItemAddon", back_populates="order_item_addons")

class OrderTracking(Base):
    """
    Represents the tracking history of an order's status changes and locations.
    
    This model maintains a complete history of:
    - All status changes in an order
    - Location updates during delivery
    - Timestamps for each update
    
    Features:
    - Complete order status history
    - Real-time location tracking during delivery
    - Timestamp for each status change
    - Audit trail for order lifecycle
    
    Used for:
    - Showing order progress to customers
    - Tracking delivery location in real-time
    - Analyzing delivery performance
    - Resolving delivery disputes
    - Generating delivery statistics
    """
    __tablename__ = "order_tracking"

    id = Column(Integer, primary_key=True, nullable=False)
    # order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)  # Status at this point
    latitude = Column(Float)                           # Location coordinates
    longitude = Column(Float)                          # during delivery
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    # order = relationship("Order", back_populates="tracking")


class Cart(Base):
    """
    Represents a user's shopping cart for a specific vendor.
    
    This model manages the temporary storage of items before order placement:
    - Stores items user wants to order
    - Groups items by vendor
    - Maintains running total
    - Tracks cart creation and update times
    
    Features:
    - Single vendor per cart to maintain delivery logic
    - Real-time price calculation
    - Automatic expiration handling
    - Items and their customizations storage
    
    Used for:
    - Building orders incrementally
    - Price calculation before checkout
    - Temporary item storage
    - Quick reordering from previous carts
    """
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    subtotal = Column(Float, nullable=False, default=0.0)  # Sum of all items and add-ons
    notes = Column(String)                                # Special instructions for entire cart
    expires_at = Column(TIMESTAMP(timezone=True))         # Cart expiration timestamp
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    vendor = relationship("Vendor")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    """
    Represents individual items in a user's shopping cart.
    
    This model manages individual items and their customizations:
    - Stores item quantity
    - Manages item variations
    - Tracks selected add-ons
    - Calculates per-item subtotal
    
    Features:
    - Complete item customization storage
    - Real-time price updates
    - Add-on and variation handling
    - Special instructions per item
    
    Example Cart Item:
    1. Large Semo with:
       - Egusi Soup add-on
       - Extra Meat add-on
       - Special instruction: "Make it spicy"
       - Quantity: 2
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, nullable=False)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    variation_id = Column(Integer, ForeignKey("item_variations.id", ondelete="SET NULL"))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)        # Base price or variation price
    subtotal = Column(Float, nullable=False)          # Total including add-ons
    notes = Column(String)                           # Special instructions for this item
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    item = relationship("Item")
    variation = relationship("ItemVariation")
    addons = relationship("CartItemAddon", back_populates="cart_item", cascade="all, delete-orphan")


class CartItemAddon(Base):
    """
    Represents add-ons selected for items in the shopping cart.
    
    This model tracks selected add-ons for cart items:
    - Links add-ons to specific cart items
    - Stores current add-on prices
    - Maintains selection history
    
    Features:
    - Flexible add-on selection
    - Real-time price tracking
    - Easy transfer to order add-ons
    
    Example:
    - For Semo in cart:
      - Selected Egusi Soup add-on
      - Selected Extra Meat add-on
    """
    __tablename__ = "cart_item_addons"

    id = Column(Integer, primary_key=True, nullable=False)
    cart_item_id = Column(Integer, ForeignKey("cart_items.id", ondelete="CASCADE"), nullable=False)
    addon_id = Column(Integer, ForeignKey("item_addons.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float, nullable=False)             # Current price of the add-on
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    cart_item = relationship("CartItem", back_populates="addons")
    addon = relationship("ItemAddon")


class UserWallet(Base):
    """
    Represents a user's wallet for managing their funds.
    
    This model manages user financial transactions and balance:
    - Stores current wallet balance
    - Tracks wallet status and security
    - Manages payment methods and funding sources
    - Handles transaction limits and controls
    
    Features:
    - Real-time balance tracking
    - Transaction history integration
    - Security measures (PIN, limits)
    - Multiple funding source support
    - Automatic balance updates
    
    Used for:
    - Paying for orders and services
    - Receiving refunds
    - Managing personal funds
    - Transaction history tracking
    """
    __tablename__ = "user_wallets"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)  # Current wallet balance
    is_active = Column(Boolean, default=True)            # Wallet active status
    is_locked = Column(Boolean, default=False)           # Security lock status
    daily_limit = Column(Float, default=50000.0)        # Daily spending limit
    transaction_pin = Column(String)                     # Encrypted transaction PIN
    last_transaction_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="user_wallet", 
                              foreign_keys="WalletTransaction.user_wallet_id")


class VendorWallet(Base):
    """
    Represents a vendor's wallet for business transactions.
    
    This model manages vendor business funds and earnings:
    - Tracks earnings from orders
    - Manages commission payments
    - Handles withdrawal requests
    - Stores business transaction history
    
    Features:
    - Revenue tracking and analytics
    - Commission management
    - Withdrawal processing
    - Business expense tracking
    - Financial reporting support
    
    Used for:
    - Receiving payments from orders
    - Paying platform commissions
    - Managing business expenses
    - Withdrawing earnings to bank accounts
    """
    __tablename__ = "vendor_wallets"

    id = Column(Integer, primary_key=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)     # Current wallet balance
    pending_balance = Column(Float, nullable=False, default=0.0)  # Pending settlement amount
    is_active = Column(Boolean, default=True)               # Wallet active status
    is_locked = Column(Boolean, default=False)              # Security lock status
    commission_rate = Column(Float, default=0.15)           # Platform commission rate (15%)
    minimum_withdrawal = Column(Float, default=1000.0)      # Minimum withdrawal amount
    last_transaction_at = Column(TIMESTAMP(timezone=True))
    last_settlement_at = Column(TIMESTAMP(timezone=True))   # Last earnings settlement
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="vendor_wallet",
                              foreign_keys="WalletTransaction.vendor_wallet_id")


class RiderWallet(Base):
    """
    Represents a rider's wallet for delivery earnings.
    
    This model manages rider earnings and delivery payments:
    - Tracks delivery fees earned
    - Manages tips and bonuses
    - Handles fuel and expense reimbursements
    - Stores delivery transaction history
    
    Features:
    - Delivery earnings tracking
    - Tips and bonus management
    - Expense reimbursement
    - Performance-based rewards
    - Real-time earning updates
    
    Used for:
    - Receiving delivery fees
    - Getting tips from customers
    - Expense reimbursements
    - Performance bonuses
    - Withdrawing earnings
    """
    __tablename__ = "rider_wallets"

    id = Column(Integer, primary_key=True, nullable=False)
    rider_id = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)     # Current wallet balance
    pending_balance = Column(Float, nullable=False, default=0.0)  # Pending delivery payments
    is_active = Column(Boolean, default=True)               # Wallet active status
    is_locked = Column(Boolean, default=False)              # Security lock status
    delivery_rate = Column(Float, default=500.0)            # Base delivery fee rate
    minimum_withdrawal = Column(Float, default=500.0)       # Minimum withdrawal amount
    last_transaction_at = Column(TIMESTAMP(timezone=True))
    last_settlement_at = Column(TIMESTAMP(timezone=True))   # Last earnings settlement
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    rider = relationship("Rider", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="rider_wallet",
                              foreign_keys="WalletTransaction.rider_wallet_id")


class WalletTransaction(Base):
    """
    Represents individual wallet transactions for all user types.
    
    This model tracks all financial transactions across the platform:
    - Records all wallet activities (deposits, payments, withdrawals)
    - Maintains transaction history and audit trail
    - Links transactions to related entities (orders, refunds, etc.)
    - Provides transaction status tracking
    
    Features:
    - Comprehensive transaction logging
    - Multi-wallet support (user, vendor, rider)
    - Transaction status tracking
    - Reference linking to related entities
    - Audit trail for financial compliance
    
    Transaction Types:
    1. User transactions: Order payments, wallet funding, refunds
    2. Vendor transactions: Order earnings, commission payments, withdrawals
    3. Rider transactions: Delivery earnings, tips, expense reimbursements
    """
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    
    # Wallet References (only one should be set per transaction)
    user_wallet_id = Column(Integer, ForeignKey("user_wallets.id", ondelete="CASCADE"))
    vendor_wallet_id = Column(Integer, ForeignKey("vendor_wallets.id", ondelete="CASCADE"))
    rider_wallet_id = Column(Integer, ForeignKey("rider_wallets.id", ondelete="CASCADE"))
    
    # Transaction Details
    transaction_type = Column(Enum(WalletTransactionType), nullable=False)
    status = Column(Enum(WalletTransactionStatus), default=WalletTransactionStatus.PENDING)
    amount = Column(Float, nullable=False)               # Transaction amount
    balance_before = Column(Float, nullable=False)       # Balance before transaction
    balance_after = Column(Float, nullable=False)        # Balance after transaction
    
    # Transaction Metadata
    description = Column(String, nullable=False)         # Human-readable description
    reference_id = Column(String)                        # External reference (order ID, etc.)
    reference_type = Column(String)                      # Type of reference (order, deposit, etc.)
    
    # Processing Information
    processed_at = Column(TIMESTAMP(timezone=True))      # When transaction was processed
    processor_id = Column(String)                        # Payment processor transaction ID
    
    # Audit Fields
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=datetime.utcnow)

    # Relationships
    user_wallet = relationship("UserWallet", back_populates="transactions",
                             foreign_keys=[user_wallet_id])
    vendor_wallet = relationship("VendorWallet", back_populates="transactions",
                               foreign_keys=[vendor_wallet_id])
    rider_wallet = relationship("RiderWallet", back_populates="transactions",
                              foreign_keys=[rider_wallet_id])


# Configure relationships after all models are defined
# Note: Item.addon_group and ItemAddonGroup.items relationships are now defined in the models above