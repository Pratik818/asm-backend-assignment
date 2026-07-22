from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import RegisterRequest, UserResponse
from app.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    command: RegisterRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = AuthService(db)
    return service.register(command)


@auth_router.post("/login", response_model=TokenResponse)
def login(command: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(command.email, command.password)
