FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV PORT=8001 METRICS_PORT=9001
EXPOSE 8001 9001
CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT} & python -m http.server ${METRICS_PORT} >/dev/null 2>&1 & tail -f /dev/null"]