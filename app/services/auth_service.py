from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import RegisterRequest

settings = get_settings()


class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register(self, command: RegisterRequest) -> User:
        if self.user_repository.get_by_email(command.email):
            raise AppException(
                "Email already registered", status_code=409, error_code="EMAIL_ALREADY_REGISTERED"
            )

        user = User(
            email=command.email,
            password_hash=hash_password(command.password),
            full_name=command.full_name,
            role=command.role,
        )
        try:
            return self.user_repository.create(user)
        except IntegrityError as exc:
            raise AppException(
                "Email already registered", status_code=409, error_code="EMAIL_ALREADY_REGISTERED"
            ) from exc

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AppException(
                "Invalid email or password", status_code=401, error_code="INVALID_CREDENTIALS"
            )
        if not user.is_active:
            raise AppException(
                "This account has been deactivated", status_code=401, error_code="INACTIVE_USER"
            )

        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_seconds,
        )
