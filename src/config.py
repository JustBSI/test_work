import os
from dotenv import load_dotenv

load_dotenv()

docker = True

DB_HOST = os.environ.get("DB_HOST") if not docker else os.getenv("DOCKER_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
STORAGE_PATH = os.environ.get("STORAGE_PATH") if not docker else os.environ.get("DOCKER_PATH")
