# Motor Part Shop Software (MPSS)

A full-stack Just-In-Time inventory management system for motor spare parts shops.

---

## Features

- **Inventory Management** — CRUD for parts with Part ID, Vehicle Type, Rack Number, Manufacturer, Vendor, Price, Stock
- **Sales Management** — Record daily transactions, auto-reduce stock, full history
- **JIT Threshold Engine** — Calculates 30-day weekly average sales as reorder threshold
- **Auto Order Generation** — One-click purchase order creation for all low-stock parts
- **Reports** — Daily revenue, monthly trends, top-selling parts with Chart.js graphs
- **Low Stock Alerts** — Dashboard badges and alert banners
- **Demo Mode** — Frontend works standalone without backend (sample data shown)

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | HTML5, CSS3, Vanilla JS, Chart.js |
| Backend   | Python 3.11, FastAPI, Pydantic    |
| Database  | MySQL 8.0                         |
| Deploy    | Docker + Docker Compose           |

---

## Quick Start (Docker)

```bash
# 1. Clone / extract the project
cd mpss

# 2. Start everything
docker-compose up -d

# 3. Open browser
#    Frontend: http://localhost:3000
#    API Docs: http://localhost:8000/docs
```

---

## Manual Setup

### 1. MySQL

```sql
# Run schema
mysql -u root -p < backend/schema.sql
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# Configure DB (edit or use env vars)
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=yourpassword
export DB_NAME=mpss

uvicorn main:app --reload --port 8000
```

### 3. Frontend

Simply open `frontend/index.html` in any browser.

> **Note:** Update the `API` constant in `index.html` if your backend runs on a different host/port.
> `const API = 'http://localhost:8000';`

---

## API Endpoints

| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| GET    | /dashboard                | Dashboard summary stats            |
| GET    | /parts                    | List all parts (search, filter)    |
| POST   | /parts                    | Add new part                       |
| PUT    | /parts/{id}               | Update part                        |
| DELETE | /parts/{id}               | Delete part                        |
| GET    | /vendors                  | List vendors                       |
| POST   | /vendors                  | Add vendor                         |
| GET    | /sales                    | Sales history (date filters)       |
| POST   | /sales                    | Record a sale                      |
| GET    | /threshold                | JIT threshold report               |
| GET    | /orders                   | List purchase orders               |
| POST   | /orders/generate          | Auto-generate low-stock orders     |
| PUT    | /orders/{id}              | Update order status                |
| GET    | /reports/daily            | Daily revenue report               |
| GET    | /reports/monthly          | Monthly sales report + chart data  |
| GET    | /reports/orders/daily     | Daily order report                 |

Full interactive docs available at: `http://localhost:8000/docs`

---

## Database Schema

```
vendors     → vendor_id, vendor_name, contact_person, phone, email, address, city
parts       → part_id, part_name, vehicle_type, manufacturer, vendor_id (FK), price, current_stock, rack_number
sales       → sale_id, part_id (FK), quantity, unit_price, total_price, sale_date
orders      → order_id, part_id (FK), vendor_id (FK), quantity_ordered, unit_cost, total_cost, order_date, status
```

---

## JIT Logic

Threshold = Average weekly sales over the last 30 days

```
weekly_avg = (total_qty_sold in 30 days) / (days_with_sales) * 7
threshold  = weekly_avg
order_qty  = (threshold × 2) - current_stock   # 2-week buffer
```

Parts are flagged when: `current_stock < threshold`

---

## Sample Data

- 5 vendors (Nairobi/Athi River suppliers)
- 15 parts (Toyota, Nissan, Universal)
- 30 days of sample sales history

---

## Currency

All prices are in **Kenya Shillings (KES)**. Modify the frontend formatting functions (`fmtNum`, `fmtK`) to change currency display.
