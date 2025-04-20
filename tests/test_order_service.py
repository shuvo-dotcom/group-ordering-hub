import pytest
from datetime import datetime
from src.models.order import Order, OrderItem
from src.services.order_service import OrderService
from pymongo import MongoClient
from src.config import MONGO_URI

@pytest.fixture
def test_db():
    """Create a test database connection."""
    client = MongoClient(MONGO_URI)
    db = client.test_crowdcargo
    yield db
    # Cleanup after tests
    client.drop_database('test_crowdcargo')

@pytest.fixture
def order_service(test_db):
    """Create an OrderService instance with test database."""
    return OrderService(test_db)

@pytest.fixture
def sample_order():
    """Create a sample order for testing."""
    items = [
        OrderItem(
            product_id="1",
            name="Haldiram's Bhujia",
            quantity=2,
            weight_kg=1.0,
            price=5.99
        ),
        OrderItem(
            product_id="2",
            name="Lays Magic Masala",
            quantity=5,
            weight_kg=0.5,
            price=2.99
        )
    ]
    
    return Order(
        user_id="test_user",
        items=items,
        total_weight_kg=4.5,
        total_price=25.93,
        shipping_address={
            "street": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "Ireland"
        },
        contact_info={
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890"
        }
    )

def test_create_order(order_service, sample_order):
    """Test creating a new order."""
    order_id = order_service.create_order(sample_order)
    assert order_id is not None
    
    # Verify order was created
    retrieved_order = order_service.get_order(sample_order.order_id)
    assert retrieved_order is not None
    assert retrieved_order.user_id == sample_order.user_id
    assert len(retrieved_order.items) == len(sample_order.items)

def test_get_user_orders(order_service, sample_order):
    """Test retrieving orders for a specific user."""
    # Create multiple orders for the same user
    order_service.create_order(sample_order)
    orders = order_service.get_user_orders(sample_order.user_id)
    assert len(orders) > 0
    assert all(order.user_id == sample_order.user_id for order in orders)

def test_update_order_status(order_service, sample_order):
    """Test updating order status."""
    order_service.create_order(sample_order)
    success = order_service.update_order_status(sample_order.order_id, "processing")
    assert success
    
    updated_order = order_service.get_order(sample_order.order_id)
    assert updated_order.status == "processing"

def test_get_pending_orders(order_service, sample_order):
    """Test retrieving pending orders."""
    order_service.create_order(sample_order)
    pending_orders = order_service.get_pending_orders()
    assert len(pending_orders) > 0
    assert all(order.status == "pending" for order in pending_orders)

def test_get_total_pending_weight(order_service, sample_order):
    """Test calculating total pending weight."""
    order_service.create_order(sample_order)
    total_weight = order_service.get_total_pending_weight()
    assert total_weight == sample_order.total_weight_kg

def test_assign_shipping_plan(order_service, sample_order):
    """Test assigning a shipping plan to an order."""
    order_service.create_order(sample_order)
    success = order_service.assign_shipping_plan(sample_order.order_id, "DHL Express")
    assert success
    
    updated_order = order_service.get_order(sample_order.order_id)
    assert updated_order.shipping_plan == "DHL Express" 