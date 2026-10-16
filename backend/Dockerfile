FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /app/backend
COPY modules/bolton-connect/backend /app/modules/bolton-connect/backend
COPY modules/bolton-connect/frontend /app/modules/bolton-connect/frontend
COPY modules/bolton-connect/data/*.json /app/modules/bolton-connect/data/
COPY modules/bolton-connect/prompts /app/modules/bolton-connect/prompts
COPY modules/adjust/backend /app/modules/adjust/backend
COPY modules/adjust/knowledge /app/modules/adjust/knowledge
COPY config /app/config
COPY data/synthetic /app/data/synthetic
RUN useradd --create-home --uid 10001 civicforge && chown -R civicforge:civicforge /app
USER civicforge
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
