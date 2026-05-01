# 🐔 Poultry Management System

A complete, production-ready, web-based poultry farm management system built with **Python (FastAPI)**.
Includes flock management, egg tracking, feed inventory, health records, AI-camera detection
(OpenCV / optional YOLOv8), PDF reports, smart alerts, predictive analytics and a built-in
farm assistant chatbot.

---

## ✨ Features

| Module | What it does |
|---|---|
| 🔐 Authentication | JWT-based login, role-based access (admin / manager / worker), bcrypt password hashing |
| 🐓 Flock Management | Track bird batches, breeds, age, growth stages and mortality |
| 🥚 Egg Tracking | Daily collection, broken-egg counts, storage levels, sales records |
| 🌾 Feed Management | Purchases, consumption, real-time inventory with low-stock alerts |
| 💊 Health Records | Diseases, treatments and vaccination scheduling per batch |
| 📹 AI Camera | OpenCV bird/egg detection — upload images **or** stream a webcam. Optional YOLOv8 support |
| 📄 PDF Reports | Daily, weekly and financial reports generated with reportlab |
| 📁 File Storage | Upload receipts, invoices, photos and certificates |
| 🤖 Chatbot | Built-in rule-based assistant for feeding, biosecurity, vaccination, profit advice |
| 📊 Dashboard | Real-time statistics, trend charts and active alerts |
| 📈 Analytics | Performance score (0–100), 7-day egg prediction, revenue summary, smart insights |

---

## 🏗️ Architecture

```
poultry_system/
├── main.py                     # FastAPI entry point
├── requirements.txt
├── .env.example
├── README.md
│
├── app/
│   ├── config.py               # Settings (env-driven)
│   ├── database.py             # SQLAlchemy engine + DB seeding
│   ├── models/                 # SQLAlchemy ORM models
│   ├── routes/                 # API endpoints (FastAPI routers)
│   ├── services/               # Alerts, analytics, chatbot, PDF reports
│   ├── utils/                  # Security (JWT, bcrypt) + Pydantic schemas
│   └── ml/
│       └── detector.py         # PoultryDetector (YOLO → OpenCV fallback)
│
├── static/
│   ├── css/main.css
│   ├── js/app.js               # API client + helpers
│   └── uploads/                # User-uploaded files
│
├── templates/                  # Jinja2 HTML pages
│   ├── login.html, dashboard.html, birds.html, eggs.html
│   ├── feed.html, health.html, reports.html, camera.html
│   ├── files.html, chatbot.html
│
├── database/
│   ├── poultry.db              # SQLite (default, auto-created)
│   └── schema.sql              # Reference SQL schema
│
└── tests/                      # (placeholder — extend as needed)
```

---

## ⚙️ Installation

### Prerequisites
- **Python 3.10+** (3.11 or 3.12 recommended)
- pip

### Quick Start (SQLite — zero-config)

```bash
# 1. Clone or unzip the project
cd poultry_system

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit environment file
cp .env.example .env
# (or: copy .env.example .env  on Windows)

# 5. Run the server
python main.py
```

Open your browser to **http://localhost:8000**

### Default Login
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ Change the password and `SECRET_KEY` in `.env` before going to production.

---

## 🗄️ Database Configuration

The system uses **SQLite by default** (no setup needed). To switch databases, edit `DATABASE_URL` in `.env`:

### MySQL
```bash
# Install driver
pip install pymysql cryptography

# .env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/poultry_db
```

```sql
CREATE DATABASE poultry_db CHARACTER SET utf8mb4;
```

### PostgreSQL
```bash
pip install psycopg2-binary

# .env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/poultry_db
```

The application automatically creates all tables on first launch and seeds the default admin user. A reference SQL schema is also provided in `database/schema.sql`.

---

## 📹 AI Camera

The detector tries three backends in order:

1. **YOLOv8 custom-trained model** (`yolov8_custom.pt` if present) — best accuracy
2. **YOLOv8 pretrained COCO model** — detects "bird" out-of-the-box
3. **Classical OpenCV fallback** — Hough circles for eggs + contour-based bird detection (no extra dependency)

**To enable YOLO** (optional, ~500 MB install):
```bash
pip install ultralytics
# Set in .env:
USE_YOLO=true
YOLO_MODEL_PATH=yolov8n.pt
```

The first time YOLO runs it will download `yolov8n.pt` (~6 MB) automatically.

The webcam streaming endpoint reads from `CAMERA_DEVICE_INDEX` (default `0`). On a headless server with no camera, the page still works for image uploads.

---

## 🔌 API Reference

All endpoints under `/api/*` require a `Authorization: Bearer <token>` header (except `/api/auth/token`).

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/token` | POST | Get JWT (form-data: username, password) |
| `/api/auth/me` | GET | Current user info |
| `/api/auth/register` | POST | Create new user (admin only) |
| `/api/dashboard/summary` | GET | All KPIs |
| `/api/dashboard/charts/eggs-trend?days=14` | GET | Egg time series |
| `/api/dashboard/charts/mortality-trend?days=30` | GET | Mortality time series |
| `/api/dashboard/alerts` | GET | Unresolved alerts |
| `/api/dashboard/insights` | GET | Smart insights |
| `/api/birds/batches` | GET / POST | List / create batches |
| `/api/birds/mortality` | GET / POST | Death records |
| `/api/eggs/collection` | GET / POST | Daily collections |
| `/api/eggs/sales` | GET / POST | Egg sales |
| `/api/eggs/storage` | GET | Current storage qty |
| `/api/feed/purchase` | GET / POST | Feed purchases |
| `/api/feed/consumption` | GET / POST | Feed usage |
| `/api/feed/inventory` | GET | Stock by feed type |
| `/api/health/disease` | GET / POST | Disease records |
| `/api/health/vaccination` | GET / POST | Vaccinations |
| `/api/reports/daily` | GET | Daily PDF |
| `/api/reports/weekly` | GET | Weekly PDF |
| `/api/reports/financial` | GET | Financial PDF |
| `/api/files/upload` | POST | Upload file (multipart) |
| `/api/files/list` | GET | All files |
| `/api/chat/message` | POST | Ask the assistant |
| `/api/camera/detect-image` | POST | Run detection on uploaded image |
| `/api/camera/stream` | GET | MJPEG webcam stream with overlays |
| `/api/camera/live-counts` | GET | Latest counts |
| `/api/analytics/performance-score` | GET | 0–100 farm score |
| `/api/analytics/predict-eggs` | GET | 7-day egg forecast |
| `/api/analytics/revenue` | GET | Revenue summary |

Interactive Swagger docs are auto-generated at **http://localhost:8000/docs**.

---

## 🧪 Smoke test

```bash
python -c "
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
r = c.post('/api/auth/token', data={'username':'admin','password':'admin123'})
print('Login:', r.status_code)
"
```

---

## 🚀 Deployment

### Production server

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Recommended setup
- Reverse-proxy with **Nginx** terminating TLS
- Use **PostgreSQL** instead of SQLite for concurrent writes
- Set `DEBUG=false` and a strong random `SECRET_KEY` in `.env`
- Run behind a **systemd** service or with **Docker**

### Sample Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError: No module named 'cv2'`**
→ `pip install opencv-python-headless`

**`bcrypt password too long`**
→ Already handled — passwords are truncated to 72 bytes before hashing.

**Camera page shows "Camera not available"**
→ The server has no webcam. Use the image-upload feature instead, or set `CAMERA_DEVICE_INDEX` correctly.

**SQLite locked errors under load**
→ Switch to PostgreSQL or MySQL.

**`email-validator is not installed`**
→ `pip install 'pydantic[email]' email-validator`

---

## 📝 License

MIT — use freely for any purpose. Attribution appreciated.

---

## 👤 Default Roles

- `admin` — full access (create users, all CRUD)
- `manager` — all CRUD, can resolve alerts
- `worker` — record data, view dashboards

---

Happy farming! 🐣
