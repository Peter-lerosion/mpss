"""
Motor Part Shop Software (MPSS) - FastAPI Backend
Run: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, timedelta
import mysql.connector
import os
from pathlib import Path
from contextlib import contextmanager

# Resolve frontend directory relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Motor Part Shop Software (MPSS)",
    description="API for managing spare parts inventory, sales, and supplier ordering",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files (CSS, JS, images etc)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ─── Database Configuration ───────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "mpss"),
    "autocommit": False
}

@contextmanager
def get_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def dict_cursor(conn):
    return conn.cursor(dictionary=True)

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class VendorCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

class PartCreate(BaseModel):
    part_id: str
    part_name: str
    vehicle_type: str
    manufacturer: str
    vendor_id: Optional[str] = None
    price: float
    current_stock: int
    rack_number: Optional[str] = None

class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    manufacturer: Optional[str] = None
    vendor_id: Optional[str] = None
    price: Optional[float] = None
    current_stock: Optional[int] = None
    rack_number: Optional[str] = None

class SaleCreate(BaseModel):
    part_id: str
    quantity: int
    unit_price: float
    sale_date: Optional[date] = None

class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Serve the frontend index.html."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "app": "MPSS API", "version": "1.0.0"}

@app.get("/health")
def health():
    try:
        with get_db() as conn:
            c = dict_cursor(conn)
            c.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(503, f"Database unavailable: {e}")

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/dashboard")
def dashboard():
    with get_db() as conn:
        c = dict_cursor(conn)

        c.execute("SELECT COUNT(*) AS total FROM parts")
        total_parts = c.fetchone()["total"]

        c.execute("SELECT SUM(current_stock * price) AS value FROM parts")
        inv_value = c.fetchone()["value"] or 0

        c.execute("SELECT SUM(total_price) AS rev FROM sales WHERE sale_date = CURDATE()")
        today_rev = c.fetchone()["rev"] or 0

        c.execute("SELECT SUM(total_price) AS rev FROM sales WHERE MONTH(sale_date)=MONTH(CURDATE()) AND YEAR(sale_date)=YEAR(CURDATE())")
        month_rev = c.fetchone()["rev"] or 0

        # Low stock parts (stock < weekly avg threshold)
        c.execute("""
            SELECT p.part_id, p.part_name, p.current_stock, p.vehicle_type,
                   COALESCE(SUM(s.quantity)/NULLIF(DATEDIFF(MAX(s.sale_date),MIN(s.sale_date))+1,0)*7, 0) AS weekly_avg
            FROM parts p
            LEFT JOIN sales s ON p.part_id = s.part_id
              AND s.sale_date >= CURDATE() - INTERVAL 30 DAY
            GROUP BY p.part_id
            HAVING p.current_stock < weekly_avg OR (weekly_avg = 0 AND p.current_stock <= 2)
        """)
        low_stock = c.fetchall()

        c.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='pending'")
        pending_orders = c.fetchone()["cnt"]

        # Today's top sellers
        c.execute("""
            SELECT p.part_name, SUM(s.quantity) AS qty, SUM(s.total_price) AS rev
            FROM sales s JOIN parts p ON s.part_id = p.part_id
            WHERE s.sale_date = CURDATE()
            GROUP BY p.part_id ORDER BY qty DESC LIMIT 5
        """)
        top_today = c.fetchall()

        return {
            "total_parts": total_parts,
            "inventory_value": round(float(inv_value), 2),
            "today_revenue": round(float(today_rev), 2),
            "month_revenue": round(float(month_rev), 2),
            "low_stock_count": len(low_stock),
            "low_stock_parts": low_stock,
            "pending_orders": pending_orders,
            "top_sellers_today": top_today
        }

# ─── Vendors ──────────────────────────────────────────────────────────────────

@app.get("/vendors")
def list_vendors():
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("SELECT * FROM vendors ORDER BY vendor_name")
        return c.fetchall()

@app.post("/vendors", status_code=201)
def create_vendor(v: VendorCreate):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("INSERT INTO vendors VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())",
                  (v.vendor_id, v.vendor_name, v.contact_person, v.phone, v.email, v.address, v.city))
    return {"message": "Vendor created", "vendor_id": v.vendor_id}

@app.get("/vendors/{vendor_id}")
def get_vendor(vendor_id: str):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("SELECT * FROM vendors WHERE vendor_id=%s", (vendor_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Vendor not found")
        return row

@app.put("/vendors/{vendor_id}")
def update_vendor(vendor_id: str, v: VendorUpdate):
    fields = {k: val for k, val in v.dict().items() if val is not None}
    if not fields:
        raise HTTPException(400, "No fields to update")
    sql = "UPDATE vendors SET " + ", ".join(f"{k}=%s" for k in fields) + " WHERE vendor_id=%s"
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute(sql, (*fields.values(), vendor_id))
    return {"message": "Updated"}

@app.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: str):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("DELETE FROM vendors WHERE vendor_id=%s", (vendor_id,))
    return {"message": "Deleted"}

# ─── Parts ────────────────────────────────────────────────────────────────────

@app.get("/parts")
def list_parts(search: Optional[str] = None, vehicle_type: Optional[str] = None, vendor_id: Optional[str] = None):
    with get_db() as conn:
        c = dict_cursor(conn)
        sql = """
            SELECT p.*, v.vendor_name, v.address as vendor_address,
                   COALESCE(
                     ROUND(SUM(s.quantity)/NULLIF(DATEDIFF(MAX(s.sale_date),MIN(s.sale_date))+1,0)*7, 1),
                   0) AS weekly_avg_sales
            FROM parts p
            LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
            LEFT JOIN sales s ON p.part_id = s.part_id AND s.sale_date >= CURDATE()-INTERVAL 30 DAY
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (p.part_name LIKE %s OR p.part_id LIKE %s OR p.manufacturer LIKE %s)"
            params += [f"%{search}%", f"%{search}%", f"%{search}%"]
        if vehicle_type:
            sql += " AND p.vehicle_type = %s"
            params.append(vehicle_type)
        if vendor_id:
            sql += " AND p.vendor_id = %s"
            params.append(vendor_id)
        sql += " GROUP BY p.part_id ORDER BY p.part_name"
        c.execute(sql, params)
        rows = c.fetchall()
        # Add threshold flag
        for r in rows:
            r["threshold"] = float(r["weekly_avg_sales"] or 0)
            r["low_stock"] = r["current_stock"] < r["threshold"] if r["threshold"] > 0 else r["current_stock"] <= 2
        return rows

@app.post("/parts", status_code=201)
def create_part(p: PartCreate):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""INSERT INTO parts (part_id,part_name,vehicle_type,manufacturer,vendor_id,price,current_stock,rack_number)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (p.part_id, p.part_name, p.vehicle_type, p.manufacturer, p.vendor_id, p.price, p.current_stock, p.rack_number))
    return {"message": "Part created", "part_id": p.part_id}

@app.get("/parts/{part_id}")
def get_part(part_id: str):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""
            SELECT p.*, v.vendor_name, v.address as vendor_address, v.phone as vendor_phone
            FROM parts p LEFT JOIN vendors v ON p.vendor_id=v.vendor_id
            WHERE p.part_id=%s
        """, (part_id,))
        row = c.fetchone()
        if not row:
            raise HTTPException(404, "Part not found")
        return row

@app.put("/parts/{part_id}")
def update_part(part_id: str, p: PartUpdate):
    fields = {k: val for k, val in p.dict().items() if val is not None}
    if not fields:
        raise HTTPException(400, "No fields to update")
    sql = "UPDATE parts SET " + ", ".join(f"{k}=%s" for k in fields) + " WHERE part_id=%s"
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute(sql, (*fields.values(), part_id))
    return {"message": "Updated"}

@app.delete("/parts/{part_id}")
def delete_part(part_id: str):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("DELETE FROM parts WHERE part_id=%s", (part_id,))
    return {"message": "Deleted"}

# ─── Sales ────────────────────────────────────────────────────────────────────

@app.get("/sales")
def list_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    part_id: Optional[str] = None
):
    with get_db() as conn:
        c = dict_cursor(conn)
        sql = """
            SELECT s.*, p.part_name, p.vehicle_type, p.manufacturer
            FROM sales s JOIN parts p ON s.part_id = p.part_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND s.sale_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND s.sale_date <= %s"
            params.append(end_date)
        if part_id:
            sql += " AND s.part_id = %s"
            params.append(part_id)
        sql += " ORDER BY s.sale_date DESC, s.created_at DESC"
        c.execute(sql, params)
        return c.fetchall()

@app.post("/sales", status_code=201)
def record_sale(s: SaleCreate):
    sale_date = s.sale_date or date.today()
    total = round(s.quantity * s.unit_price, 2)
    with get_db() as conn:
        c = dict_cursor(conn)
        # Check stock
        c.execute("SELECT current_stock, part_name FROM parts WHERE part_id=%s", (s.part_id,))
        part = c.fetchone()
        if not part:
            raise HTTPException(404, "Part not found")
        if part["current_stock"] < s.quantity:
            raise HTTPException(400, f"Insufficient stock. Available: {part['current_stock']}")
        # Record sale
        c.execute("""INSERT INTO sales (part_id, quantity, unit_price, total_price, sale_date)
                     VALUES (%s,%s,%s,%s,%s)""",
                  (s.part_id, s.quantity, s.unit_price, total, sale_date))
        # Reduce stock
        c.execute("UPDATE parts SET current_stock = current_stock - %s WHERE part_id=%s",
                  (s.quantity, s.part_id))
    return {"message": "Sale recorded", "total_price": total}

# ─── JIT Threshold ────────────────────────────────────────────────────────────

@app.get("/threshold")
def get_threshold_report():
    """Get all parts with their JIT thresholds and stock status."""
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""
            SELECT * FROM (
                SELECT p.part_id, p.part_name, p.vehicle_type, p.manufacturer,
                       p.current_stock, p.price, p.rack_number,
                       v.vendor_name, v.address as vendor_address, v.phone as vendor_phone,
                       COALESCE(ROUND(SUM(s.quantity)/NULLIF(DATEDIFF(MAX(s.sale_date),MIN(s.sale_date))+1,0)*7,1),0) AS weekly_avg
                FROM parts p
                LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
                LEFT JOIN sales s ON p.part_id = s.part_id AND s.sale_date >= CURDATE()-INTERVAL 30 DAY
                GROUP BY p.part_id, p.part_name, p.vehicle_type, p.manufacturer,
                         p.current_stock, p.price, p.rack_number,
                         v.vendor_name, v.address, v.phone
            ) AS sub
            ORDER BY (sub.current_stock - sub.weekly_avg) ASC
        """)
        rows = c.fetchall()
        result = []
        for r in rows:
            weekly = float(r["weekly_avg"] or 0)
            stock = r["current_stock"]
            status = "ok"
            if weekly > 0 and stock < weekly:
                status = "low"
            elif stock <= 2:
                status = "critical"
            result.append({**r, "threshold": weekly, "status": status,
                           "order_qty": max(0, round(weekly * 2 - stock))})
        return result

# ─── Orders ───────────────────────────────────────────────────────────────────

@app.get("/orders")
def list_orders(status: Optional[str] = None, order_date: Optional[date] = None):
    with get_db() as conn:
        c = dict_cursor(conn)
        sql = """
            SELECT o.*, p.part_name, p.vehicle_type, v.vendor_name, v.address as vendor_address, v.phone as vendor_phone
            FROM orders o
            JOIN parts p ON o.part_id = p.part_id
            LEFT JOIN vendors v ON o.vendor_id = v.vendor_id
            WHERE 1=1
        """
        params = []
        if status:
            sql += " AND o.status=%s"
            params.append(status)
        if order_date:
            sql += " AND o.order_date=%s"
            params.append(order_date)
        sql += " ORDER BY o.created_at DESC"
        c.execute(sql, params)
        return c.fetchall()

@app.post("/orders/generate")
def generate_orders():
    """Auto-generate orders for all low-stock parts."""
    today = date.today()
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""
            SELECT p.part_id, p.current_stock, p.vendor_id, p.price,
                   COALESCE(ROUND(SUM(s.quantity)/NULLIF(DATEDIFF(MAX(s.sale_date),MIN(s.sale_date))+1,0)*7,1),0) AS weekly_avg
            FROM parts p
            LEFT JOIN sales s ON p.part_id = s.part_id AND s.sale_date >= CURDATE()-INTERVAL 30 DAY
            GROUP BY p.part_id
            HAVING p.current_stock < weekly_avg OR (weekly_avg = 0 AND p.current_stock <= 2)
        """)
        low_parts = c.fetchall()
        created = 0
        for part in low_parts:
            weekly = float(part["weekly_avg"] or 1)
            order_qty = max(1, round(weekly * 2 - part["current_stock"]))
            cost = round(part["price"] * order_qty, 2)
            c.execute("""INSERT INTO orders (part_id, vendor_id, quantity_ordered, unit_cost, total_cost, order_date, status)
                         VALUES (%s,%s,%s,%s,%s,%s,'pending')""",
                      (part["part_id"], part["vendor_id"], order_qty, part["price"], cost, today))
            created += 1
    return {"message": f"Generated {created} orders", "orders_created": created}

@app.put("/orders/{order_id}")
def update_order_status(order_id: int, update: OrderStatusUpdate):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("UPDATE orders SET status=%s, notes=%s WHERE order_id=%s",
                  (update.status, update.notes, order_id))
        if update.status == "received":
            c.execute("SELECT part_id, quantity_ordered FROM orders WHERE order_id=%s", (order_id,))
            o = c.fetchone()
            if o:
                c.execute("UPDATE parts SET current_stock=current_stock+%s WHERE part_id=%s",
                          (o["quantity_ordered"], o["part_id"]))
    return {"message": "Order updated"}

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("DELETE FROM orders WHERE order_id=%s", (order_id,))
    return {"message": "Order deleted"}

# ─── Reports ──────────────────────────────────────────────────────────────────

@app.get("/reports/daily")
def daily_report(report_date: Optional[date] = None):
    d = report_date or date.today()
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""
            SELECT s.sale_id, s.part_id, p.part_name, p.vehicle_type,
                   s.quantity, s.unit_price, s.total_price, s.sale_date
            FROM sales s JOIN parts p ON s.part_id=p.part_id
            WHERE s.sale_date=%s ORDER BY s.created_at
        """, (d,))
        transactions = c.fetchall()

        c.execute("SELECT SUM(total_price) AS rev, SUM(quantity) AS qty, COUNT(*) AS txn FROM sales WHERE sale_date=%s", (d,))
        summary = c.fetchone()

        c.execute("""
            SELECT p.part_name, SUM(s.quantity) AS units, SUM(s.total_price) AS revenue
            FROM sales s JOIN parts p ON s.part_id=p.part_id
            WHERE s.sale_date=%s GROUP BY s.part_id ORDER BY revenue DESC LIMIT 5
        """, (d,))
        top_parts = c.fetchall()

        return {
            "date": str(d),
            "total_revenue": float(summary["rev"] or 0),
            "total_units_sold": int(summary["qty"] or 0),
            "total_transactions": int(summary["txn"] or 0),
            "transactions": transactions,
            "top_parts": top_parts
        }

@app.get("/reports/monthly")
def monthly_report(year: int = None, month: int = None):
    today = date.today()
    y = year or today.year
    m = month or today.month
    with get_db() as conn:
        c = dict_cursor(conn)
        # Daily breakdown
        c.execute("""
            SELECT sale_date, SUM(total_price) AS revenue, SUM(quantity) AS units, COUNT(*) AS transactions
            FROM sales WHERE YEAR(sale_date)=%s AND MONTH(sale_date)=%s
            GROUP BY sale_date ORDER BY sale_date
        """, (y, m))
        daily = c.fetchall()

        c.execute("""
            SELECT SUM(total_price) AS revenue, SUM(quantity) AS units, COUNT(*) AS transactions
            FROM sales WHERE YEAR(sale_date)=%s AND MONTH(sale_date)=%s
        """, (y, m))
        summary = c.fetchone()

        # Top parts this month
        c.execute("""
            SELECT p.part_name, p.vehicle_type, SUM(s.quantity) AS units_sold, SUM(s.total_price) AS revenue
            FROM sales s JOIN parts p ON s.part_id=p.part_id
            WHERE YEAR(s.sale_date)=%s AND MONTH(s.sale_date)=%s
            GROUP BY s.part_id ORDER BY revenue DESC LIMIT 10
        """, (y, m))
        top_parts = c.fetchall()

        return {
            "year": y, "month": m,
            "total_revenue": float(summary["revenue"] or 0),
            "total_units_sold": int(summary["units"] or 0),
            "total_transactions": int(summary["transactions"] or 0),
            "daily_breakdown": [
                {**d, "revenue": float(d["revenue"]), "sale_date": str(d["sale_date"])}
                for d in daily
            ],
            "top_parts": top_parts
        }

@app.get("/reports/orders/daily")
def daily_order_report(report_date: Optional[date] = None):
    d = report_date or date.today()
    with get_db() as conn:
        c = dict_cursor(conn)
        c.execute("""
            SELECT o.*, p.part_name, p.vehicle_type, v.vendor_name, v.address, v.phone, v.email
            FROM orders o
            JOIN parts p ON o.part_id=p.part_id
            LEFT JOIN vendors v ON o.vendor_id=v.vendor_id
            WHERE o.order_date=%s ORDER BY v.vendor_name
        """, (d,))
        orders = c.fetchall()
        c.execute("SELECT SUM(total_cost) AS total FROM orders WHERE order_date=%s", (d,))
        total = c.fetchone()
        return {
            "date": str(d),
            "total_order_cost": float(total["total"] or 0),
            "order_count": len(orders),
            "orders": orders
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 