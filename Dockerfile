FROM python:3.10-slim-bookworm

WORKDIR /workspaces/

RUN apt-get update && \
    apt-get install -y git \
    sudo 

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt