import uuid

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(
            "Missing or invalid authorization header", status_code=401, error_code="UNAUTHORIZED"
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise AppException(
            "Invalid or expired token", status_code=401, error_code="INVALID_TOKEN"
        ) from exc

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError as exc:
        raise AppException(
            "Invalid token payload", status_code=401, error_code="INVALID_TOKEN"
        ) from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppException("User not found", status_code=401, error_code="INVALID_TOKEN")
    if not user.is_active:
        raise AppException(
            "This account has been deactivated", status_code=401, error_code="INACTIVE_USER"
        )

    return user


def require_role(*allowed_roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AppException(
                "You do not have permission to perform this action",
                status_code=403,
                error_code="FORBIDDEN",
            )
        return current_user

    return dependency
