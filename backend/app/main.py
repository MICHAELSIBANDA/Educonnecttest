"""EduConnect API backed entirely by PostgreSQL."""
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.database import (create_database_engine, create_user, find_user, get_record,
                          initialize_database, issue_token, list_records, revoke_token,
                          save_record, user_for_token, verify_password)

Role = Literal["student", "donor", "supervisor", "technician", "reviewer", "allocation_officer", "admin"]
ALL_ROLES = {"student", "donor", "supervisor", "technician", "reviewer", "allocation_officer", "admin"}
STAFF_ROLES = {"supervisor", "technician", "reviewer", "allocation_officer", "admin"}
PUBLIC_ROLES = {"student", "donor"}

app = FastAPI(title="EduConnect API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
security = HTTPBearer(auto_error=False)
db_engine = create_database_engine()


class Health(BaseModel):
    status: str
    service: str


class Credentials(BaseModel):
    number: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12, max_length=200)


class Registration(Credentials):
    name: str = Field(min_length=2, max_length=150)
    role: Literal["student", "donor"]


class BootstrapUser(Registration):
    role: Role


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject", "request_info"]
    reason: str = Field(min_length=3, max_length=500)


class ReservationRequest(BaseModel):
    application_id: str
    device_asset: str


class HandoverRequest(BaseModel):
    application_id: str
    device_asset: str


@app.on_event("startup")
def startup() -> None:
    initialize_database(db_engine)


def public_user(user) -> dict:
    return {"id": user.id, "number": user.number, "name": user.name, "role": user.role}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    user = user_for_token(db_engine, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user


def require_staff(user=Depends(current_user)):
    if user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff role required")
    return user


@app.get("/api/health", response_model=Health, tags=["system"])
async def health() -> Health:
    return Health(status="ok", service="educonnect-api")


@app.post("/api/auth/login", tags=["authentication"])
async def login(credentials: Credentials) -> dict:
    user = find_user(db_engine, credentials.number)
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": issue_token(db_engine, user), "token_type": "bearer", "user": public_user(user)}


@app.post("/api/auth/register", tags=["authentication"])
async def register(registration: Registration) -> dict:
    if find_user(db_engine, registration.number):
        raise HTTPException(status_code=409, detail="An account with that number already exists")
    user = create_user(db_engine, registration.number, registration.name, registration.role, registration.password)
    return {"user": public_user(user), "message": "Account created. Sign in with your credentials."}


@app.post("/api/auth/bootstrap", tags=["authentication"])
async def bootstrap_user(registration: BootstrapUser, x_bootstrap_token: str | None = Header(default=None)) -> dict:
    configured_token = os.getenv("BOOTSTRAP_TOKEN")
    if not configured_token or x_bootstrap_token != configured_token:
        raise HTTPException(status_code=403, detail="Bootstrap token required")
    if find_user(db_engine, registration.number):
        raise HTTPException(status_code=409, detail="An account with that number already exists")
    user = create_user(db_engine, registration.number, registration.name, registration.role, registration.password)
    return {"user": public_user(user)}


@app.get("/api/auth/me", tags=["authentication"])
async def me(user=Depends(current_user)) -> dict:
    return {"user": public_user(user)}


@app.post("/api/auth/logout", tags=["authentication"])
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    revoke_token(db_engine, credentials.credentials)
    return {"message": "Signed out"}


@app.get("/api/overview", tags=["reporting"])
async def overview(_: object = Depends(require_staff)) -> dict:
    applications = list_records(db_engine, "application")
    inventory = list_records(db_engine, "inventory")
    eligible = sum(item.get("status") == "Eligible" for item in applications)
    ready = sum(item.get("status") == "Ready to allocate" for item in inventory)
    review = sum(item.get("status") == "Pending review" for item in applications)
    return {"total_applications": len(applications), "eligible_students": eligible, "ready_devices": ready, "awaiting_review": review, "complete_first_submission": 0, "average_allocation_days": 0, "qa_pass_rate": 0}


@app.get("/api/applications", tags=["applications"])
async def list_applications(faculty: str | None = Query(default=None), _: object = Depends(require_staff)) -> dict:
    items = list_records(db_engine, "application")
    filtered = [item for item in items if not faculty or faculty == "All faculties" or item.get("faculty") == faculty]
    return {"items": filtered, "faculty_filter": faculty, "policy": "canonical-fifo", "count": len(filtered)}


@app.post("/api/applications/{application_id}/review", tags=["applications"])
async def review_application(application_id: str, request: ReviewRequest, _: object = Depends(require_staff)) -> dict:
    record = get_record(db_engine, application_id)
    if record is None or record.record_type != "application":
        raise HTTPException(status_code=404, detail="Application not found")
    application = record.payload
    if request.decision == "approve" and (not application.get("complete") or float(str(application.get("average", "0")).strip("%")) < 60):
        raise HTTPException(status_code=422, detail="Application must be complete and have an average of at least 60%")
    application["status"] = {"approve": "Eligible", "reject": "Rejected", "request_info": "More info needed"}[request.decision]
    application["verified"] = request.decision == "approve"
    save_record(db_engine, application_id, "application", application)
    return {"item": application, "reason": request.reason}


@app.get("/api/students", tags=["students"])
async def list_students(query: str | None = Query(default=None), _: object = Depends(require_staff)) -> dict:
    items = list_records(db_engine, "student")
    filtered = [item for item in items if not query or query.lower() in f"{item.get('name', '')} {item.get('number', '')} {item.get('faculty', '')} {item.get('programme', '')}".lower()]
    return {"items": filtered, "count": len(filtered)}


@app.get("/api/inventory", tags=["inventory"])
async def list_inventory(_: object = Depends(require_staff)) -> dict:
    items = list_records(db_engine, "inventory")
    return {"items": items, "count": len(items)}


@app.get("/api/refurbishment", tags=["refurbishment"])
async def list_refurbishment(_: object = Depends(require_staff)) -> dict:
    items = list_records(db_engine, "refurbishment")
    return {"items": items, "count": len(items)}


@app.post("/api/allocations/reserve", tags=["allocation"])
async def reserve_device(request: ReservationRequest, _: object = Depends(require_staff)) -> dict:
    application_record = get_record(db_engine, request.application_id)
    device_record = get_record(db_engine, request.device_asset)
    if not application_record or not device_record or application_record.record_type != "application" or device_record.record_type != "inventory":
        raise HTTPException(status_code=404, detail="Application or device not found")
    application, device = application_record.payload, device_record.payload
    if application.get("status") != "Eligible" or not application.get("verified"):
        raise HTTPException(status_code=422, detail="Only verified eligible applications can be reserved")
    profile_rank = {"G1": 1, "G2": 2, "G3": 3}
    if device.get("status") != "Ready to allocate" or profile_rank.get(device.get("profile"), 0) < profile_rank.get(application.get("profile"), 99):
        raise HTTPException(status_code=422, detail="Device does not satisfy the student's academic requirement")
    expires = datetime.now(timezone.utc) + timedelta(days=14)
    application["status"], application["reservation_expires"] = "Reserved", expires.isoformat()
    device["status"] = "Reserved"
    save_record(db_engine, request.application_id, "application", application)
    save_record(db_engine, request.device_asset, "inventory", device)
    return {"application": application, "device": device, "reservation_expires": expires.isoformat(), "policy": "permanent-allocation-14-day-collection"}


@app.post("/api/allocations/handover", tags=["allocation"])
async def complete_handover(request: HandoverRequest, _: object = Depends(require_staff)) -> dict:
    application_record = get_record(db_engine, request.application_id)
    device_record = get_record(db_engine, request.device_asset)
    if not application_record or not device_record:
        raise HTTPException(status_code=404, detail="Application or device not found")
    application, device = application_record.payload, device_record.payload
    if application.get("status") != "Reserved" or device.get("status") != "Reserved":
        raise HTTPException(status_code=422, detail="Only a reserved application and device can be handed over")
    application["status"], application["reservation_expires"] = "Allocated permanently", None
    device["status"] = "Allocated permanently"
    save_record(db_engine, request.application_id, "application", application)
    save_record(db_engine, request.device_asset, "inventory", device)
    return {"application": application, "device": device, "policy": "permanent-allocation-no-reallocation"}
