import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "crowdcargo"

# Collection Names
ORDERS_COLLECTION = "orders"
SHIPPING_PLANS_COLLECTION = "shipping_plans"
USERS_COLLECTION = "users"

# Shipping Plans Configuration
DEFAULT_SHIPPING_PLANS = [
    {
        "name": "India Post SAL",
        "min_weight": 20,
        "max_weight": 30,
        "rate_per_kg": 0.30,
        "delivery_time": "15-20 days",
        "carrier": "India Post"
    },
    {
        "name": "India Post EMS",
        "min_weight": 0,
        "max_weight": 20,
        "rate_per_kg": 2.00,
        "delivery_time": "7-10 days",
        "carrier": "India Post"
    },
    {
        "name": "DHL Express",
        "min_weight": 0,
        "max_weight": 70,
        "rate_per_kg": 4.50,
        "delivery_time": "3-5 days",
        "carrier": "DHL"
    },
    {
        "name": "FedEx Economy",
        "min_weight": 0,
        "max_weight": 68,
        "rate_per_kg": 3.50,
        "delivery_time": "5-7 days",
        "carrier": "FedEx"
    }
]

# Application Settings
APP_TITLE = "CrowdCargo"
APP_DESCRIPTION = "Community-Powered Ordering & Shipping Platform"
DEFAULT_CURRENCY = "EUR"
MIN_ORDER_WEIGHT = 0.1  # Minimum weight for a single item in kg
MAX_ORDER_WEIGHT = 70   # Maximum weight for a single order in kg

# Notification Settings
ENABLE_NOTIFICATIONS = False
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") 