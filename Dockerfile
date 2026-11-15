FROM python:3.13-slim-trixie AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target /deps -r requirements.txt

FROM gcr.io/distroless/python3-debian13:nonroot

WORKDIR /app
ENV PYTHONPATH=/deps \
    PYTHONUNBUFFERED=1

COPY --from=builder /deps /deps
COPY notesapp/ ./notesapp/
COPY wsgi.py .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

ENTRYPOINT ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "wsgi:app"]