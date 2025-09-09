# app/core/helpers.py
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.auth.jwt_handler import verify_access_token


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)):
    """Retrieve the current logged-in user or redirect to login."""
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")

    payload = verify_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")

    user_id = payload.get("sub")
    if not user_id:
        return RedirectResponse(url="/login")

    # Optional: load the user from DB
    from app.core.models.user import User
    result = await session.get(User, user_id)
    if not result:
        return RedirectResponse(url="/login")

    return result
