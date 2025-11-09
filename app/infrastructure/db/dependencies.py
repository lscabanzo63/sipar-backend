from typing import Generator
from fastapi import Depends
from .database import SessionLocal
from app.infrastructure.repositories.sorteo_repository import SorteoRepo 
from sqlalchemy.orm import Session

def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(session: Session = Depends(get_session)) -> SorteoRepo:
    return SorteoRepo(session)