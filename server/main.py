import math
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    status: str = "pending"

class CreateTaskRequest(BaseModel):
    title: str

class RestockingItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    lead_time_days: int

class CreateRestockingOrderRequest(BaseModel):
    budget: float
    items: List[RestockingItem]

# In-memory task storage
tasks_store: List[dict] = []
task_id_counter = 0

# In-memory restocking order storage
restocking_orders_store: List[dict] = []
restocking_order_id_counter = 0

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports"""
    # Filter orders based on params
    filtered_orders = orders
    if warehouse and warehouse != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('warehouse') == warehouse]
    if category and category != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('category', '').lower() == category.lower()]
    if month and month != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('order_date', '').startswith(month)]

    # Calculate quarterly statistics from orders
    quarters = {}

    for order in filtered_orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends"""
    # Filter orders based on params
    filtered_orders = orders
    if warehouse and warehouse != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('warehouse') == warehouse]
    if category and category != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('category', '').lower() == category.lower()]
    if month and month != 'all':
        filtered_orders = [o for o in filtered_orders if o.get('order_date', '').startswith(month)]

    months = {}

    for order in filtered_orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks"""
    return tasks_store

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task_data: CreateTaskRequest):
    """Create a new task"""
    global task_id_counter
    task_id_counter += 1
    task = {
        "id": f"task-{task_id_counter}",
        "title": task_data.title,
        "status": "pending"
    }
    tasks_store.insert(0, task)
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    global tasks_store
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_store = [t for t in tasks_store if t["id"] != task_id]
    return {"message": "Task deleted"}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle task status between pending and completed"""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.get("/api/restocking/recommendations")
def get_restocking_recommendations(budget: float = 10000):
    """Get restocking recommendations within a budget, prioritized by demand gap"""
    items_needing_restock = []
    for item in inventory_items:
        if item["quantity_on_hand"] < item["reorder_point"]:
            demand_gap = item["reorder_point"] - item["quantity_on_hand"]
            items_needing_restock.append({
                "item_sku": item["sku"],
                "item_name": item["name"],
                "demand_gap": demand_gap,
                "unit_cost": item["unit_cost"],
            })

    items_needing_restock.sort(key=lambda x: x["demand_gap"], reverse=True)

    remaining_budget = budget
    recommended_items = []
    for item in items_needing_restock:
        if remaining_budget <= 0:
            break
        recommended_qty = min(item["demand_gap"], math.floor(remaining_budget / item["unit_cost"]))
        if recommended_qty <= 0:
            continue
        if recommended_qty < 200:
            lead_time_days = 4
        elif recommended_qty <= 500:
            lead_time_days = 8
        else:
            lead_time_days = 14
        line_cost = recommended_qty * item["unit_cost"]
        remaining_budget -= line_cost
        recommended_items.append({
            "item_sku": item["item_sku"],
            "item_name": item["item_name"],
            "demand_gap": item["demand_gap"],
            "unit_cost": item["unit_cost"],
            "recommended_qty": recommended_qty,
            "line_cost": line_cost,
            "lead_time_days": lead_time_days,
        })

    total_cost = budget - remaining_budget
    return {
        "budget": budget,
        "total_cost": total_cost,
        "remaining_budget": remaining_budget,
        "items": recommended_items,
    }

@app.post("/api/restocking/orders", status_code=201)
def create_restocking_order(order_data: CreateRestockingOrderRequest):
    """Submit a restocking order"""
    global restocking_order_id_counter
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    restocking_order_id_counter += 1
    total_value = sum(item.quantity * item.unit_cost for item in order_data.items)
    max_lead_time = max(item.lead_time_days for item in order_data.items)
    order_date = datetime.now().isoformat()
    expected_delivery = (datetime.now() + timedelta(days=max_lead_time)).isoformat()

    order = {
        "id": f"rst-{restocking_order_id_counter}",
        "order_number": f"RST-{restocking_order_id_counter:04d}",
        "budget": order_data.budget,
        "status": "Submitted",
        "total_value": total_value,
        "order_date": order_date,
        "expected_delivery": expected_delivery,
        "items": [item.model_dump() for item in order_data.items],
    }
    restocking_orders_store.insert(0, order)
    return order

@app.get("/api/restocking/orders")
def get_restocking_orders():
    """Get all restocking orders"""
    return restocking_orders_store

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(po_data: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item"""
    po = {
        "id": f"po-{len(purchase_orders) + 1}",
        "backlog_item_id": po_data.backlog_item_id,
        "supplier_name": po_data.supplier_name,
        "quantity": po_data.quantity,
        "unit_cost": po_data.unit_cost,
        "expected_delivery_date": po_data.expected_delivery_date,
        "status": "pending",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "notes": po_data.notes,
    }
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order(backlog_item_id: str):
    """Get purchase order for a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
