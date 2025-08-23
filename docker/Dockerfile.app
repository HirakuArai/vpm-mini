FROM vpm-mini/base:latest AS app
WORKDIR /app
ENV PYTHONPATH=/app
COPY src ./src
COPY playground.py cli.py ./
# ROLE で挙動切替（watcher/curator/planner/synthesizer/archivist）
CMD ["python","playground.py","--role","${ROLE:-watcher}","--hello"]