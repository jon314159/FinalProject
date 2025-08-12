"""
FastAPI Main Application Module

This module defines the main FastAPI application, including:
- Application initialization and configuration
- API endpoints for user authentication
- API endpoints for calculation management (BREAD operations)
- Web routes for HTML templates
- Database table creation on startup
- Cross-origin configuration, compression, health checks, and basic error handling
"""

from contextlib import asynccontextmanager  # Used for startup/shutdown events
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List, Optional

# FastAPI imports
from fastapi import Body, FastAPI, Depends, HTTPException, status, Request, Form, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError, ProgrammingError
from sqlalchemy import text, select
# App imports
from app.auth.dependencies import get_current_active_user
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.database import Base, get_db, engine

# ------------------------------------------------------------------------------
# Lifespan: create tables on startup for dev
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when the application starts. Creates DB tables for dev convenience.
    Prefer Alembic in production.
    """
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    yield

# ------------------------------------------------------------------------------
# App init
# ------------------------------------------------------------------------------
tags_metadata = [
    {"name": "web", "description": "HTML pages rendered with Jinja2."},
    {"name": "auth", "description": "User authentication and tokens."},
    {"name": "calculations", "description": "BREAD operations for calculations."},
    {"name": "health", "description": "Service and database health checks."},
]

app = FastAPI(
    title="Calculations API",
    description="API for managing calculations",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Simple security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp

# ------------------------------------------------------------------------------
# Static files and templates
# ------------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------------------------------------------------------
# Web (HTML) routes
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["web"])
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])
def view_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse("view_calculation.html", {"request": request, "calc_id": calc_id})

@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])
def edit_calculation_page(request: Request, calc_id: str):
    return templates.TemplateResponse("edit_calculation.html", {"request": request, "calc_id": calc_id})

# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}

@app.get("/health/db", tags=["health"])
def db_health(db: Session = Depends(get_db)):
    try:
        # Either option works; both satisfy Pylance + SQLAlchemy 2.0 typing
        db.execute(text("SELECT 1"))               # TextClause is Executable
        # db.execute(select(1))                    # Select is Executable
        return {"status": "ok", "db": "connected"}
    except OperationalError as e:
        raise HTTPException(status_code=503, detail=f"DB not reachable: {str(e)}")

# ------------------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------------------
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")

@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_result["user"]
    db.commit()

    expires_at = auth_result.get("expires_at")
    if not isinstance(expires_at, datetime):
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    elif expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )

@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": auth_result["access_token"], "token_type": "bearer"}

@app.post("/auth/refresh", response_model=TokenResponse, tags=["auth"])
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    Assumes User.refresh_access_token implements verification and rotation.
    """
    try:
        new_tokens = User.refresh_access_token(db, refresh_token)
        user = new_tokens["user"]
        expires_at = new_tokens.get("expires_at") or (datetime.now(timezone.utc) + timedelta(minutes=15))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        db.commit()
        return TokenResponse(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            token_type="bearer",
            expires_at=expires_at,
            user_id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/me", response_model=UserResponse, tags=["auth"])
def read_me(current_user = Depends(get_current_active_user)):
    return current_user

# ------------------------------------------------------------------------------
# Calculations (BREAD)
# ------------------------------------------------------------------------------
@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calculation.result = new_calculation.get_result()
        db.add(new_calculation)
        db.commit()
        db.refresh(new_calculation)
        return new_calculation
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
):
    """
    List current user's calculations with simple pagination.
    """
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def get_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    return calculation

@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()

    calculation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(calculation)
    return calculation

@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    db.delete(calculation)
    db.commit()
    return None

# ------------------------------------------------------------------------------
# Global error handlers
# ------------------------------------------------------------------------------
@app.exception_handler(IntegrityError)
def handle_integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=400, content={"detail": "Integrity error"})

@app.exception_handler(ProgrammingError)
def handle_programming_error(request: Request, exc: ProgrammingError):
    # Common when tables are missing
    return JSONResponse(status_code=500, content={"detail": "Database schema not ready"})

@app.exception_handler(SQLAlchemyError)
def handle_sa_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"detail": "Database error"})

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
