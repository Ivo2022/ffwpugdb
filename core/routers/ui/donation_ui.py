
"""
# core/routers/donation.py
from fastapi import APIRouter, Depends
from core.crud.donation import create_donation, get_donations_by_member
from core.schemas.donation import DonationCreate, DonationRead
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.donation import Donation

router = APIRouter(prefix="/donations", tags=["Donations"])

# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/", response_model=DonationRead)
async def add_donation(donation: DonationCreate, db: AsyncSession = Depends(get_session)):
    don_obj = Donation(**donation.dict())
    return await create_donation(db, don_obj)

@router.get("/{member_id}", response_model=list[DonationRead])
async def list_donations(member_id: str, db: AsyncSession = Depends(get_session)):
    return await get_donations_by_member(db, member_id)
"""

from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from core.models.donation import DonationType, Donation
from core.auth.deps import require_login
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from utils.templates import templates
from core.crud.donation import donation_crud
from typing import Optional
from sqlmodel import select
from uuid import UUID
import uuid
from datetime import date
from core.models.member import Members  # make sure you import Member
from sqlalchemy.orm import selectinload

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------
# List Donations
# ------------------------
@router.get("/")
async def donations_list(request: Request, q: Optional[str] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), user=Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

    # Load donations with their members
    stmt = donation_crud.select_stmt(
        q=q,
        search_fields=["donation_type", "remarks"],
        page=page,
        page_size=page_size,
        order_by="date"
    ).options(selectinload(Donation.member))  # <-- eager load member

    donations = (await session.execute(stmt)).scalars().all()
    total = await donation_crud.count_filtered(
        session,
        q=q,
        search_fields=["donation_type", "remarks"]
    )

    return templates.TemplateResponse(
        "/admin/donation/list.html",
        {
            "request": request,
            "user": user, 
            "donations": donations,
            "q": q or "",
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size else 0),
        },
    )

# ------------------------
# Display Donation Form
# ------------------------
@router.get("/create")
async def donations_create_page(request: Request, session: AsyncSession = Depends(get_session), user=Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    result = await session.execute(select(Members))
    members = result.scalars().all()
    return templates.TemplateResponse(
        "/admin/donation/create.html", {"request": request, "members": members, "user": user, "error": None}
    )

# ------------------------
# Handle Donation Data
# ------------------------
@router.post("/create", response_class=HTMLResponse)
async def donations_create(request: Request, member_id: UUID = Form(...), amount: float = Form(...), donation_type: DonationType = Form(...), donation_date: date = Form(...), remarks: Optional[str] = Form(None), session: AsyncSession = Depends(get_session),):
    donation_in = {
        "member_id": member_id,
        "amount": amount,
        "donation_type": donation_type,
        "donation_date": donation_date,
        "remarks": remarks,
    }
    try:
        donation = await donation_crud.create(session, donation_in)
        return RedirectResponse(url="/donation", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "/admin/donation/create.html",
            {"request": request, "error": str(e), "donation": donation_in},
        )

# --------------------------
# Display Edit / Update Form
# --------------------------

@router.get("/{donation_id}/edit")
async def donations_form_page(request: Request, donation_id: uuid.UUID, user=Depends(require_login), session: AsyncSession = Depends(get_session)):
    if isinstance(user, RedirectResponse):
        return user
    donation = await donation_crud.get(session, donation_id, with_relationships=True)
    
    # Convert donation_date to string for HTML input
    if donation and donation.donation_date:
        donation.donation_date = donation.donation_date.strftime("%Y-%m-%d")
    else:
        donation.donation_date = ""

    return templates.TemplateResponse(
        "/admin/donation/update.html", {"request": request, "user": user, "donation": donation}
    )

# --------------------------
# Handle Edit / Update Form
# --------------------------
@router.post("/{donation_id}/edit")
async def donations_edit_page(request: Request, donation_id: uuid.UUID, amount: float = Form(...), donation_date: date = Form(...), donation_type: DonationType = Form(...), remarks: Optional[str] = Form(None), user=Depends(require_login), session: AsyncSession = Depends(get_session),):
    if isinstance(user, RedirectResponse):
        return user

    donation = await donation_crud.get(session, donation_id, with_relationships=True)
    updates = {
        "amount": amount,
        "donation_date": donation_date,
        "donation_type": donation_type,
        "remarks": remarks,
    }
    await donation_crud.update(session, donation, updates)  # ✅ must be awaited
    return RedirectResponse(url="/donation", status_code=303)

# ------------------------
# Delete
# ------------------------
@router.post("/{donation_id}/delete")
async def donations_delete(donation_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    donation = await donation_crud.get(session, donation_id)
    await donation_crud.delete(session, donation)
    return RedirectResponse(url="/donations", status_code=303)

# ------------------------
# Search Members
# ------------------------
@router.get("/search-members")
async def search_members(q: str, session: AsyncSession = Depends(get_session), user=Depends(require_login)):
    if isinstance(user, RedirectResponse):
        return user
    
    stmt = select(Members).where(
        (Members.first_name.ilike(f"%{q}%")) |
        (Members.last_name.ilike(f"%{q}%")) |
        (Members.member_code.ilike(f"%{q}%"))
    )
    result = await session.execute(stmt)
    members = result.scalars().all()

    return [{"id": str(m.id), "user": user, "name": f"{m.first_name} {m.last_name}"} for m in members]