# Multi-stage Dockerfile combining base and app
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# 非rootユーザー & redis-cli install
RUN apt-get update && apt-get install -y redis-tools && rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --gecos "" app && mkdir -p /app && chown -R app:app /app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
USER app

FROM base AS app
WORKDIR /app
ENV PYTHONPATH=/app
COPY --chown=app:app src ./src
COPY --chown=app:app schema ./schema
COPY --chown=app:app playground.py cli.py ./
# ROLE で挙動切替（watcher/curator/planner/synthesizer/archivist）
CMD ["sh", "-c", "python playground.py --role ${ROLE:-watcher} --hello"]