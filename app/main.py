# main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

# --- Import database and models ---
from app.database import engine, async_session
from sqlmodel import SQLModel
from core.models.chapter import Chapters
from core.models.member import Members
from core.models.donation import Donation

# --- Import routers ---
from app.core.routers import auth_ui
from core.routers import events
from core.auth.routers import router_ui, router_api
from core.routers.ui import members_ui, donation_ui, attendance_ui, dashboard_ui
from core.routers.api import members_api, donations_api, attendance_api, dashboard_api
import os
# from starlette.middleware.base import BaseHTTPMiddleware
from core.auth.deps import get_current_user

# --- Import JWT handler for auth ---   
from core.auth.jwt_handler import decode_access_token
app = FastAPI(title="FFWPU-UG ERP Core System")

"""
class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user = await get_current_user(request)
        response = await call_next(request)
        return response
"""

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") 
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
# app.add_middleware(UserContextMiddleware)
# --- Mount static files ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def hybrid_auth_middleware(request: Request, call_next):
    request.state.user = None
    request.state.is_authenticated = False

    token = None

    # 1️⃣ Try UI session
    if "session" in request.scope:
        token = request.session.get("token")

    # 2️⃣ Try API header
    if not token and "authorization" in request.headers:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    # 3️⃣ Decode if available
    if token:
        try:
            payload = decode_access_token(token)
            request.state.user = payload
            request.state.is_authenticated = True
        except Exception:
            if "session" in request.scope:
                request.session.clear()
            request.state.user = None
            request.state.is_authenticated = False

    return await call_next(request)

# Force root "/" → login screen
@app.get("/", include_in_schema=False)
async def root(request: Request):
    if getattr(request.state, "user", None):
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/auth/login")



# --- Include routers ---
app.include_router(router_ui.router, prefix="/auth", tags=["Router-UI"])
app.include_router(members_ui.router, prefix="/members", tags=["Members-UI"])
app.include_router(attendance_ui.router, prefix="/attendance", tags=["Attendance-UI"])
app.include_router(donation_ui.router, prefix="/donation", tags=["Donation-UI"])
app.include_router(dashboard_ui.router, prefix="", tags=["Dashboard-UI"])

app.include_router(router_api.router, prefix="/api/auth", tags=["Router-API"])       # JWT for APIs
app.include_router(members_api.router, prefix="/api/members", tags=["Members-API"])
app.include_router(donations_api.router, prefix="/api/donations", tags=["Donations-API"])
app.include_router(attendance_api.router, prefix="/api/attendance", tags=["Attendance-API"])
app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["Dashboard-API"])

# --- Database initialization ---
@app.on_event("startup")
async def on_startup():
    """
    Runs at FastAPI startup:
    - Creates all tables if they don't exist
    """
    async with engine.begin() as conn:
        # Import all models before creating tables to resolve FKs
        await conn.run_sync(SQLModel.metadata.create_all) 