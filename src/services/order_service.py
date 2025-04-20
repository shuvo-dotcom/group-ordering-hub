from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
from ..models.order import Order, OrderItem
from ..config import ORDERS_COLLECTION, SHIPPING_PLANS_COLLECTION

class OrderService:
    def __init__(self, db):
        self.orders = db[ORDERS_COLLECTION]
        self.shipping_plans = db[SHIPPING_PLANS_COLLECTION]

    def create_order(self, order: Order) -> str:
        """Create a new order in the database."""
        order_dict = order.to_dict()
        result = self.orders.insert_one(order_dict)
        return str(result.inserted_id)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by its ID."""
        order_data = self.orders.find_one({"order_id": order_id})
        if order_data:
            return Order.from_dict(order_data)
        return None

    def get_user_orders(self, user_id: str) -> List[Order]:
        """Retrieve all orders for a specific user."""
        orders_data = self.orders.find({"user_id": user_id})
        return [Order.from_dict(order) for order in orders_data]

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Update the status of an order."""
        result = self.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0

    def get_pending_orders(self) -> List[Order]:
        """Retrieve all pending orders."""
        orders_data = self.orders.find({"status": "pending"})
        return [Order.from_dict(order) for order in orders_data]

    def get_total_pending_weight(self) -> float:
        """Calculate the total weight of all pending orders."""
        pipeline = [
            {"$match": {"status": "pending"}},
            {"$group": {"_id": None, "total_weight": {"$sum": "$total_weight_kg"}}}
        ]
        result = list(self.orders.aggregate(pipeline))
        return result[0]["total_weight"] if result else 0.0

    def get_eligible_shipping_plans(self, total_weight: float) -> List[dict]:
        """Get shipping plans that can accommodate the given weight."""
        return list(self.shipping_plans.find({
            "min_weight": {"$lte": total_weight},
            "max_weight": {"$gte": total_weight}
        }))

    def assign_shipping_plan(self, order_id: str, shipping_plan: str) -> bool:
        """Assign a shipping plan to an order."""
        result = self.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "shipping_plan": shipping_plan,
                    "updated_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0

    def get_orders_by_status(self, status: str) -> List[Order]:
        """Retrieve all orders with a specific status."""
        orders_data = self.orders.find({"status": status})
        return [Order.from_dict(order) for order in orders_data] 