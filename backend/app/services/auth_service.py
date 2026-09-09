from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import create_access_token, hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, name: str, email: str, password: str) -> tuple[User, str]:
        if self.users.get_by_email(email):
            raise EmailAlreadyRegisteredError(f"An account with email '{email}' already exists")
        user = self.users.create(name=name, email=email, password_hash=hash_password(password))
        return user, create_access_token(subject=user.id)

    def login(self, email: str, password: str) -> tuple[User, str]:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        return user, create_access_token(subject=user.id)
