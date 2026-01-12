"""
Client CMS API - Simple content management for client sites
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
from pathlib import Path

app = FastAPI(title="Client CMS API", version="1.0.0")

# CORS for admin panel and client sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple file-based storage (upgrade to Postgres later)
# Use /tmp for Vercel serverless compatibility (ephemeral storage)
DATA_DIR = Path("/tmp/cms-data") if os.getenv("VERCEL") else Path("data")
DATA_DIR.mkdir(exist_ok=True)


# --- Models ---


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


# --- Auth (simple password-based) ---

SITE_PASSWORDS = {
    "clater-jewelers": os.getenv("CLATER_PASSWORD", "demo123"),
    "fritz-salon": os.getenv("FRITZ_PASSWORD", "demo123"),
    "jw-cafe": os.getenv("JW_PASSWORD", "demo123"),
    # Add more as needed
}


def verify_auth(site_id: str, x_auth_token: str = Header(None)) -> bool:
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="Missing auth token")
    expected = SITE_PASSWORDS.get(site_id, "")
    if x_auth_token != expected:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return True


# --- Storage helpers ---


def get_site_path(site_id: str) -> Path:
    return DATA_DIR / f"{site_id}.json"


def load_site(site_id: str) -> SiteContent:
    path = get_site_path(site_id)
    if path.exists():
        data = json.loads(path.read_text())
        return SiteContent(**data)
    # Return default structure
    return SiteContent(site_id=site_id, business_name=site_id.replace("-", " ").title())


def save_site(content: SiteContent) -> None:
    path = get_site_path(content.site_id)
    path.write_text(json.dumps(content.model_dump(), indent=2))


# --- Public endpoints (for client sites to fetch content) ---


@app.get("/api/sites/{site_id}", response_model=SiteContent)
def get_site_content(site_id: str) -> SiteContent:
    """Public endpoint - client sites fetch their content here"""
    return load_site(site_id)


@app.get("/api/sites/{site_id}/hours", response_model=Hours)
def get_hours(site_id: str) -> Hours:
    return load_site(site_id).hours


@app.get("/api/sites/{site_id}/services", response_model=list[Service])
def get_services(site_id: str) -> list[Service]:
    return load_site(site_id).services


@app.get("/api/sites/{site_id}/menu", response_model=list[MenuItem])
def get_menu(site_id: str) -> list[MenuItem]:
    return load_site(site_id).menu_items


# --- Admin endpoints (require auth) ---


@app.post("/api/auth/login")
def login(auth: SiteAuth) -> dict:
    """Verify password, return token (password itself for simplicity)"""
    expected = SITE_PASSWORDS.get(auth.site_id)
    if not expected or auth.password != expected:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": auth.password, "site_id": auth.site_id}


@app.put("/api/admin/{site_id}")
def update_site(
    site_id: str, content: SiteContent, x_auth_token: str = Header(None)
) -> dict:
    """Update entire site content"""
    verify_auth(site_id, x_auth_token)
    content.site_id = site_id  # Ensure consistency
    save_site(content)
    return {"status": "saved", "site_id": site_id}


@app.put("/api/admin/{site_id}/hours")
def update_hours(
    site_id: str, hours: Hours, x_auth_token: str = Header(None)
) -> dict:
    verify_auth(site_id, x_auth_token)
    site = load_site(site_id)
    site.hours = hours
    save_site(site)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/services")
def update_services(
    site_id: str, services: list[Service], x_auth_token: str = Header(None)
) -> dict:
    verify_auth(site_id, x_auth_token)
    site = load_site(site_id)
    # Auto-generate IDs
    for i, svc in enumerate(services):
        if not svc.id:
            svc.id = f"svc-{i}"
    site.services = services
    save_site(site)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/menu")
def update_menu(
    site_id: str, items: list[MenuItem], x_auth_token: str = Header(None)
) -> dict:
    verify_auth(site_id, x_auth_token)
    site = load_site(site_id)
    for i, item in enumerate(items):
        if not item.id:
            item.id = f"menu-{i}"
    site.menu_items = items
    save_site(site)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/staff")
def update_staff(
    site_id: str, staff: list[StaffMember], x_auth_token: str = Header(None)
) -> dict:
    verify_auth(site_id, x_auth_token)
    site = load_site(site_id)
    for i, member in enumerate(staff):
        if not member.id:
            member.id = f"staff-{i}"
    site.staff = staff
    save_site(site)
    return {"status": "saved"}


@app.put("/api/admin/{site_id}/promotions")
def update_promotions(
    site_id: str, promos: list[Promotion], x_auth_token: str = Header(None)
) -> dict:
    verify_auth(site_id, x_auth_token)
    site = load_site(site_id)
    for i, promo in enumerate(promos):
        if not promo.id:
            promo.id = f"promo-{i}"
    site.promotions = promos
    save_site(site)
    return {"status": "saved"}


# --- Health check ---


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
def root() -> dict:
    return {"service": "Client CMS API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
