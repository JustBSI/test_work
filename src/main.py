from pathlib import Path

import uvicorn
from fastapi import FastAPI

from src.files.router import router as router_file
from src.config import Config

app = FastAPI(
    title="File manager"
)

app.include_router(router_file)

Path(Config.STORAGE_PATH).mkdir(parents=True, exist_ok=True) if Config.DOCKER == 'False' else None

if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
