FROM python:3.12.2-slim

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh