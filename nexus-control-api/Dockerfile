FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt


FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_APP=run.py \
    PYTHONPYCACHEPREFIX=/tmp/pycache

RUN useradd --create-home --uid 1000 nexus

COPY --from=builder /opt/venv /opt/venv
COPY docker/entrypoint.sh docker/espera_db.py docker/bootstrap_esquema.py \
     docker/revision_actual.py /usr/local/bin/
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /app
COPY --chown=nexus:nexus . .
RUN mkdir -p /app/data && chown -R nexus:nexus /app/data

USER nexus
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if b'\"ok\"' in urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).read() else 1)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", \
     "--workers", "1", \
     "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", \
     "--worker-connections", "1000", \
     "--worker-tmp-dir", "/dev/shm", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "60", \
     "--keep-alive", "5", \
     "--limit-request-line", "4094", \
     "--limit-request-fields", "32", \
     "--limit-request-field_size", "8190", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "run:app"]
