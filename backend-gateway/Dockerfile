# ---- Frontend build ----
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# ---- Python runtime ----
FROM python:3.11-slim
WORKDIR /app
COPY backend-gateway/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
COPY --from=frontend /build/frontend/dist /app/dist
COPY backend-gateway/gateway/ /app/gateway/
