from typing import Generator
from fastapi import Depends
from .database import SessionLocal
from app.infrastructure.repositories.sorteo_repository import SorteoRepo as SorteoRepository
from sqlalchemy.orm import Session

def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(session: Session = Depends(get_session)) -> SorteoRepository:
    return SorteoRepository(session)