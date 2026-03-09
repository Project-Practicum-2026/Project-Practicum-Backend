from fastapi import FastAPI
from app.core import base  # noqa: F401
from app.auth.router import router as auth_router

app = FastAPI(title="LogiGlobal API")

app.include_router(auth_router, prefix="/api/auth")


@app.post("/")
async def root():
    return {"message": "Hello World"}