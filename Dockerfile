FROM python:3.10-slim-bookworm

WORKDIR /workspaces/

RUN apt-get update && \
    apt-get install -y git \
    sudo 
COPY . .
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7861

# CMD ["python", "chat_app.py"]