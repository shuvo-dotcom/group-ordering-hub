from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format a number as currency."""
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "INR": "₹"
    }
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def format_weight(weight_kg: float) -> str:
    """Format weight in kilograms."""
    return f"{weight_kg:.2f} kg"

def calculate_shipping_cost(weight_kg: float, rate_per_kg: float) -> float:
    """Calculate shipping cost based on weight and rate."""
    return weight_kg * rate_per_kg

def get_progress_percentage(current: float, target: float) -> float:
    """Calculate progress percentage."""
    if target == 0:
        return 0
    return min(100, (current / target) * 100)

def format_datetime(dt: datetime) -> str:
    """Format datetime in a user-friendly way."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def validate_shipping_address(address: Dict[str, str]) -> bool:
    """Validate shipping address fields."""
    required_fields = ["street", "city", "postal_code", "country"]
    return all(field in address and address[field].strip() for field in required_fields)

def validate_contact_info(contact: Dict[str, str]) -> bool:
    """Validate contact information fields."""
    required_fields = ["name", "email", "phone"]
    return all(field in contact and contact[field].strip() for field in required_fields)

def calculate_estimated_delivery_date(
    shipping_date: datetime,
    delivery_timeframe: str
) -> datetime:
    """Calculate estimated delivery date based on shipping date and timeframe."""
    # Parse delivery timeframe (e.g., "3-5 days")
    try:
        min_days, max_days = map(int, delivery_timeframe.split("-")[0].split())
        avg_days = (min_days + max_days) / 2
        return shipping_date + timedelta(days=avg_days)
    except (ValueError, IndexError):
        return shipping_date + timedelta(days=7)  # Default to 7 days if parsing fails

def format_order_summary(order: Dict[str, Any]) -> str:
    """Format order details into a readable summary."""
    items = "\n".join([
        f"- {item['name']} x{item['quantity']} ({format_weight(item['weight_kg'])})"
        for item in order['items']
    ])
    return f"""
Order ID: {order['order_id']}
Status: {order['status'].title()}
Total Weight: {format_weight(order['total_weight_kg'])}
Total Price: {format_currency(order['total_price'], order['currency'])}
Items:
{items}
Shipping Address: {order['shipping_address']['street']}, {order['shipping_address']['city']}
Created: {format_datetime(order['created_at'])}
    """.strip() 