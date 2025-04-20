from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    weight_kg: float
    price: float
    currency: str = "EUR"

class Order(BaseModel):
    order_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    user_id: str
    items: List[OrderItem]
    total_weight_kg: float
    total_price: float
    currency: str = "EUR"
    status: str = "pending"  # pending, processing, shipped, delivered
    shipping_plan: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    shipping_address: Dict[str, str]
    contact_info: Dict[str, str]

    def calculate_totals(self) -> None:
        """Calculate total weight and price of the order."""
        self.total_weight_kg = sum(item.weight_kg * item.quantity for item in self.items)
        self.total_price = sum(item.price * item.quantity for item in self.items)

    def update_status(self, new_status: str) -> None:
        """Update the order status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert the order to a dictionary for MongoDB storage."""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": [item.dict() for item in self.items],
            "total_weight_kg": self.total_weight_kg,
            "total_price": self.total_price,
            "currency": self.currency,
            "status": self.status,
            "shipping_plan": self.shipping_plan,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "shipping_address": self.shipping_address,
            "contact_info": self.contact_info
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Order':
        """Create an Order instance from a dictionary."""
        items = [OrderItem(**item) for item in data.get('items', [])]
        return cls(
            order_id=data.get('order_id'),
            user_id=data.get('user_id'),
            items=items,
            total_weight_kg=data.get('total_weight_kg', 0),
            total_price=data.get('total_price', 0),
            currency=data.get('currency', 'EUR'),
            status=data.get('status', 'pending'),
            shipping_plan=data.get('shipping_plan'),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now()),
            shipping_address=data.get('shipping_address', {}),
            contact_info=data.get('contact_info', {})
        ) 