"""
app/core/dependencies.py
────────────────────────
Reusable FastAPI dependencies for authentication and authorization.

Usage:
    @router.get("/protected")
    async def handler(user: User = Depends(get_current_user)):
        ...

    @router.delete("/admin-only")
    async def handler(user: User = Depends(require_role(UserRole.ADMIN))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.base import get_db
from app.models import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates Bearer JWT and returns the active User.
    Raises 401 on any auth failure — never leaks the reason to the client.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not user_id or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_role(*roles: UserRole):
    """
    Factory that returns a dependency requiring specific roles.

    Usage:
        Depends(require_role(UserRole.ADMIN, UserRole.OWNER))
    """
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _checker


# Shortcuts
get_current_admin = require_role(UserRole.ADMIN)
get_current_owner = require_role(UserRole.OWNER, UserRole.ADMIN)
