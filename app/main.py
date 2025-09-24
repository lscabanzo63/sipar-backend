from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine
from app.interfaces.routers.auth import router as auth_router
from app.interfaces.routers.setup_router import router as setup_router


app = FastAPI(title="SIPAR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ajusta a tu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(setup_router)
