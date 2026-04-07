# ABOUTME: Tests for restocking recommendation and order submission endpoints.
# ABOUTME: Covers budget-based recommendations, order placement, and retrieval.
"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_default_budget(self, client):
        """Test getting recommendations with default budget."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["budget"] == 10000.0

    def test_get_recommendations_custom_budget(self, client):
        """Test getting recommendations with a specific budget."""
        response = client.get("/api/restocking/recommendations?budget=25000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 25000.0
        assert data["total_cost"] <= 25000.0
        assert data["remaining_budget"] >= 0
        assert abs(data["budget"] - data["total_cost"] - data["remaining_budget"]) < 0.01

    def test_get_recommendations_zero_budget_rejected(self, client):
        """Test that zero budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 400

    def test_negative_budget_rejected(self, client):
        """Test that negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400

    def test_recommendations_sorted_by_demand_gap(self, client):
        """Test that recommendations are sorted by demand gap descending."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        items = response.json()["items"]
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert items[i]["demand_gap"] >= items[i + 1]["demand_gap"]

    def test_recommendations_total_within_budget(self, client):
        """Test that total cost never exceeds budget."""
        for budget in [5000, 10000, 25000, 50000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["total_cost"] <= budget

    def test_recommendation_item_structure(self, client):
        """Test that each recommendation item has all required fields."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        items = response.json()["items"]
        assert len(items) > 0

        for item in items:
            assert "item_sku" in item
            assert "item_name" in item
            assert "demand_gap" in item
            assert "unit_cost" in item
            assert "quantity" in item
            assert "line_cost" in item
            assert "lead_time_days" in item
            assert isinstance(item["demand_gap"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["quantity"], int)
            assert isinstance(item["lead_time_days"], int)
            assert item["quantity"] > 0
            assert abs(item["line_cost"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_lead_time_tiers(self, client):
        """Test that lead times follow quantity-based tiers."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        for item in response.json()["items"]:
            qty = item["quantity"]
            lead = item["lead_time_days"]
            if qty < 200:
                assert lead == 4
            elif qty <= 500:
                assert lead == 8
            else:
                assert lead == 14

    def test_partial_quantity_fits_budget(self, client):
        """Test that a small budget can still recommend partial quantities."""
        response = client.get("/api/restocking/recommendations?budget=500")
        assert response.status_code == 200

        data = response.json()
        # With $500 budget, should get at least some items (cheapest is ~$19/unit)
        assert data["total_cost"] <= 500
        if len(data["items"]) > 0:
            assert data["items"][0]["quantity"] > 0


class TestRestockingOrders:
    """Test suite for POST and GET /api/restocking/orders."""

    def test_submit_restocking_order(self, client):
        """Test placing a restocking order."""
        order_data = {
            "budget": 10000,
            "items": [
                {
                    "item_sku": "SRV-301",
                    "item_name": "Micro Servo Motor",
                    "quantity": 10,
                    "unit_cost": 445.0,
                    "lead_time_days": 4
                }
            ]
        }
        response = client.post("/api/restocking/orders", json=order_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert "order_number" in data
        assert data["order_number"].startswith("RST-")
        assert data["status"] == "Submitted"
        assert data["total_value"] == 4450.0
        assert "order_date" in data
        assert "expected_delivery" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1

    def test_submit_empty_order_rejected(self, client):
        """Test that an order with no items is rejected."""
        order_data = {
            "budget": 10000,
            "items": []
        }
        response = client.post("/api/restocking/orders", json=order_data)
        assert response.status_code == 400

    def test_get_restocking_orders(self, client):
        """Test retrieving submitted restocking orders."""
        # Submit an order first
        order_data = {
            "budget": 5000,
            "items": [
                {
                    "item_sku": "GYR-207",
                    "item_name": "Gyroscope Module",
                    "quantity": 20,
                    "unit_cost": 95.0,
                    "lead_time_days": 4
                }
            ]
        }
        client.post("/api/restocking/orders", json=order_data)

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        order = data[-1]
        assert order["status"] == "Submitted"
        assert "order_number" in order
        assert "expected_delivery" in order

    def test_round_trip_order(self, client):
        """Test that a submitted order can be retrieved with correct data."""
        order_data = {
            "budget": 8000,
            "items": [
                {
                    "item_sku": "TMP-201",
                    "item_name": "Temperature Sensor Module",
                    "quantity": 50,
                    "unit_cost": 89.5,
                    "lead_time_days": 4
                },
                {
                    "item_sku": "GYR-207",
                    "item_name": "Gyroscope Module",
                    "quantity": 30,
                    "unit_cost": 95.0,
                    "lead_time_days": 4
                }
            ]
        }
        post_response = client.post("/api/restocking/orders", json=order_data)
        assert post_response.status_code == 201
        created_order = post_response.json()

        get_response = client.get("/api/restocking/orders")
        assert get_response.status_code == 200

        orders = get_response.json()
        matched = [o for o in orders if o["id"] == created_order["id"]]
        assert len(matched) == 1
        assert matched[0]["total_value"] == created_order["total_value"]
        assert len(matched[0]["items"]) == 2
