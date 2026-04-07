# ABOUTME: Tests for purchase order creation endpoint.
# ABOUTME: Covers ID uniqueness, field validation, and retrieval.
"""
Tests for purchase order API endpoints.
"""


class TestCreatePurchaseOrder:
    """Test suite for POST /api/purchase-orders."""

    def _make_po_data(self, backlog_item_id="BL-001"):
        return {
            "backlog_item_id": backlog_item_id,
            "supplier_name": "Acme Corp",
            "quantity": 100,
            "unit_cost": 25.0,
            "expected_delivery_date": "2026-05-01",
            "notes": "Urgent restock",
        }

    def test_create_purchase_order(self, client):
        """Test basic PO creation returns 201 with expected fields."""
        response = client.post("/api/purchase-orders", json=self._make_po_data())
        assert response.status_code == 201

        data = response.json()
        assert data["id"].startswith("po-")
        assert data["backlog_item_id"] == "BL-001"
        assert data["supplier_name"] == "Acme Corp"
        assert data["quantity"] == 100
        assert data["unit_cost"] == 25.0
        assert data["status"] == "pending"

    def test_unique_ids_across_multiple_pos(self, client):
        """Test that two sequential POs produce distinct IDs."""
        r1 = client.post("/api/purchase-orders", json=self._make_po_data("BL-001"))
        r2 = client.post("/api/purchase-orders", json=self._make_po_data("BL-002"))
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]

    def test_ids_increment_monotonically(self, client):
        """Test that PO ID numeric suffix increases with each creation."""
        r1 = client.post("/api/purchase-orders", json=self._make_po_data("BL-001"))
        r2 = client.post("/api/purchase-orders", json=self._make_po_data("BL-002"))

        id1 = int(r1.json()["id"].split("-")[1])
        id2 = int(r2.json()["id"].split("-")[1])
        assert id2 > id1

    def test_ids_unique_after_list_shrinks(self, client):
        """Test that IDs never collide even if the backing list shrinks."""
        from mock_data import purchase_orders

        r1 = client.post("/api/purchase-orders", json=self._make_po_data("BL-001"))
        r2 = client.post("/api/purchase-orders", json=self._make_po_data("BL-002"))
        # Simulate a PO being removed from the in-memory list
        purchase_orders.pop()

        r3 = client.post("/api/purchase-orders", json=self._make_po_data("BL-003"))
        ids = {r1.json()["id"], r2.json()["id"], r3.json()["id"]}
        assert len(ids) == 3, f"Expected 3 unique IDs, got {ids}"
