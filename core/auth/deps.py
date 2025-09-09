from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from core.auth.jwt_handler import decode_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from core.models.user import User, Role, UserRole
from core.schemas.user import UserRead
from sqlmodel import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

async def get_current_user_api(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        return payload  # or lookup user in DB
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def require_login(request: Request):
    # ✅ UI session-based auth
    user_id = request.session.get("user_id")
    if user_id:
        return {"sub": user_id}  # mimic token payload

    # ✅ Fallback to API auth
    token = request.headers.get("Authorization")
    if token:
        return await get_current_user_api(token.split(" ")[1])

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

async def get_current_user_ui(
    request: Request, session: AsyncSession = Depends(get_session)
):
    token = request.session.get("token")
    payload = decode_access_token(token) if token else None
    if not payload:
        return None
    return await session.get(User, payload.get("sub"))

async def get_current_user(request: Request, db: AsyncSession = Depends(get_session)) -> User:
    # Get token from session
    token = request.session.get("token")
    user = None

    if token:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            user = await db.get(User, user_id)

    # Fallback to API Bearer token
    if not user:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Role.name).join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    roles = result.scalars().all()

    user_out = UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        role_names=roles
    )
    return user_out
"""
def require_roles(*allowed_roles: str):
    async def dependency(user: User = Depends(get_current_user)):
        user_roles = user.roles if isinstance(user.roles, list) else [user.roles]
# role hierarchy
        hierarchy = {
            "member": ["member", "staff", "admin"],
            "staff": ["staff", "admin"],
            "admin": ["admin"],
        }

        # check if any of user's roles is allowed (considering hierarchy)
        for role in allowed_roles:
            if any(r in hierarchy[role] for r in user_roles):
                return user

        raise HTTPException(
            status_code=403,
            detail="You do not have permission",
        )
    return dependency
"""

def _extract_roles_from_obj(obj: any) -> list | None:
    """Try common attribute names and boolean flags to extract roles."""
    if not obj:
        return None

    # common list/string attributes
    for attr in ("roles", "role", "role_name", "role_names"):
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if val is None:
                continue
            if isinstance(val, (list, tuple, set)):
                return [str(x).lower() for x in val]
            if isinstance(val, str):
                return [val.lower()]

    # boolean flags
    flags = []
    if getattr(obj, "is_admin", False):
        flags.append("admin")
    if getattr(obj, "is_staff", False):
        flags.append("staff")
    if getattr(obj, "is_member", False):
        flags.append("member")
    if flags:
        return [f.lower() for f in flags]

    return None


def require_roles(*allowed_roles: str):
    """
    Role dependency that:
      - reads roles from the user object if present
      - otherwise loads the user row from DB and inspects it
      - supports role hierarchy: staff/admin can access member routes, admin can access staff routes, etc.
    Usage: Depends(require_roles("member")), Depends(require_roles("staff")), etc.
    """
    async def dependency(
        user: any = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ):
        # 1) Try to get roles directly from the user object returned by get_current_user
        roles = _extract_roles_from_obj(user)

        # 2) Fallback: load from DB (UserModel) and try again
        if roles is None:
            # Make sure user.id exists
            user_id = getattr(user, "id", None)
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid user object")

            # load DB user row
            result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user_row = result.scalar_one_or_none()
            if user_row:
                roles = _extract_roles_from_obj(user_row)

        # 3) If still None -> no role info available -> deny
        if not roles:
            raise HTTPException(status_code=403, detail="You do not have permission")

        # Normalize roles set
        user_roles_set: Set[str] = {r.lower() for r in roles}

        # Role hierarchy mapping (adjust if you have different names)
        hierarchy = {
            "member": {"member", "staff", "admin"},
            "staff": {"staff", "admin"},
            "admin": {"admin"},
        }

        # Check allowed_roles against hierarchy
        for role in allowed_roles:
            allowed_set = hierarchy.get(role, {role})
            if user_roles_set & {r.lower() for r in allowed_set}:
                return user

        raise HTTPException(status_code=403, detail="You do not have permission")

    return dependency