from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from core.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceRead
from core.models.attendance import Attendance, AttendanceStatus
from core.crud.attendance import attendance_crud
from app.database import async_session
from core.auth.deps import require_login, get_current_user_api
import uuid

router = APIRouter()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------
# List attendances (API)
# ------------------------
@router.get("/", response_model=List[AttendanceRead])
async def list_attendances(q: Optional[str] = Query(None), status: Optional[AttendanceStatus] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), dependencies=[Depends(get_current_user_api)], session: AsyncSession = Depends(get_session)):
    # --- Convert empty strings to None ---
    status = status.strip() if status and status.strip() else None

    # --- Parse Enum safely ---
    status_enum = None
    if status:
        try:
            status_enum = AttendanceStatus(status.lower())
        except ValueError:
            status_enum = None

    filters = {}
    if status_enum:
        filters["status"] = status_enum

    stmt = attendance_crud.select_stmt(
        q=q,
        filters=filters,
        search_fields=["attendance_date"],
        page=page,
        page_size=page_size,
        order_by="attendance_date"
    )

    attendances = (await session.execute(stmt)).scalars().all()
    return attendances

# ------------------------
# Get single attendance
# ------------------------
@router.get("/{attendance_id}", response_model=AttendanceRead)
async def get_attendance(member_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    attendance = await attendance_crud.get(session, member_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return attendance

# ------------------------
# Create Attendance
# ------------------------

@router.post("/", response_model=AttendanceRead)
async def create_attendance(member_in: AttendanceCreate, session: AsyncSession = Depends(get_session)):
    return await attendance_crud.create(session, member_in.model_dump())
"""

@router.post("/create")
async def create_attendance(
    member_ids: list[str] = Form(...),
    attendance_date: str = Form(...),
    status: str = Form(...),
    remarks: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    try:
        attendance_date_obj = datetime.datetime.strptime(attendance_date, "%Y-%m-%d").date()
        created_records = []

        for member_id in member_ids:
            obj_in = {
                "member_id": member_id,
                "attendance_date": attendance_date_obj,
                "status": status,
                "remarks": remarks
            }
            record = await attendance_crud.create(session, obj_in)
            created_records.append(record)

        return RedirectResponse(url="/attendance", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
# ------------------------
# Update Attendance
# ------------------------
@router.patch("/{attendance_id}", response_model=AttendanceRead)
async def update_attendance(attendance_id: uuid.UUID, attendance_in: AttendanceUpdate, session: AsyncSession = Depends(get_session)):
    attendance = await attendance_crud.get(session, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="attendance not found")
    return await attendance_crud.update(session, attendance, attendance_in.model_dump(exclude_unset=True))

# ------------------------
# Archive / Restore / Delete
# ------------------------
@router.post("/{attendance_id}/archive", response_model=AttendanceRead)
async def archive_attendance(attendance_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    attendance = await attendance_crud.get(session, attendance_id)
    return await attendance_crud.update(session, attendance, {"status": AttendanceStatus.inactive.value})

@router.post("/{attendance_id}/restore", response_model=AttendanceRead)
async def restore_attendance(attendance_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    attendance = await attendance_crud.get(session, attendance_id)
    return await attendance_crud.update(session, attendance, {"status": AttendanceStatus.active.value})

@router.delete("/{attendance_id}")
async def delete_attendance(attendance_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    attendance = await attendance_crud.get(session, attendance_id)
    await attendance_crud.delete(session, attendance)
    return {"detail": "Attendance deleted successfully"}
