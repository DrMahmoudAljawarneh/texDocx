FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    imagemagick \
    poppler-utils \
    librsvg2-bin \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
COPY . .
