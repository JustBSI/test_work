import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DOCKER = os.environ.get("DOCKER")
    DB_HOST = os.environ.get("DB_HOST") if DOCKER == 'False' else os.environ.get("DOCKER_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASS = os.environ.get("DB_PASS")
    STORAGE_PATH = os.environ.get("STORAGE_PATH") if DOCKER == 'False' else os.environ.get("DOCKER_PATH")
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
