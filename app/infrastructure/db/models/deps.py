from email.generator import Generator
from app.infrastructure.db.models.model import User
from typing import Generator
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal

def get_current_user() -> User:
    return User(id=1, rol="ADMIN")

def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()