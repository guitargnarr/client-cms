"""
Client CMS API - Production version with PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import os
import json

from sqlalchemy import create_engine, Column, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


# --- Database Setup ---

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Handle Railway/Render postgres:// vs postgresql:// URL format
# Use pg8000 driver (pure Python, no compilation needed)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+pg8000" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# Remove sslmode from URL (pg8000 handles SSL differently)
if "sslmode=" in DATABASE_URL:
    # Strip sslmode parameter from URL
    import re
    DATABASE_URL = re.sub(r'[\?&]sslmode=[^&]*', '', DATABASE_URL)
    # Clean up any double ? or trailing ?
    DATABASE_URL = DATABASE_URL.replace('?&', '?').rstrip('?')

# For local development without database
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./cms_data.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pg8000 with SSL for cloud databases
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    engine = create_engine(DATABASE_URL, connect_args={"ssl_context": ssl_context})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Database Models ---


class SiteContentDB(Base):
    __tablename__ = "site_content"

    site_id = Column(String(100), primary_key=True, index=True)
    business_name = Column(String(200), nullable=False)
    tagline = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    hours_json = Column(Text, default="{}")
    services_json = Column(Text, default="[]")
    staff_json = Column(Text, default="[]")
    menu_items_json = Column(Text, default="[]")
    promotions_json = Column(Text, default="[]")


class SitePasswordDB(Base):
    __tablename__ = "site_passwords"

    site_id = Column(String(100), primary_key=True, index=True)
    password_hash = Column(String(200), nullable=False)


# --- Pydantic Models ---


class Hours(BaseModel):
    monday: str = "Closed"
    tuesday: str = "Closed"
    wednesday: str = "Closed"
    thursday: str = "Closed"
    friday: str = "Closed"
    saturday: str = "Closed"
    sunday: str = "Closed"


class Service(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    price: Optional[str] = None
    icon: Optional[str] = None


class StaffMember(BaseModel):
    id: Optional[str] = None
    name: str
    role: str
    bio: Optional[str] = None
    image: Optional[str] = None


class MenuItem(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: str
    category: Optional[str] = None


class Promotion(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    active: bool = True


class SiteContent(BaseModel):
    site_id: str
    business_name: str
    tagline: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    hours: Hours = Hours()
    services: list[Service] = []
    staff: list[StaffMember] = []
    menu_items: list[MenuItem] = []
    promotions: list[Promotion] = []


class SiteAuth(BaseModel):
    site_id: str
    password: str


class SiteCreate(BaseModel):
    site_id: str
    business_name: str
    password: str


# --- App Initialization ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Client CMS API", version="2.0.0", lifespan=lifespan)

# CORS for admin panel and client sites
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dependencies ---


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Auth ---


# Fallback passwords for demo (use DB in production)
DEMO_PASSWORDS = {
    "clater-jewelers": os.getenv("CLATER_PASSWORD", "demo123"),
    "fritz-salon": os.getenv("FRITZ_PASSWORD", "demo123"),
    "jw-cafe": os.getenv("JW_PASSWORD", "demo123"),
}


def verify_auth(
    site_id: str, x_auth_token: str = Header(None), db: Session = Depends(get_db)
) -> bool:
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    # Check database first
    site_pw = db.query(SitePasswordDB).filter(SitePasswordDB.site_id == site_id).first()
    if site_pw:
        if x_auth_token != site_pw.password_hash:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        return True

    # Fall back to env/demo passwords
    expected = DEMO_PASSWORDS.get(site_id, "")
    if x_auth_token != expected:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return True


# --- Storage Helpers ---


def db_to_content(db_site: SiteContentDB) -> SiteContent:
    return SiteContent(
        site_id=db_site.site_id,
        business_name=db_site.business_name,
        tagline=db_site.tagline,
        phone=db_site.phone,
        email=db_site.email,
        address=db_site.address,
        hours=Hours(**json.loads(db_site.hours_json or "{}")),
        services=[Service(**s) for s in json.loads(db_site.services_json or "[]")],
        staff=[StaffMember(**s) for s in json.loads(db_site.staff_json or "[]")],
        menu_items=[MenuItem(**m) for m in json.loads(db_site.menu_items_json or "[]")],
        promotions=[Promotion(**p) for p in json.loads(db_site.promotions_json or "[]")],
    )


def content_to_db(content: SiteContent, db_site: SiteContentDB) -> SiteContentDB:
    db_site.business_name = content.business_name
    db_site.tagline = content.tagline
    db_site.phone = content.phone
    db_site.email = content.email
    db_site.address = content.address
    db_site.hours_json = json.dumps(content.hours.model_dump())
    db_site.services_json = json.dumps([s.model_dump() for s in content.services])
    db_site.staff_json = json.dumps([s.model_dump() for s in content.staff])
    db_site.menu_items_json = json.dumps([m.model_dump() for m in content.menu_items])
    db_site.promotions_json = json.dumps([p.model_dump() for p in content.promotions])
    return db_site


def load_site(site_id: str, db: Session) -> SiteContent:
    db_site = db.query(SiteContentDB).filter(SiteContentDB.site_id == site_id).first()
    if db_site:
        return db_to_content(db_site)
    # Return default structure for new sites
    return SiteContent(
        site_id=site_id, business_name=site_id.replace("-", " ").title()
    )


def save_site(content: SiteContent, db: Session) -> None:
    db_site = (
        db.query(SiteContentDB).filter(SiteContentDB.site_id == content.site_id).first()
    )
    if db_site:
        content_to_db(content, db_site)
    else:
        db_site = SiteContentDB(site_id=content.site_id)
        content_to_db(content, db_site)
        db.add(db_site)
    db.commit()


# --- Public Endpoints ---


@app.get("/api/sites/{site_id}", response_model=SiteContent)
def get_site_content(site_id: str, db: Session = Depends(get_db)) -> SiteContent:
    """Public endpoint - client sites fetch their content here"""
    return load_site(site_id, db)


@app.get("/api/sites/{site_id}/hours", response_model=Hours)
def get_hours(site_id: str, db: Session = Depends(get_db)) -> Hours:
    return load_site(site_id, db).hours


@app.get("/api/sites/{site_id}/services", response_model=list[Service])
def get_services(site_id: str, db: Session = Depends(get_db)) -> list[Service]:
    return load_site(site_id, db).services


@app.get("/api/sites/{site_id}/menu", response_model=list[MenuItem])
def get_menu(site_id: str, db: Session = Depends(get_db)) -> list[MenuItem]:
    return load_site(site_id, db).menu_items


@app.get("/api/sites")
def list_sites(db: Session = Depends(get_db)) -> list[dict]:
    """List all sites (admin overview)"""
    sites = db.query(SiteContentDB).all()
    return [{"site_id": s.site_id, "business_name": s.business_name} for s in sites]


# --- Admin Endpoints ---


@app.post("/api/auth/login")
def login(auth: SiteAuth, db: Session = Depends(get_db)) -> dict:
    """Verify password, return token"""
    # Check database first
    site_pw = db.query(SitePasswordDB).filter(SitePasswordDB.site_id == auth.site_id).first()
    if site_pw:
        if auth.password != site_pw.password_hash:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"token": auth.password, "site_id": auth.site_id}

    # Fall back to demo passwords
    expected = DEMO_PASSWORDS.get(auth.site_id)
    if not expected or auth.password != expected:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": auth.password, "site_id": auth.site_id}


@app.post("/api/admin/sites")
def create_site(
    site_data: SiteCreate, x_auth_token: str = Header(None), db: Session = Depends(get_db)
) -> dict:
    """Create a new site with password"""
    # Simple admin auth - require master password
    master_pw = os.getenv("ADMIN_PASSWORD", "admin123")
    if x_auth_token != master_pw:
        raise HTTPException(status_code=401, detail="Admin auth required")

    # Check if site exists
    existing = db.query(SiteContentDB).filter(SiteContentDB.site_id == site_data.site_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists")

    # Create site content
    db_site = SiteContentDB(
        site_id=site_data.site_id,
        business_name=site_data.business_name,
    )
    db.add(db_site)

    # Create site password
    db_pw = SitePasswordDB(
        site_id=site_data.site_id,
        password_hash=site_data.password,  # In production, hash this!
    )
    db.add(db_pw)

    db.commit()
    return {"status": "created", "site_id": site_data.site_id}


@app.put("/api/admin/{site_id}")
def update_site(
    site_id: str,
    content: SiteContent,
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Update entire site content"""
    verify_auth(site_id, x_auth_token, db)
    content.site_id = site_id
    save_site(content, db)
    return {"status": "saved", "site_id": site_id}


@app.put("/api/admin/{site_id}/hours")
def update_hours(
    site_id: str,
    hours: Hours,
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    verify_auth(site_id, x_auth_token, db)
    site = load_site(site_id, db)
    site.hours = hours
    save_site(site, db)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/services")
def update_services(
    site_id: str,
    services: list[Service],
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    verify_auth(site_id, x_auth_token, db)
    site = load_site(site_id, db)
    for i, svc in enumerate(services):
        if not svc.id:
            svc.id = f"svc-{i}"
    site.services = services
    save_site(site, db)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/menu")
def update_menu(
    site_id: str,
    items: list[MenuItem],
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    verify_auth(site_id, x_auth_token, db)
    site = load_site(site_id, db)
    for i, item in enumerate(items):
        if not item.id:
            item.id = f"menu-{i}"
    site.menu_items = items
    save_site(site, db)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/staff")
def update_staff(
    site_id: str,
    staff: list[StaffMember],
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    verify_auth(site_id, x_auth_token, db)
    site = load_site(site_id, db)
    for i, member in enumerate(staff):
        if not member.id:
            member.id = f"staff-{i}"
    site.staff = staff
    save_site(site, db)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/promotions")
def update_promotions(
    site_id: str,
    promos: list[Promotion],
    x_auth_token: str = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    verify_auth(site_id, x_auth_token, db)
    site = load_site(site_id, db)
    for i, promo in enumerate(promos):
        if not promo.id:
            promo.id = f"promo-{i}"
    site.promotions = promos
    save_site(site, db)
    return {"status": "saved"}


# --- Health Check ---


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "2.0.0", "database": "connected" if DATABASE_URL else "sqlite"}


@app.get("/")
def root() -> dict:
    return {"service": "Client CMS API", "version": "2.0.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
