#!/bin/bash

alembic upgrade head

uvicorn src.main:app --reload --host 127.0.0.1 --port 8000