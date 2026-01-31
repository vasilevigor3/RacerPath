FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json /app/frontend/package.json
COPY frontend/vite.config.js /app/frontend/vite.config.js
COPY frontend/index.html /app/frontend/index.html
COPY frontend/src /app/frontend/src
RUN npm install --no-fund --no-audit
RUN npm run build

FROM python:3.13-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY backend /app/backend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
