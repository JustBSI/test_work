from pathlib import Path

from fastapi import FastAPI

from src.files.router import router as router_file
from src.config import STORAGE_PATH as STORAGE, docker

app = FastAPI(
    title="File manager"
)

app.include_router(router_file)

Path(STORAGE).mkdir(parents=True, exist_ok=True) if not docker else None
