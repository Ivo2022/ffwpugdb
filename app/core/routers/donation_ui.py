from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from core.models.member import Members
from core.models.donation import Donation
from utils.templates import templates

# router = APIRouter(prefix="/admin/donations", tags=["Donations"])

router = APIRouter(include_in_schema=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ------------------------------
# List Donations
# ------------------------------
@router.get("/", name="donation_list")
async def list_donations(request: Request, db: AsyncSession = Depends(get_session)):
    results = await db.exec(select(Donation))
    donations_records = results.all()
    for d in donations_records:
        member = db.get(Members, d.member_id)
        d.member_name = member.name if member else "N/A"
    return templates.TemplateResponse(
        "admin/donation/list.html",
        {"request": request, "donations": donations_records}
    )

# ------------------------------
# Create Donation
# ------------------------------
@router.get("/create", name="donation_create")
async def create_donation_form(request: Request, db: AsyncSession = Depends(get_session)):
    results = await db.exec(select(Members))
    members_records = results.all()
    return templates.TemplateResponse(
        "admin/donation/create.html",
        {"request": request, "members": members_records}
    )

@router.post("/create", name="donation_create")
def create_donation(
    request: Request,
    member_id: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    db: Session = Depends(get_session)
):
    new_donation = Donation(member_id=member_id, amount=amount, date=date)
    db.add(new_donation)
    db.commit()
    db.refresh(new_donation)
    return RedirectResponse(url=request.url_for("donation_list"), status_code=303)

# ------------------------------
# Update Donation
# ------------------------------
@router.get("/update/{donation_id}", name="donation_update")
def update_donation_form(donation_id: str, request: Request, db: Session = Depends(get_session)):
    donation = db.get(Donations, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    members = db.exec(select(Members)).all()
    return request.app.state.templates.TemplateResponse(
        "admin/donation/update.html",
        {"request": request, "donation": donation, "members": members}
    )

@router.post("/update/{donation_id}", name="donation_update")
def update_donation(
    donation_id: str,
    request: Request,
    member_id: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    db: Session = Depends(get_session)
):
    donation = db.get(Donations, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    donation.member_id = member_id
    donation.amount = amount
    donation.date = date
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return RedirectResponse(url=request.url_for("donation_list"), status_code=303)

# ------------------------------
# Delete Donation
# ------------------------------
@router.get("/delete/{donation_id}", name="donation_delete")
def delete_donation(donation_id: str, request: Request, db: Session = Depends(get_session)):
    donation = db.get(Donations, donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    db.delete(donation)
    db.commit()
    return RedirectResponse(url=request.url_for("donation_list"), status_code=303)
