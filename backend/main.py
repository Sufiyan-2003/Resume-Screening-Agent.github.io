from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.routes import router

app = FastAPI(title="ResumeScreen AI", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
frontend = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
