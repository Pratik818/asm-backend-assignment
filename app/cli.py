import click

from app.core.security import hash_password, validate_password_strength
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


@click.group()
def asm() -> None:
    """ASM Asset Discovery Service CLI."""


@asm.command(name="create-admin", help="Create an Admin user")
@click.option("--email", required=True)
@click.option("--password", required=True)
@click.option("--full-name", required=True)
def create_admin(email: str, password: str, full_name: str) -> None:
    email = email.lower()
    try:
        validate_password_strength(password)
    except ValueError as exc:
        click.echo(f"Invalid password: {exc}")
        raise SystemExit(1) from exc

    db = SessionLocal()
    try:
        user_repository = UserRepository(db)
        if user_repository.get_by_email(email):
            click.echo(f"A user with email {email} already exists.")
            return

        user_repository.create(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=UserRole.ADMIN,
            )
        )
        click.echo(f"Created admin user: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    asm(prog_name="asm")
