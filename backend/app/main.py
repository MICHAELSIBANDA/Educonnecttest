"""EduConnect API for the allocation operations MVP."""
from datetime import datetime, timedelta, timezone
import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.database import create_database_engine, initialize_database, load_state, save_state

app = FastAPI(title="EduConnect API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Role = Literal["student", "donor", "supervisor", "technician", "reviewer", "allocation_officer", "admin"]
STAFF_ROLES = {"supervisor", "technician", "reviewer", "allocation_officer", "admin"}

class Health(BaseModel):
    status: str
    service: str
class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject", "request_info"]
    reason: str = Field(min_length=3, max_length=500)
class ReservationRequest(BaseModel):
    application_id: str
    device_asset: str
class HandoverRequest(BaseModel):
    application_id: str
    device_asset: str

def current_role(x_role: str | None = Header(default=None)) -> Role:
    role = x_role or "allocation_officer"
    if role not in {"student", "donor", "supervisor", "technician", "reviewer", "allocation_officer", "admin"}:
        raise HTTPException(status_code=403, detail="Unknown role")
    return role  # type: ignore[return-value]
def require_staff(role: Role = Depends(current_role)) -> Role:
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff role required")
    return role

students = [
    {"name": "Thabo Mokoena", "number": "222345678", "faculty": "ICT", "programme": "Diploma in IT", "year": "2nd year", "device": "Allocated", "academic_average": 72, "profile": "G3"},
    {"name": "Lerato Dlamini", "number": "223456789", "faculty": "Science", "programme": "Diploma in Analytical Chemistry", "year": "1st year", "device": "Pending allocation", "academic_average": 68, "profile": "G2"},
    {"name": "Anele Ndlovu", "number": "224567890", "faculty": "Humanities", "programme": "Diploma in Language Practice", "year": "3rd year", "device": "Pending review", "academic_average": 64, "profile": "G1"},
    {"name": "Mpho Khumalo", "number": "225678901", "faculty": "Management Sciences", "programme": "Diploma in Marketing", "year": "2nd year", "device": "More info needed", "academic_average": 61, "profile": "G1"},
]
applications = [
    {"id": "APP-001", "position": 1, "name": "Thabo Mokoena", "number": "222345678", "faculty": "ICT", "programme": "Diploma in IT", "average": "72%", "submitted": "18 Aug 2026, 08:42", "profile": "G3", "status": "Eligible", "complete": True, "verified": True, "reservation_expires": None},
    {"id": "APP-002", "position": 2, "name": "Lerato Dlamini", "number": "223456789", "faculty": "Science", "programme": "Diploma in Analytical Chemistry", "average": "68%", "submitted": "18 Aug 2026, 09:17", "profile": "G2", "status": "Eligible", "complete": True, "verified": True, "reservation_expires": None},
    {"id": "APP-003", "position": 3, "name": "Anele Ndlovu", "number": "224567890", "faculty": "Humanities", "programme": "Diploma in Language Practice", "average": "64%", "submitted": "18 Aug 2026, 10:04", "profile": "G1", "status": "Pending review", "complete": True, "verified": False, "reservation_expires": None},
    {"id": "APP-004", "position": 4, "name": "Mpho Khumalo", "number": "225678901", "faculty": "Management Sciences", "programme": "Diploma in Marketing", "average": "61%", "submitted": "19 Aug 2026, 08:09", "profile": "G1", "status": "More info needed", "complete": False, "verified": False, "reservation_expires": None},
]
inventory = [
    {"asset": "TUT-DEV-1042", "model": "Lenovo ThinkPad L14", "condition": "Grade A", "location": "Main store", "status": "Ready to allocate", "profile": "G3"},
    {"asset": "TUT-DEV-1043", "model": "Dell Latitude 5420", "condition": "Grade A", "location": "Main store", "status": "Ready to allocate", "profile": "G2"},
    {"asset": "TUT-DEV-1044", "model": "HP ProBook 440 G8", "condition": "Grade B", "location": "TUT eMalahleni", "status": "Awaiting QA", "profile": "G1"},
    {"asset": "TUT-DEV-1045", "model": "Lenovo ThinkPad L14", "condition": "Grade B", "location": "Main store", "status": "Reserved", "profile": "G1"},
]
refurbishment = [
    {"asset": "TUT-DEV-1044", "model": "HP ProBook 440 G8", "technician": "K. Mthembu", "completed": "19 Aug 2026", "result": "Awaiting QA"},
    {"asset": "TUT-DEV-1038", "model": "Dell Latitude 5420", "technician": "S. Molefe", "completed": "18 Aug 2026", "result": "Passed"},
    {"asset": "TUT-DEV-1037", "model": "Lenovo ThinkPad L14", "technician": "K. Mthembu", "completed": "18 Aug 2026", "result": "Passed"},
]

db_engine = create_database_engine() if os.getenv("DATABASE_URL") else None


def persist_state() -> None:
    if db_engine is None:
        return
    save_state(db_engine, "students", {"items": students})
    save_state(db_engine, "applications", {"items": applications})
    save_state(db_engine, "inventory", {"items": inventory})
    save_state(db_engine, "refurbishment", {"items": refurbishment})


@app.on_event("startup")
def load_persisted_state() -> None:
    if db_engine is None:
        return
    initialize_database(db_engine)
    for key, target in (("students", students), ("applications", applications), ("inventory", inventory), ("refurbishment", refurbishment)):
        state = load_state(db_engine, key)
        if state is None:
            persist_state()
        else:
            target[:] = state["items"]

@app.get("/api/health", response_model=Health, tags=["system"])
async def health() -> Health:
    return Health(status="ok", service="educonnect-api")
@app.get("/api/overview", tags=["reporting"])
async def overview(_: Role = Depends(require_staff)) -> dict:
    return {"total_applications": 248, "eligible_students": 126, "ready_devices": 38, "awaiting_review": 24, "complete_first_submission": 72, "average_allocation_days": 15, "qa_pass_rate": 84}
@app.get("/api/applications", tags=["applications"])
async def list_applications(faculty: str | None = Query(default=None), _: Role = Depends(require_staff)) -> dict:
    items = [item for item in applications if not faculty or faculty == "All faculties" or item["faculty"] == faculty]
    return {"items": items, "faculty_filter": faculty, "policy": "canonical-fifo", "count": len(items)}
@app.post("/api/applications/{application_id}/review", tags=["applications"])
async def review_application(application_id: str, request: ReviewRequest, _: Role = Depends(require_staff)) -> dict:
    application = next((item for item in applications if item["id"] == application_id), None)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if request.decision == "approve" and (not application["complete"] or float(application["average"].strip("%")) < 60):
        raise HTTPException(status_code=422, detail="Application must be complete and have an average of at least 60%")
    application["status"] = {"approve": "Eligible", "reject": "Rejected", "request_info": "More info needed"}[request.decision]
    application["verified"] = request.decision == "approve"
    persist_state()
    return {"item": application, "reason": request.reason}
@app.get("/api/students", tags=["students"])
async def list_students(query: str | None = Query(default=None), _: Role = Depends(require_staff)) -> dict:
    items = [item for item in students if not query or query.lower() in f"{item['name']} {item['number']} {item['faculty']} {item['programme']}".lower()]
    return {"items": items, "count": len(items)}
@app.get("/api/inventory", tags=["inventory"])
async def list_inventory(_: Role = Depends(require_staff)) -> dict:
    return {"items": inventory, "count": len(inventory)}
@app.get("/api/refurbishment", tags=["refurbishment"])
async def list_refurbishment(_: Role = Depends(require_staff)) -> dict:
    return {"items": refurbishment, "count": len(refurbishment)}
@app.post("/api/allocations/reserve", tags=["allocation"])
async def reserve_device(request: ReservationRequest, _: Role = Depends(require_staff)) -> dict:
    application = next((item for item in applications if item["id"] == request.application_id), None)
    device = next((item for item in inventory if item["asset"] == request.device_asset), None)
    if not application or not device:
        raise HTTPException(status_code=404, detail="Application or device not found")
    if application["status"] != "Eligible" or not application["verified"]:
        raise HTTPException(status_code=422, detail="Only verified eligible applications can be reserved")
    profile_rank = {"G1": 1, "G2": 2, "G3": 3}
    if device["status"] != "Ready to allocate" or profile_rank[device["profile"]] < profile_rank[application["profile"]]:
        raise HTTPException(status_code=422, detail="Device does not satisfy the student's academic requirement")
    expires = datetime.now(timezone.utc) + timedelta(days=14)
    application["status"] = "Reserved"
    application["reservation_expires"] = expires.isoformat()
    device["status"] = "Reserved"
    persist_state()
    return {"application": application, "device": device, "reservation_expires": expires.isoformat(), "policy": "permanent-allocation-14-day-collection"}
@app.post("/api/allocations/handover", tags=["allocation"])
async def complete_handover(request: HandoverRequest, _: Role = Depends(require_staff)) -> dict:
    application = next((item for item in applications if item["id"] == request.application_id), None)
    device = next((item for item in inventory if item["asset"] == request.device_asset), None)
    if not application or not device:
        raise HTTPException(status_code=404, detail="Application or device not found")
    if application["status"] != "Reserved" or device["status"] != "Reserved":
        raise HTTPException(status_code=422, detail="Only a reserved application and device can be handed over")
    application["status"] = "Allocated permanently"
    device["status"] = "Allocated permanently"
    application["reservation_expires"] = None
    persist_state()
    return {"application": application, "device": device, "policy": "permanent-allocation-no-reallocation"}
