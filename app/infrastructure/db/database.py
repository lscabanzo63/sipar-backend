from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.settings import DATABASE_URL

SQLALCHEMY_DATABASE_URL = DATABASE_URL or "postgresql+psycopg://postgres:123456@localhost:5432/db_sipar"

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)