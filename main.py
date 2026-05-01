"""
Poultry Management System - This is Main Application Entry Point
Production-ready FastAPI application for managing a poultry farm.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes import (
    auth_routes,
    dashboard_routes,
    bird_routes,
    egg_routes,
    feed_routes,
    health_routes,
    report_routes,
    file_routes,
    chatbot_routes,
    camera_routes,
    analytics_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Initializing database...")
    init_db()
    print("[STARTUP] Database ready.")
    print("[STARTUP] Poultry Management System running on http://localhost:8000")
    yield
    print("[SHUTDOWN] Closing connections.")


app = FastAPI(
    title="Online Poultry Management System",
    description="Production-grade web app for managing poultry farms with AI integration.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(bird_routes.router, prefix="/api/birds", tags=["Birds"])
app.include_router(egg_routes.router, prefix="/api/eggs", tags=["Eggs"])
app.include_router(feed_routes.router, prefix="/api/feed", tags=["Feed"])
app.include_router(health_routes.router, prefix="/api/health", tags=["Health"])
app.include_router(report_routes.router, prefix="/api/reports", tags=["Reports"])
app.include_router(file_routes.router, prefix="/api/files", tags=["Files"])
app.include_router(chatbot_routes.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(camera_routes.router, prefix="/api/camera", tags=["Camera"])
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["Analytics"])


# Frontend pages
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/birds", response_class=HTMLResponse)
async def birds_page(request: Request):
    return templates.TemplateResponse(request, "birds.html")


@app.get("/eggs", response_class=HTMLResponse)
async def eggs_page(request: Request):
    return templates.TemplateResponse(request, "eggs.html")


@app.get("/feed", response_class=HTMLResponse)
async def feed_page(request: Request):
    return templates.TemplateResponse(request, "feed.html")


@app.get("/health", response_class=HTMLResponse)
async def health_page(request: Request):
    return templates.TemplateResponse(request, "health.html")


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse(request, "reports.html")


@app.get("/camera", response_class=HTMLResponse)
async def camera_page(request: Request):
    return templates.TemplateResponse(request, "camera.html")


@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    return templates.TemplateResponse(request, "files.html")


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request):
    return templates.TemplateResponse(request, "chatbot.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
