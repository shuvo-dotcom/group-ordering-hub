import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.order import Order, OrderItem
from src.utils.helpers import format_currency, format_weight, validate_shipping_address, validate_contact_info, format_datetime, format_order_summary
import bcrypt
import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import secrets
import string
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import stats
import json
import random
from PIL import Image
import base64
from pathlib import Path

# Sample products data
SAMPLE_PRODUCTS = [
    {
        "id": "P001",
        "name": "Haldiram's Bhujia",
        "weight_kg": 1.0,
        "price": 5.99,
        "description": "Popular Indian snack"
    },
    {
        "id": "P002",
        "name": "Maggi Noodles",
        "weight_kg": 0.5,
        "price": 3.99,
        "description": "Instant noodles"
    },
    {
        "id": "P003",
        "name": "Tata Tea Premium",
        "weight_kg": 0.25,
        "price": 4.99,
        "description": "Premium Indian tea"
    },
    {
        "id": "P004",
        "name": "MTR Sambar Powder",
        "weight_kg": 0.2,
        "price": 6.99,
        "description": "Authentic sambar mix"
    }
]

def add_to_cart(product_id, quantity):
    """Add a product to the cart with the specified quantity."""
    product = next((p for p in SAMPLE_PRODUCTS if p['id'] == product_id), None)
    if product:
        cart_item = {
            'product_id': product['id'],
            'name': product['name'],
            'quantity': quantity,
            'price': product['price'],
            'weight_kg': product['weight_kg']
        }
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        st.session_state.cart.append(cart_item)

def remove_from_cart(index):
    """Remove an item from the cart at the specified index."""
    if 'cart' in st.session_state and 0 <= index < len(st.session_state.cart):
        st.session_state.cart.pop(index)

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="CrowdCargo",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide the sidebar by default
)

# Add loading spinner function
def show_loading_spinner(message="Loading..."):
    return st.spinner(message)

# Add image paths
ASSETS_DIR = Path("assets/images")
ICONS = {
    "logo": ASSETS_DIR / "logo.png",
    "shopping": ASSETS_DIR / "shopping.png",
    "cart": ASSETS_DIR / "cart.png",
    "tracking": ASSETS_DIR / "tracking.png",
    "shipping": ASSETS_DIR / "shipping.png",
    "product": ASSETS_DIR / "product.png",
    "remove": ASSETS_DIR / "remove.png"
}

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

# Add custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    /* Navigation bar styling */
    .nav-container {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: white;
        padding: 20px;
        margin: 20px auto;
        max-width: 800px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .nav-item {
        margin: 0 15px;
        padding: 8px 20px;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #2c3e50;
        font-weight: 500;
        text-decoration: none;
        border: 1px solid transparent;
    }
    
    .nav-item:hover {
        background-color: #f0f2f6;
        transform: translateY(-2px);
        border-color: #4CAF50;
    }
    
    .nav-item.active {
        background-color: #4CAF50;
        color: white;
        border-color: #4CAF50;
    }
    
    /* Welcome message styling */
    .welcome-message {
        text-align: center;
        margin: 40px 0;
        color: #2c3e50;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        padding: 10px;
        border: 1px solid #ddd;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .how-it-works-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 220px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        text-align: center;
        overflow: hidden;
    }
    .how-it-works-card img {
        width: 80px;
        height: 80px;
        object-fit: contain;
        margin-bottom: 15px;
    }
    .how-it-works-card h4 {
        margin: 10px 0;
        color: #2c3e50;
        font-size: 1.1em;
        line-height: 1.2;
    }
    .how-it-works-card p {
        margin: 0;
        color: #666;
        font-size: 0.9em;
        line-height: 1.4;
        max-width: 100%;
        overflow-wrap: break-word;
        word-wrap: break-word;
        hyphens: auto;
    }
    .product-card {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
    }
    .product-image {
        width: 100px;
        height: 100px;
        object-fit: cover;
        border-radius: 5px;
    }
    .cart-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin: 5px 0;
    }
    .summary-card {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .truck-icon {
        width: 50px;
        height: 50px;
        margin-right: 10px;
        vertical-align: middle;
    }
    .truck-card {
        display: flex;
        align-items: center;
        padding: 15px;
        margin: 10px 0;
        background-color: #f8f9fa;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid #ddd;
    }
    .truck-card:hover {
        background-color: #e9ecef;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .truck-info {
        flex-grow: 1;
    }
    .truck-status {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
    .truck-details {
        margin-top: 20px;
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .back-button {
        margin-bottom: 20px;
    }
    .cart-counter {
        position: absolute;
        top: 0;
        right: 0;
        padding: 10px;
        background-color: #4CAF50;
        color: white;
        border-radius: 50%;
        min-width: 40px;
        text-align: center;
    }
    .truck-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin: 20px 0;
    }
    .truck-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .truck-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .truck-image {
        width: 50px;
        height: 50px;
        margin-bottom: 10px;
    }
    .truck-info {
        font-size: 0.9em;
    }
    .truck-status {
        color: #666;
        margin: 5px 0;
    }
    .progress-bar {
        background-color: #f0f0f0;
        height: 8px;
        border-radius: 4px;
        margin: 5px 0;
    }
    .progress-fill {
        background-color: #4CAF50;
        height: 100%;
        border-radius: 4px;
    }
    .capacity-info {
        font-size: 0.8em;
        color: #666;
    }
    .logout-icon {
        font-size: 24px;
        color: #2c3e50;
        cursor: pointer;
        padding: 10px;
        border-radius: 5px;
        transition: all 0.3s ease;
        background: none;
        border: none;
        display: inline-block;
        position: relative;
        top: 10px;
    }
    .logout-icon:hover {
        color: #ff4b4b;
        transform: scale(1.1);
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    /* Specific style for logout button */
    [data-testid="stButton"] button[aria-label=""] {
        background: none;
        border: none;
        padding: 0;
        margin: 0;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
    }
    [data-testid="stButton"] button[aria-label=""]:hover {
        background: none;
    }
    /* Style for navigation buttons */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    /* Special style for logout button */
    [data-testid="stButton"] button[key="nav_logout"] {
        background-color: transparent;
        color: #2c3e50;
        border: 1px solid #2c3e50;
        transition: all 0.3s ease;
    }
    [data-testid="stButton"] button[key="nav_logout"]:hover {
        background-color: rgba(44, 62, 80, 0.1);
        color: #ff4b4b;
        border-color: #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# JWT Secret Key
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Add this at the top with other constants
SHIPPING_TRUCKS = [
    {
        "truck_id": "TRUCK-001",
        "status": "collecting",
        "current_weight": 1500,
        "max_weight": 2000,
        "items": [
            {"name": "Haldiram's Bhujia", "quantity": 50, "weight": 50},
            {"name": "Lays Magic Masala", "quantity": 100, "weight": 50},
            {"name": "Parle-G Biscuits", "quantity": 200, "weight": 60}
        ],
        "departure_date": datetime.now() + timedelta(days=3),
        "arrival_date": datetime.now() + timedelta(days=10),
        "location": "Mumbai, India",
        "progress": 75
    },
    {
        "truck_id": "TRUCK-002",
        "status": "collecting",
        "current_weight": 1200,
        "max_weight": 2000,
        "items": [
            {"name": "Maggi Noodles", "quantity": 150, "weight": 60},
            {"name": "Kurkure", "quantity": 80, "weight": 40},
            {"name": "Bournvita", "quantity": 50, "weight": 25}
        ],
        "departure_date": datetime.now() + timedelta(days=5),
        "arrival_date": datetime.now() + timedelta(days=12),
        "location": "Delhi, India",
        "progress": 60
    },
    {
        "truck_id": "TRUCK-003",
        "status": "collecting",
        "current_weight": 1800,
        "max_weight": 2000,
        "items": [
            {"name": "Amul Butter", "quantity": 100, "weight": 50},
            {"name": "Britannia Biscuits", "quantity": 150, "weight": 75},
            {"name": "Cadbury Dairy Milk", "quantity": 200, "weight": 100}
        ],
        "departure_date": datetime.now() + timedelta(days=2),
        "arrival_date": datetime.now() + timedelta(days=9),
        "location": "Bangalore, India",
        "progress": 90
    },
    {
        "truck_id": "TRUCK-004",
        "status": "collecting",
        "current_weight": 1600,
        "max_weight": 2000,
        "items": [
            {"name": "Tata Tea", "quantity": 100, "weight": 50},
            {"name": "Nescafe Coffee", "quantity": 80, "weight": 40},
            {"name": "Horlicks", "quantity": 120, "weight": 60}
        ],
        "departure_date": datetime.now() + timedelta(days=4),
        "arrival_date": datetime.now() + timedelta(days=11),
        "location": "Chennai, India",
        "progress": 80
    },
    {
        "truck_id": "TRUCK-005",
        "status": "collecting",
        "current_weight": 1400,
        "max_weight": 2000,
        "items": [
            {"name": "Dabur Honey", "quantity": 60, "weight": 30},
            {"name": "Patanjali Ghee", "quantity": 40, "weight": 20},
            {"name": "Fortune Oil", "quantity": 50, "weight": 25}
        ],
        "departure_date": datetime.now() + timedelta(days=6),
        "arrival_date": datetime.now() + timedelta(days=13),
        "location": "Kolkata, India",
        "progress": 70
    }
]

# Add this after the SHIPPING_TRUCKS definition and before MongoDB connection
SAMPLE_PRODUCTS = [
    {
        "id": "P001",
        "name": "Haldiram's Bhujia",
        "weight_kg": 1.0,
        "price": 5.99,
        "description": "Popular Indian snack"
    },
    {
        "id": "P002",
        "name": "Maggi Noodles",
        "weight_kg": 0.5,
        "price": 3.99,
        "description": "Instant noodles"
    },
    {
        "id": "P003",
        "name": "Tata Tea Premium",
        "weight_kg": 0.25,
        "price": 4.99,
        "description": "Premium Indian tea"
    },
    {
        "id": "P004",
        "name": "MTR Sambar Powder",
        "weight_kg": 0.2,
        "price": 6.99,
        "description": "Authentic sambar mix"
    },
    {
        "id": "P005",
        "name": "Amul Ghee",
        "weight_kg": 1.0,
        "price": 12.99,
        "description": "Pure cow ghee"
    },
    {
        "id": "P006",
        "name": "Britannia Good Day",
        "weight_kg": 0.3,
        "price": 2.99,
        "description": "Butter cookies"
    },
    {
        "id": "P007",
        "name": "MDH Garam Masala",
        "weight_kg": 0.1,
        "price": 3.99,
        "description": "Mixed Indian spices"
    },
    {
        "id": "P008",
        "name": "Lijjat Papad",
        "weight_kg": 0.2,
        "price": 4.99,
        "description": "Crispy Indian papad"
    }
]

# MongoDB connection
@st.cache_resource
def init_mongodb():
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            st.error("MONGO_URI not found in environment variables")
            return None
            
        # Try to connect to MongoDB
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        
        return client
    except pymongo.errors.ServerSelectionTimeoutError as err:
        st.error(f"Could not connect to MongoDB Atlas: {err}")
        st.error("Please check your internet connection and MongoDB Atlas settings")
        return None
    except pymongo.errors.OperationFailure as err:
        st.error(f"Authentication failed: {err}")
        st.error("Please check your MongoDB Atlas credentials")
        return None
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

# Initialize MongoDB connection
client = init_mongodb()
if client:
    try:
        db = client.crowdcargo
        # Test database access
        db.command('ping')
        
        # Initialize collections
        orders_collection = db.orders
        shipping_plans_collection = db.shipping_plans
        users_collection = db.users
        ab_tests_collection = db.ab_tests
        trucks_collection = db.trucks
        
        # Initialize trucks collection if empty
        if trucks_collection.count_documents({}) == 0:
            trucks_collection.insert_many(SHIPPING_TRUCKS)
        
    except Exception as e:
        st.error(f"Failed to initialize database collections: {str(e)}")
        client = None

# Authentication functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

# Add validation functions
def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  # Check for uppercase
        return False
    if not re.search(r'[a-z]', password):  # Check for lowercase
        return False
    if not re.search(r'\d', password):     # Check for digit
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Check for special char
        return False
    return True

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'page' not in st.session_state:
    st.session_state.page = "Home"
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'selected_truck' not in st.session_state:
    st.session_state.selected_truck = None

# Show authentication UI if not logged in
if not st.session_state.user:
    st.markdown("""
    <div style='text-align: center; margin: 40px 0;'>
        <h2 style='color: #2c3e50;'>Welcome to CrowdCargo</h2>
        <p style='color: #666;'>Your Community Shipping Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for Login and Register
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if not validate_email(email):
                st.error("Invalid email format")
            else:
                user = users_collection.find_one({"email": email})
                if user and verify_password(password, user['password']):
                    st.session_state.user = user
                    st.session_state.token = create_token(str(user['_id']))
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        st.markdown("### Create New Account")
        name = st.text_input("Full Name", key="register_name")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        if st.button("Register", key="register_button"):
            if not validate_email(email):
                st.error("Invalid email format")
            elif not validate_password(password):
                st.error("Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif users_collection.find_one({"email": email}):
                st.error("Email already registered")
            else:
                hashed_password = hash_password(password)
                user = {
                    "name": name,
                    "email": email,
                    "password": hashed_password,
                    "role": "user",
                    "created_at": datetime.now(),
                    "email_verified": False,
                    "verification_token": secrets.token_urlsafe(32)
                }
                users_collection.insert_one(user)
                
                # Send verification email
                verification_link = f"{os.getenv('APP_URL', 'http://localhost:8501')}/verify?token={user['verification_token']}"
                send_email(
                    email,
                    "Verify your CrowdCargo account",
                    f"""
                    <html>
                        <body>
                            <h2>Welcome to CrowdCargo!</h2>
                            <p>Please verify your email address by clicking the link below:</p>
                            <p><a href="{verification_link}">Verify Email</a></p>
                            <p>If you did not create an account, please ignore this email.</p>
                        </body>
                    </html>
                    """
                )
                st.success("Registration successful! Please check your email to verify your account.")
    st.stop()

# Main content for logged-in users
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("Logout", key="nav_logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.session_state.page = "Home"
        st.success("Logged out successfully!")
        st.rerun()

with col2:
    st.markdown("""
    <div style='text-align: center; margin: 40px 0;'>
        <h2 style='color: #2c3e50;'>Welcome to CrowdCargo</h2>
        <p style='color: #666;'>Your Community Shipping Platform</p>
    </div>
    """, unsafe_allow_html=True)

# Add navigation button styles
st.markdown("""
<style>
    /* Style for navigation buttons */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# Navigation using Streamlit columns
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    if st.button("Home", key="nav_home"):
        st.session_state.page = "Home"
        st.rerun()
with col2:
    if st.button("Place Order", key="nav_place_order"):
        st.session_state.page = "Place Order"
        st.rerun()
with col3:
    if st.button("My Cart", key="nav_cart"):
        st.session_state.page = "My Cart"
        st.rerun()
with col4:
    if st.button("Share Shipping", key="nav_share"):
        st.session_state.page = "Share Shipping"
        st.rerun()
with col5:
    if st.button("Checkout", key="nav_checkout"):
        st.session_state.page = "Checkout"
        st.rerun()
with col6:
    if st.button("Track Orders", key="nav_track"):
        st.session_state.page = "Track Orders"
        st.rerun()
with col7:
    if st.button("Shipping Status", key="nav_status"):
        st.session_state.page = "Shipping Status"
        st.rerun()

# Add some spacing
st.markdown("<br>", unsafe_allow_html=True)

# Main content based on selected page
if st.session_state.page == "Home":
    
    # Show welcome message and features for logged-in users
    st.markdown(f"""
    <div style='text-align: center;'>
        <h2 style='color: #2c3e50;'>Welcome back, {st.session_state.user['name']}!</h2>
        <p style='font-size: 1.2em;'>Ready to start ordering and sharing shipping costs?</p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works section with proper icons
    st.markdown("### How it works")
    cols = st.columns(4)
    steps = [
        ("Browse Products", "shopping", "Browse our selection of authentic Indian products"),
        ("Add to Cart", "cart", "Select items and add them to your cart"),
        ("Place Order", "tracking", "Complete your order with shipping details"),
        ("Share Shipping", "shipping", "We'll combine orders to reduce costs")
    ]
    
    for col, (title, icon, desc) in zip(cols, steps):
        with col:
            icon_path = ICONS.get(icon)
            if icon_path and icon_path.exists():
                icon_base64 = get_image_base64(icon_path)
                if icon_base64:
                    st.markdown(f"""
                    <div class='how-it-works-card'>
                        <img src='data:image/png;base64,{icon_base64}'/>
                        <h4>{title}</h4>
                        <p>{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)

elif st.session_state.page == "Place Order":
    st.title("Place Your Order")
    
    # Product Selection in 4x4 grid
    st.markdown("### Available Products")
    products_per_row = 4
    rows = [SAMPLE_PRODUCTS[i:i + products_per_row] for i in range(0, len(SAMPLE_PRODUCTS), products_per_row)]
    
    for row in rows:
        cols = st.columns(products_per_row)
        for col, product in zip(cols, row):
            with col:
                st.markdown(f"""
                <div class='product-card' style='padding: 10px; margin: 10px;'>
                    <div style='text-align: center;'>
                        <img src='data:image/png;base64,{get_image_base64(ICONS["product"])}' style='width: 80px; height: 80px; object-fit: contain;'/>
                        <h4>{product['name']}</h4>
                        <p>📦 {format_weight(product['weight_kg'])}</p>
                        <p>💰 {format_currency(product['price'])}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Use Streamlit's native components for quantity and add button
                quantity = st.number_input(
                    "Quantity",
                    min_value=0,
                    max_value=10,
                    key=f"qty_{product['id']}",
                    step=1
                )
                
                if st.button("Add to Cart", key=f"add_{product['id']}"):
                    with show_loading_spinner("Adding to cart..."):
                        if quantity > 0:
                            add_to_cart(product['id'], quantity)
                            st.success(f"Added {quantity} {product['name']} to cart!")
                        else:
                            st.warning("Please select a quantity greater than 0")

elif st.session_state.page == "My Cart":
    st.title("My Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is empty. Add some products!")
    else:
        total_weight = sum(item['weight_kg'] * item['quantity'] for item in st.session_state.cart)
        total_price = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
        
        for i, item in enumerate(st.session_state.cart):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class='cart-item'>
                        <div>
                            <h4>{item['name']}</h4>
                            <p>Quantity: {item['quantity']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<p style='text-align: right;'>{format_currency(item['price'] * item['quantity'])}</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("❌ Remove", key=f"remove_{i}"):
                        with show_loading_spinner("Removing item..."):
                            remove_from_cart(i)
                            st.rerun()
        
        st.markdown(f"""
        <div class='summary-card'>
            <h4>Order Summary</h4>
            <p>Total Weight: {format_weight(total_weight)}</p>
            <p>Total Price: {format_currency(total_price)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add buttons for checkout and share shipping
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Proceed to Checkout"):
                with show_loading_spinner("Redirecting to checkout..."):
                    st.session_state.page = "Checkout"
                    st.rerun()
        with col2:
            if st.button("Share Shipping"):
                with show_loading_spinner("Redirecting to share shipping..."):
                    st.session_state.page = "Share Shipping"
                    st.rerun()

elif st.session_state.page == "Share Shipping":
    st.title("Share Shipping")
    
    # Initialize session state
    if 'selected_truck' not in st.session_state:
        st.session_state.selected_truck = None
    
    # If a truck is selected, show its details
    if st.session_state.selected_truck:
        truck = trucks_collection.find_one({"truck_id": st.session_state.selected_truck})
        if truck:
            # Back button at the top
            if st.button("← Back to Truck List"):
                st.session_state.selected_truck = None
                st.rerun()
            
            st.markdown(f"""
            <div class='truck-details'>
                <h3>Truck {truck['truck_id']}</h3>
                <div style='display: flex; gap: 20px; margin: 20px 0;'>
                    <div style='flex: 2;'>
                        <p><strong>Status:</strong> {truck['status'].title()}</p>
                        <p><strong>Location:</strong> {truck['location']}</p>
                        <p><strong>Destination:</strong> {truck.get('destination', 'New York, USA')}</p>
                        <p><strong>Departure:</strong> {format_datetime(truck['departure_date'])}</p>
                        <p><strong>Arrival:</strong> {format_datetime(truck['arrival_date'])}</p>
                    </div>
                    <div style='flex: 1;'>
                        <p><strong>Weight Progress:</strong></p>
                        <div style='background-color: #f0f0f0; height: 20px; border-radius: 10px; margin: 10px 0;'>
                            <div style='background-color: #4CAF50; width: {(truck['current_weight'] / truck['max_weight']) * 100}%; height: 100%; border-radius: 10px;'></div>
                        </div>
                        <p>{format_weight(truck['current_weight'])} / {format_weight(truck['max_weight'])}</p>
                        <p><strong>Remaining Capacity:</strong> {format_weight(truck['max_weight'] - truck['current_weight'])}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Items table
            st.markdown("#### Items in Truck")
            items_df = pd.DataFrame(truck['items'])
            st.dataframe(items_df, hide_index=True)
            
            # Add to truck button if there's enough space and user has items in cart
            if st.session_state.cart:
                total_weight = sum(item['weight_kg'] * item['quantity'] for item in st.session_state.cart)
                if truck['max_weight'] - truck['current_weight'] >= total_weight:
                    if st.button(f"Add Your Items to Truck {truck['truck_id']}"):
                        with show_loading_spinner("Adding to truck..."):
                            try:
                                # Create new items list with cart items
                                new_items = truck['items'].copy()
                                cart_items = []
                                total_price = 0
                                
                                for item in st.session_state.cart:
                                    new_items.append({
                                        "name": item['name'],
                                        "quantity": item['quantity'],
                                        "weight": item['weight_kg'] * item['quantity']
                                    })
                                    cart_items.append({
                                        "product_id": item['product_id'],
                                        "name": item['name'],
                                        "quantity": item['quantity'],
                                        "price": item['price'],
                                        "weight_kg": item['weight_kg']
                                    })
                                    total_price += item['price'] * item['quantity']
                                
                                # Update the truck in MongoDB
                                trucks_collection.update_one(
                                    {"truck_id": truck['truck_id']},
                                    {
                                        "$set": {
                                            "items": new_items,
                                            "current_weight": truck['current_weight'] + total_weight
                                        }
                                    }
                                )
                                
                                # Create a pending order for shared shipping
                                order = Order(
                                    order_id=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                    user_id=str(st.session_state.user['_id']),  # Convert ObjectId to string
                                    items=[OrderItem(
                                        product_id=item['product_id'],
                                        name=item['name'],
                                        quantity=item['quantity'],
                                        price=item['price'],
                                        weight_kg=item['weight_kg']
                                    ) for item in cart_items],
                                    total_price=total_price,
                                    total_weight_kg=total_weight,
                                    status="pending",
                                    contact_info={
                                        "name": st.session_state.user['name'],
                                        "email": st.session_state.user['email'],
                                        "phone": st.session_state.user.get('phone', '')
                                    },
                                    shipping_address={
                                        "street": st.session_state.user.get('address', {}).get('street', ''),
                                        "city": st.session_state.user.get('address', {}).get('city', ''),
                                        "state": st.session_state.user.get('address', {}).get('state', ''),
                                        "postal_code": st.session_state.user.get('address', {}).get('postal_code', ''),
                                        "country": st.session_state.user.get('address', {}).get('country', '')
                                    },
                                    payment_method="shared_shipping",
                                    created_at=datetime.now(),
                                    truck_id=truck['truck_id']
                                )
                                
                                # Save order to database
                                orders_collection.insert_one(order.to_dict())
                                
                                st.success("Added to truck successfully! Please proceed to checkout to complete your shared shipping payment.")
                                st.session_state.cart = []  # Clear cart
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to add to truck: {str(e)}")
                else:
                    st.warning(f"Not enough space in this truck. Available space: {format_weight(truck['max_weight'] - truck['current_weight'])}")
            
            # Admin approval section
            if st.session_state.user.get('role') == 'admin':
                if truck['current_weight'] >= truck['max_weight']:
                    if st.button(f"Approve Truck {truck['truck_id']} for Shipping"):
                        trucks_collection.update_one(
                            {"truck_id": truck['truck_id']},
                            {"$set": {"status": "approved"}}
                        )
                        st.success(f"Truck {truck['truck_id']} approved for shipping!")
                else:
                    st.info(f"Truck needs {format_weight(truck['max_weight'] - truck['current_weight'])} more to be ready for shipping")
    
    # If no truck is selected, show the grid of trucks
    else:
        st.markdown("### Available Shipping Trucks")
        
        # Create columns for the grid
        cols = st.columns(4)
        
        # Get all trucks from MongoDB
        trucks = list(trucks_collection.find())
        
        for i, truck in enumerate(trucks):
            # Calculate remaining capacity and progress
            remaining_capacity = truck['max_weight'] - truck['current_weight']
            progress_percent = (truck['current_weight'] / truck['max_weight']) * 100
            
            # Determine which column to use
            col = cols[i % 4]
            
            with col:
                # Create a container for the truck card
                container = st.container()
                with container:
                    st.markdown(f"""
                    <div class='truck-card'>
                        <img src='data:image/png;base64,{get_image_base64(ICONS["shipping"])}' class='truck-image'/>
                        <div class='truck-info'>
                            <h4>Truck {truck['truck_id']}</h4>
                            <p class='truck-status'><strong>Status:</strong> {truck['status'].title()}</p>
                            <p class='truck-status'><strong>From:</strong> {truck['location']}</p>
                            <p class='truck-status'><strong>To:</strong> {truck.get('destination', 'New York, USA')}</p>
                            <div class='progress-bar'>
                                <div class='progress-fill' style='width: {progress_percent}%'></div>
                            </div>
                            <p class='capacity-info'>{format_weight(remaining_capacity)} left</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add a button for click handling
                    if st.button("View Details", key=f"select_{truck['truck_id']}"):
                        st.session_state.selected_truck = truck['truck_id']
                        st.rerun()

elif st.session_state.page == "Checkout":
    st.title("Checkout")
    
    # Get all pending orders for the user
    pending_orders = list(orders_collection.find({
        "user_id": str(st.session_state.user['_id']),  # Convert ObjectId to string for query
        "status": "pending"
    }))
    
    if not pending_orders and not st.session_state.cart:
        st.warning("You have no items to checkout. Please add items to your cart or join a shared shipping.")
        with show_loading_spinner("Redirecting..."):
            st.session_state.page = "Place Order"
            st.rerun()
    
    # Show pending orders from shared shipping
    for order in pending_orders:
        with st.expander(f"Order {order['order_id']} - Shared Shipping", expanded=True):
            st.markdown(f"""
            <div class='card'>
                <h3>Order Details</h3>
                <p><strong>Status:</strong> {order['status'].title()}</p>
                <p><strong>Total Weight:</strong> {format_weight(order['total_weight_kg'])}</p>
                <p><strong>Total Price:</strong> {format_currency(order['total_price'])}</p>
                <p><strong>Shipping Method:</strong> Shared Shipping (Truck {order.get('truck_id', 'N/A')})</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Items table
            st.markdown("#### Items")
            items_df = pd.DataFrame([
                {
                    "Name": item['name'],
                    "Quantity": item['quantity'],
                    "Price": format_currency(item['price']),
                    "Total": format_currency(item['price'] * item['quantity'])
                }
                for item in order['items']
            ])
            st.dataframe(items_df, hide_index=True)
            
            # Payment button for shared shipping
            if st.button(f"Pay for Shared Shipping - {format_currency(order['total_price'])}", key=f"pay_{order['order_id']}"):
                with show_loading_spinner("Processing payment..."):
                    try:
                        # Update order status
                        orders_collection.update_one(
                            {"order_id": order['order_id']},
                            {"$set": {"status": "paid"}}
                        )
                        st.success("Payment successful! Your items will be shipped with the shared truck.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Payment failed: {str(e)}")
    
    # Show regular cart items if any
    if st.session_state.cart:
        st.markdown("### Your Cart Items")
        total_weight = sum(item['weight_kg'] * item['quantity'] for item in st.session_state.cart)
        total_price = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
        
        for i, item in enumerate(st.session_state.cart):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class='cart-item'>
                        <div>
                            <h4>{item['name']}</h4>
                            <p>Quantity: {item['quantity']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<p style='text-align: right;'>{format_currency(item['price'] * item['quantity'])}</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("❌ Remove", key=f"remove_{i}"):
                        with show_loading_spinner("Removing item..."):
                            remove_from_cart(i)
                            st.rerun()
        
        st.markdown(f"""
        <div class='summary-card'>
            <h4>Order Summary</h4>
            <p>Total Weight: {format_weight(total_weight)}</p>
            <p>Total Price: {format_currency(total_price)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Payment form for regular cart items
        with st.form("checkout_form"):
            st.markdown("#### Payment Information")
            payment_method = st.selectbox(
                "Payment Method",
                ["Credit Card", "Debit Card", "PayPal"]
            )
            
            if st.form_submit_button("Place Order"):
                with show_loading_spinner("Processing your order..."):
                    try:
                        # Create order object
                        order = Order(
                            order_id=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            user_id=str(st.session_state.user['_id']),
                            items=[OrderItem(
                                product_id=item['product_id'],
                                name=item['name'],
                                quantity=item['quantity'],
                                price=item['price'],
                                weight_kg=item['weight_kg']
                            ) for item in st.session_state.cart],
                            total_price=total_price,
                            total_weight_kg=total_weight,
                            status="paid",
                            contact_info={
                                "name": st.session_state.user['name'],
                                "email": st.session_state.user['email'],
                                "phone": st.session_state.user.get('phone', '')
                            },
                            shipping_address={
                                "street": st.session_state.user.get('address', {}).get('street', ''),
                                "city": st.session_state.user.get('address', {}).get('city', ''),
                                "state": st.session_state.user.get('address', {}).get('state', ''),
                                "postal_code": st.session_state.user.get('address', {}).get('postal_code', ''),
                                "country": st.session_state.user.get('address', {}).get('country', '')
                            },
                            payment_method=payment_method,
                            created_at=datetime.now()
                        )
                        
                        # Save order to database
                        orders_collection.insert_one(order.to_dict())
                        send_order_confirmation(order, st.session_state.user['email'])
                        st.success("Order placed successfully! A confirmation email has been sent.")
                        st.session_state.cart = []  # Clear cart
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to place order: {str(e)}")

elif st.session_state.page == "Track Orders":
    st.title("Track Your Orders")
    
    # Search section with tracking icon
    st.markdown("### Search Order")
    search_id = st.text_input("Enter Order ID")
    
    if search_id:
        try:
            order_data = orders_collection.find_one({"order_id": search_id})
            if order_data:
                order = Order.from_dict(order_data)
                with st.container():
                    st.markdown(f"""
                    <div class='card'>
                        <h3>Order Details</h3>
                        <p><strong>Status:</strong> {order.status.title()}</p>
                        <p><strong>Created:</strong> {format_datetime(order.created_at)}</p>
                        <p><strong>Total:</strong> {format_currency(order.total_price)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Order not found. Please check the Order ID.")
        except Exception as e:
            st.error(f"Error retrieving order: {str(e)}")

elif st.session_state.page == "Shipping Status":
    st.title("Shipping Status")
    
    # Active Shipping Plans with cards
    st.markdown("### Active Shipping Plans")
    try:
        active_plans = list(shipping_plans_collection.find({
            "status": {"$in": ["pending", "processing", "in_transit"]}
        }).sort("departure_date", 1))
        
        if active_plans:
            for plan in active_plans:
                with st.expander(f"Plan {plan['plan_id']} - {plan['status'].title()}", expanded=True):
                    st.markdown(f"""
                    <div class='card'>
                        <p><strong>Status:</strong> {plan['status'].title()}</p>
                        <p><strong>Departure:</strong> {format_datetime(plan['departure_date'])}</p>
                        <p><strong>Arrival:</strong> {format_datetime(plan['arrival_date'])}</p>
                        <p><strong>Capacity:</strong> {format_weight(plan['capacity_kg'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active shipping plans at the moment.")
    except Exception as e:
        st.error(f"Error retrieving shipping plans: {str(e)}")

elif st.session_state.page == "Admin Dashboard":
    if st.session_state.user.get('role') != 'admin':
        st.error("You don't have permission to access this page.")
        st.stop()
    
    st.header("Admin Dashboard")
    
    # Analytics Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Overview", "Advanced Analytics", "Forecasting", "User Activity", "A/B Testing", "Customer Segmentation"])
    
    with tab1:
        # Analytics Overview
        st.subheader("Analytics Overview")
        
        # Order Analytics
        order_analytics = get_order_analytics()
        if order_analytics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Orders", order_analytics['total_orders'])
            with col2:
                st.metric("Total Revenue", format_currency(order_analytics['total_revenue']))
            with col3:
                st.metric("Average Order Value", format_currency(order_analytics['avg_order_value']))
            with col4:
                st.metric("Total Weight Shipped", format_weight(order_analytics['total_weight']))
            
            # Status Distribution Chart
            st.subheader("Order Status Distribution")
            fig = px.pie(
                values=order_analytics['status_counts'].values,
                names=order_analytics['status_counts'].index,
                title="Order Status Distribution"
            )
            st.plotly_chart(fig)
            
            # Daily Orders Chart
            st.subheader("Daily Orders")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=order_analytics['daily_orders'].index,
                y=order_analytics['daily_orders'].values,
                name="Number of Orders"
            ))
            fig.add_trace(go.Scatter(
                x=order_analytics['daily_revenue'].index,
                y=order_analytics['daily_revenue'].values,
                name="Daily Revenue",
                yaxis="y2"
            ))
            fig.update_layout(
                title="Daily Orders and Revenue",
                yaxis=dict(title="Number of Orders"),
                yaxis2=dict(title="Revenue", overlaying="y", side="right")
            )
            st.plotly_chart(fig)
        
        # User Analytics
        user_analytics = get_user_analytics()
        if user_analytics:
            st.subheader("User Analytics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", user_analytics['total_users'])
            with col2:
                st.metric("Verified Users", user_analytics['verified_users'])
            with col3:
                st.metric("Admin Users", user_analytics['admin_users'])
            
            # Daily Signups Chart
            st.subheader("Daily User Signups")
            fig = px.line(
                x=user_analytics['daily_signups'].index,
                y=user_analytics['daily_signups'].values,
                title="Daily User Signups"
            )
            st.plotly_chart(fig)
        
        # Recent Orders Table
        st.subheader("Recent Orders")
        try:
            recent_orders = list(orders_collection.find().sort("created_at", -1).limit(10))
            if recent_orders:
                orders_df = pd.DataFrame([
                    {
                        "Order ID": order['order_id'],
                        "User": order['contact_info']['name'],
                        "Status": order['status'],
                        "Total": format_currency(order['total_price']),
                        "Created": format_datetime(order['created_at'])
                    }
                    for order in recent_orders
                ])
                st.dataframe(orders_df, hide_index=True)
            else:
                st.info("No orders found.")
        except Exception as e:
            st.error(f"Error retrieving orders: {str(e)}")
        
        # User Management
        st.subheader("User Management")
        try:
            users = list(users_collection.find().sort("created_at", -1))
            if users:
                users_df = pd.DataFrame([
                    {
                        "Name": user['name'],
                        "Email": user['email'],
                        "Role": user['role'],
                        "Verified": user.get('email_verified', False),
                        "Created": format_datetime(user['created_at'])
                    }
                    for user in users
                ])
                st.dataframe(users_df, hide_index=True)
                
                # Role Management
                selected_email = st.selectbox("Select User", [user['email'] for user in users])
                new_role = st.selectbox("New Role", ["user", "admin"])
                if st.button("Update Role"):
                    users_collection.update_one(
                        {"email": selected_email},
                        {"$set": {"role": new_role}}
                    )
                    st.success("Role updated successfully!")
                    st.rerun()
            else:
                st.info("No users found.")
        except Exception as e:
            st.error(f"Error retrieving users: {str(e)}")
    
    with tab2:
        st.header("Advanced Analytics")
        analytics = get_advanced_order_analytics()
        
        if analytics:
            # Daily Metrics
            st.subheader("Daily Order Metrics")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=analytics['daily_metrics']['date'],
                y=analytics['daily_metrics'][('total_price', 'sum')],
                name="Daily Revenue"
            ))
            fig.add_trace(go.Scatter(
                x=analytics['daily_metrics']['date'],
                y=analytics['daily_metrics'][('total_price', 'mean')],
                name="Average Order Value"
            ))
            fig.update_layout(title="Daily Revenue and Average Order Value")
            st.plotly_chart(fig)
            
            # Hourly Distribution
            st.subheader("Hourly Order Distribution")
            fig = px.bar(
                analytics['hourly_metrics'],
                x='hour',
                y='order_id',
                title="Orders by Hour of Day"
            )
            st.plotly_chart(fig)
            
            # Weekday Analysis
            st.subheader("Weekday Analysis")
            fig = px.bar(
                analytics['weekday_metrics'],
                x='day_of_week',
                y='order_id',
                title="Orders by Day of Week"
            )
            st.plotly_chart(fig)
            
            # Product Popularity
            st.subheader("Product Popularity")
            fig = px.bar(
                analytics['product_popularity'],
                x='name',
                y='quantity',
                title="Most Popular Products"
            )
            st.plotly_chart(fig)
    
    with tab3:
        st.header("Order Forecasting")
        analytics = get_advanced_order_analytics()
        
        if analytics:
            # Model selection
            model_type = st.selectbox(
                "Select Forecasting Model",
                ["Holt-Winters", "ARIMA", "SARIMA"]
            )
            
            if model_type == "Holt-Winters":
                forecast = forecast_orders(analytics['orders_df'])
            elif model_type == "ARIMA":
                forecast = forecast_with_arima(analytics['orders_df'])
            else:
                forecast = forecast_with_sarima(analytics['orders_df'])
            
            if forecast:
                # Plot historical data and forecast
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=analytics['orders_df']['date'].unique(),
                    y=analytics['orders_df'].groupby('date').size(),
                    name="Historical Orders"
                ))
                
                # Forecast
                forecast_dates = pd.date_range(
                    start=forecast['last_date'] + timedelta(days=1),
                    periods=len(forecast['forecast']),
                    freq='D'
                )
                
                fig.add_trace(go.Scatter(
                    x=forecast_dates,
                    y=forecast['forecast'],
                    name="Forecast",
                    line=dict(dash='dash')
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast_dates,
                    y=forecast['upper_bound'],
                    name="Upper Bound",
                    line=dict(dash='dot'),
                    opacity=0.3
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_dates,
                    y=forecast['lower_bound'],
                    name="Lower Bound",
                    line=dict(dash='dot'),
                    opacity=0.3,
                    fill='tonexty'
                ))
                
                fig.update_layout(
                    title="Order Forecast with 95% Confidence Interval",
                    xaxis_title="Date",
                    yaxis_title="Number of Orders"
                )
                st.plotly_chart(fig)
                
                # Model comparison
                st.subheader("Model Comparison")
                models = {
                    "Holt-Winters": forecast_orders(analytics['orders_df']),
                    "ARIMA": forecast_with_arima(analytics['orders_df']),
                    "SARIMA": forecast_with_sarima(analytics['orders_df'])
                }
                
                comparison_data = []
                for model_name, model_forecast in models.items():
                    if model_forecast:
                        comparison_data.append({
                            "Model": model_name,
                            "Mean Forecast": model_forecast['forecast'].mean(),
                            "Confidence Range": f"{model_forecast['lower_bound'].mean():.1f} - {model_forecast['upper_bound'].mean():.1f}"
                        })
                
                if comparison_data:
                    st.dataframe(pd.DataFrame(comparison_data))
    
    with tab4:
        st.header("User Activity Tracking")
        
        # Select user
        users = list(users_collection.find())
        selected_email = st.selectbox("Select User", [user['email'] for user in users])
        selected_user = next(user for user in users if user['email'] == selected_email)
        
        activity = track_user_activity(selected_user['_id'])
        
        if activity:
            # User metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Orders", activity['total_orders'])
            with col2:
                st.metric("Total Spent", format_currency(activity['total_spent']))
            with col3:
                st.metric("Average Order Value", format_currency(activity['avg_order_value']))
            
            # Login history
            st.subheader("Login History")
            if activity['login_history']:
                login_df = pd.DataFrame(activity['login_history'])
                st.dataframe(login_df, hide_index=True)
            else:
                st.info("No login history available")
            
            # Recent orders
            st.subheader("Recent Orders")
            if activity['recent_orders']:
                for order in activity['recent_orders']:
                    with st.expander(f"Order {order['order_id']} - {order['status'].title()}"):
                        st.write(format_order_summary(order))
            else:
                st.info("No recent orders")
            
            # Time between orders
            if activity['avg_time_between_orders']:
                st.subheader("Order Frequency")
                st.write(f"Average time between orders: {activity['avg_time_between_orders'].days} days")

    with tab5:
        st.header("A/B Testing")
        
        # Create new test
        with st.expander("Create New A/B Test"):
            test_name = st.text_input("Test Name")
            variants = st.text_area("Variants (one per line)").split('\n')
            target_metric = st.selectbox(
                "Target Metric",
                ["order_value", "conversion_rate", "user_engagement"]
            )
            duration_days = st.number_input("Test Duration (days)", min_value=1, value=14)
            
            if st.button("Create Test"):
                test = create_ab_test(test_name, variants, target_metric, duration_days)
                if test:
                    st.success(f"Test '{test_name}' created successfully!")
        
        # View active tests
        st.subheader("Active Tests")
        active_tests = list(ab_tests_collection.find({"status": "active"}))
        if active_tests:
            for test in active_tests:
                with st.expander(f"Test: {test['name']}"):
                    st.write(f"Target Metric: {test['target_metric']}")
                    st.write(f"Duration: {(test['end_date'] - test['start_date']).days} days")
                    st.write("Variants:")
                    for variant in test['variants']:
                        st.write(f"- {variant}")
                    
                    # Test results
                    if 'results' in test:
                        st.write("Current Results:")
                        st.write(test['results'])
        else:
            st.info("No active A/B tests")
    
    with tab6:
        st.header("Customer Segmentation")
        
        segments = segment_customers(analytics['orders_df'])
        if segments is not None:
            # Segment distribution
            st.subheader("Segment Distribution")
            fig = px.pie(
                segments,
                names='segment_name',
                title="Customer Segments"
            )
            st.plotly_chart(fig)
            
            # Segment characteristics
            st.subheader("Segment Characteristics")
            segment_stats = segments.groupby('segment_name').agg({
                'total_spent': 'mean',
                'avg_order_value': 'mean',
                'order_count': 'mean'
            }).reset_index()
            
            st.dataframe(segment_stats)
            
            # Customer list by segment
            st.subheader("Customers by Segment")
            selected_segment = st.selectbox(
                "Select Segment",
                segments['segment_name'].unique()
            )
            
            segment_customers = segments[segments['segment_name'] == selected_segment]
            st.dataframe(segment_customers)
            
            # Segment-specific recommendations
            st.subheader("Segment-Specific Recommendations")
            if selected_segment == "High-Value Frequent Buyers":
                st.write("Recommendations:")
                st.write("- Offer loyalty rewards")
                st.write("- Provide early access to new products")
                st.write("- Create personalized bundles")
            elif selected_segment == "Medium-Value Regular Buyers":
                st.write("Recommendations:")
                st.write("- Implement volume discounts")
                st.write("- Offer subscription options")
                st.write("- Send personalized recommendations")
            elif selected_segment == "Low-Value Occasional Buyers":
                st.write("Recommendations:")
                st.write("- Send re-engagement emails")
                st.write("- Offer first-time buyer discounts")
                st.write("- Provide product education content")
            else:  # New/Inactive Customers
                st.write("Recommendations:")
                st.write("- Send welcome series")
                st.write("- Offer sign-up bonuses")
                st.write("- Provide onboarding guidance")

# Footer
st.markdown("---")
st.markdown("© 2024 CrowdCargo - Community-Powered Ordering & Shipping Platform")

# Update the order placement to send confirmation email
def place_order(order: Order):
    try:
        orders_collection.insert_one(order.to_dict())
        send_order_confirmation(order, st.session_state.user['email'])
        st.success("Order placed successfully! A confirmation email has been sent.")
        st.session_state.cart = []  # Clear cart
    except Exception as e:
        st.error(f"Failed to place order: {str(e)}")

# Update the order status change to send notification
def update_order_status(order_id: str, new_status: str):
    try:
        orders_collection.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now()
                }
            }
        )
        order = Order.from_dict(orders_collection.find_one({"order_id": order_id}))
        send_status_update(order, order.contact_info['email'])
        st.success("Status updated successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to update status: {str(e)}")

# Analytics functions
def get_order_analytics():
    try:
        # Get all orders
        orders = list(orders_collection.find())
        
        # Convert to DataFrame for analysis
        orders_df = pd.DataFrame([
            {
                'order_id': order['order_id'],
                'status': order['status'],
                'total_price': order['total_price'],
                'total_weight': order['total_weight_kg'],
                'created_at': order['created_at'],
                'user_id': order['user_id']
            }
            for order in orders
        ])
        
        # Calculate metrics
        total_orders = len(orders_df)
        total_revenue = orders_df['total_price'].sum()
        avg_order_value = orders_df['total_price'].mean()
        total_weight = orders_df['total_weight_kg'].sum()
        
        # Status distribution
        status_counts = orders_df['status'].value_counts()
        
        # Time-based analysis
        orders_df['date'] = pd.to_datetime(orders_df['created_at']).dt.date
        daily_orders = orders_df.groupby('date').size()
        daily_revenue = orders_df.groupby('date')['total_price'].sum()
        
        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'total_weight': total_weight,
            'status_counts': status_counts,
            'daily_orders': daily_orders,
            'daily_revenue': daily_revenue
        }
    except Exception as e:
        st.error(f"Error calculating analytics: {str(e)}")
        return None

def get_user_analytics():
    try:
        # Get all users
        users = list(users_collection.find())
        
        # Convert to DataFrame
        users_df = pd.DataFrame([
            {
                'user_id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'],
                'email_verified': user.get('email_verified', False)
            }
            for user in users
        ])
        
        # Calculate metrics
        total_users = len(users_df)
        verified_users = users_df['email_verified'].sum()
        admin_users = (users_df['role'] == 'admin').sum()
        
        # Time-based analysis
        users_df['date'] = pd.to_datetime(users_df['created_at']).dt.date
        daily_signups = users_df.groupby('date').size()
        
        return {
            'total_users': total_users,
            'verified_users': verified_users,
            'admin_users': admin_users,
            'daily_signups': daily_signups
        }
    except Exception as e:
        st.error(f"Error calculating user analytics: {str(e)}")
        return None

# Advanced Analytics functions
def get_advanced_order_analytics():
    try:
        # Get all orders
        orders = list(orders_collection.find())
        
        # Convert to DataFrame
        orders_df = pd.DataFrame([
            {
                'order_id': order['order_id'],
                'status': order['status'],
                'total_price': order['total_price'],
                'total_weight': order['total_weight_kg'],
                'created_at': order['created_at'],
                'user_id': order['user_id'],
                'items': order['items']
            }
            for order in orders
        ])
        
        # Time-based analysis
        orders_df['date'] = pd.to_datetime(orders_df['created_at']).dt.date
        orders_df['hour'] = pd.to_datetime(orders_df['created_at']).dt.hour
        orders_df['day_of_week'] = pd.to_datetime(orders_df['created_at']).dt.day_name()
        
        # Product analysis
        all_items = []
        for items in orders_df['items']:
            for item in items:
                all_items.append({
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': item['price']
                })
        items_df = pd.DataFrame(all_items)
        
        # Calculate metrics
        daily_metrics = orders_df.groupby('date').agg({
            'total_price': ['sum', 'mean', 'count'],
            'total_weight': 'sum'
        }).reset_index()
        
        hourly_metrics = orders_df.groupby('hour').agg({
            'order_id': 'count',
            'total_price': 'sum'
        }).reset_index()
        
        weekday_metrics = orders_df.groupby('day_of_week').agg({
            'order_id': 'count',
            'total_price': 'sum'
        }).reset_index()
        
        # Product popularity
        product_popularity = items_df.groupby('name').agg({
            'quantity': 'sum',
            'price': 'mean'
        }).reset_index()
        
        return {
            'daily_metrics': daily_metrics,
            'hourly_metrics': hourly_metrics,
            'weekday_metrics': weekday_metrics,
            'product_popularity': product_popularity,
            'orders_df': orders_df
        }
    except Exception as e:
        st.error(f"Error calculating advanced analytics: {str(e)}")
        return None

def forecast_orders(orders_df, days_to_forecast=30):
    try:
        # Prepare time series data
        daily_orders = orders_df.groupby('date')['order_id'].count()
        daily_orders = daily_orders.asfreq('D', fill_value=0)
        
        # Fit Holt-Winters model
        model = ExponentialSmoothing(
            daily_orders,
            seasonal_periods=7,
            trend='add',
            seasonal='add'
        ).fit()
        
        # Generate forecast
        forecast = model.forecast(days_to_forecast)
        
        # Calculate confidence intervals
        residuals = model.resid
        std_resid = np.std(residuals)
        z_score = stats.norm.ppf(0.975)  # 95% confidence interval
        
        lower_bound = forecast - z_score * std_resid
        upper_bound = forecast + z_score * std_resid
        
        return {
            'forecast': forecast,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'last_date': daily_orders.index[-1]
        }
    except Exception as e:
        st.error(f"Error generating forecast: {str(e)}")
        return None

def forecast_with_arima(orders_df, days_to_forecast=30):
    try:
        daily_orders = orders_df.groupby('date')['order_id'].count()
        daily_orders = daily_orders.asfreq('D', fill_value=0)
        
        # Fit ARIMA model
        model = ARIMA(daily_orders, order=(1, 1, 1))
        model_fit = model.fit()
        
        # Generate forecast
        forecast = model_fit.forecast(days_to_forecast)
        
        # Calculate confidence intervals
        conf_int = model_fit.get_forecast(days_to_forecast).conf_int()
        
        return {
            'forecast': forecast,
            'lower_bound': conf_int.iloc[:, 0],
            'upper_bound': conf_int.iloc[:, 1],
            'last_date': daily_orders.index[-1]
        }
    except Exception as e:
        st.error(f"Error with ARIMA forecast: {str(e)}")
        return None

def forecast_with_sarima(orders_df, days_to_forecast=30):
    try:
        daily_orders = orders_df.groupby('date')['order_id'].count()
        daily_orders = daily_orders.asfreq('D', fill_value=0)
        
        # Fit SARIMA model
        model = SARIMAX(daily_orders, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
        model_fit = model.fit()
        
        # Generate forecast
        forecast = model_fit.forecast(days_to_forecast)
        
        # Calculate confidence intervals
        conf_int = model_fit.get_forecast(days_to_forecast).conf_int()
        
        return {
            'forecast': forecast,
            'lower_bound': conf_int.iloc[:, 0],
            'upper_bound': conf_int.iloc[:, 1],
            'last_date': daily_orders.index[-1]
        }
    except Exception as e:
        st.error(f"Error with SARIMA forecast: {str(e)}")
        return None

def segment_customers(orders_df):
    try:
        # Prepare customer features
        customer_features = orders_df.groupby('user_id').agg({
            'total_price': ['sum', 'mean', 'count'],
            'total_weight': 'sum'
        }).reset_index()
        
        # Rename columns
        customer_features.columns = ['user_id', 'total_spent', 'avg_order_value', 'order_count', 'total_weight']
        
        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(customer_features[['total_spent', 'avg_order_value', 'order_count']])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=4, random_state=42)
        customer_features['segment'] = kmeans.fit_predict(features_scaled)
        
        # Define segment names based on characteristics
        segment_names = {
            0: 'High-Value Frequent Buyers',
            1: 'Medium-Value Regular Buyers',
            2: 'Low-Value Occasional Buyers',
            3: 'New/Inactive Customers'
        }
        
        customer_features['segment_name'] = customer_features['segment'].map(segment_names)
        
        return customer_features
    except Exception as e:
        st.error(f"Error in customer segmentation: {str(e)}")
        return None

def create_ab_test(test_name, variants, target_metric, duration_days):
    try:
        test = {
            'test_id': f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'name': test_name,
            'variants': variants,
            'target_metric': target_metric,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=duration_days),
            'status': 'active',
            'results': {}
        }
        
        ab_tests_collection.insert_one(test)
        return test
    except Exception as e:
        st.error(f"Error creating A/B test: {str(e)}")
        return None

def assign_variant(user_id, test_id):
    try:
        test = ab_tests_collection.find_one({'test_id': test_id})
        if not test:
            return None
        
        # Simple random assignment
        variant = random.choice(test['variants'])
        
        # Record assignment
        ab_tests_collection.update_one(
            {'test_id': test_id},
            {'$push': {'assignments': {'user_id': user_id, 'variant': variant}}}
        )
        
        return variant
    except Exception as e:
        st.error(f"Error assigning variant: {str(e)}")
        return None

def track_user_activity(user_id):
    try:
        # Get user's orders
        user_orders = list(orders_collection.find({"user_id": user_id}).sort("created_at", -1))
        
        # Get user's login history
        user_logins = list(users_collection.find_one({"_id": user_id}).get('login_history', []))
        
        # Calculate metrics
        total_orders = len(user_orders)
        total_spent = sum(order['total_price'] for order in user_orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Time between orders
        if len(user_orders) > 1:
            order_dates = [order['created_at'] for order in user_orders]
            time_between_orders = np.diff(order_dates)
            avg_time_between_orders = np.mean(time_between_orders)
        else:
            avg_time_between_orders = None
        
        return {
            'total_orders': total_orders,
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'avg_time_between_orders': avg_time_between_orders,
            'login_history': user_logins,
            'recent_orders': user_orders[:5]
        }
    except Exception as e:
        st.error(f"Error tracking user activity: {str(e)}")
        return None 