# syntax=docker/dockerfile:1
# Multi-stage build for EdgeGuard.
#   test    — runs the unit tests (used by the CI pipeline)
#   runtime — small production image with the CLI and the web interface

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

# ---------------------------------------------------------------- test stage
FROM base AS test
RUN pip install ".[dev]"
COPY tests ./tests
RUN mkdir -p /reports
# The test container writes a JUnit report that Jenkins copies out with `docker cp`.
CMD ["pytest", "--junitxml=/reports/junit.xml"]

# ---------------------------------------------------------------- runtime stage
FROM base AS runtime
RUN pip install ".[ui]" \
    && useradd --create-home --uid 1001 appuser \
    && mkdir -p /app/results \
    && chown appuser /app/results
COPY app.py ./
USER 1001
EXPOSE 8501
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1
# Default: web interface. CLI example: docker run --rm edgeguard edgeguard benchmark
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
