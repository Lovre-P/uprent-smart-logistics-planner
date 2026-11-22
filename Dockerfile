FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    UV_NO_DEV=1 \
    UV_NO_CACHE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable
COPY data/ data/
COPY web/dist/ web/dist/

ENV UV_NO_SYNC=1
EXPOSE 8000
CMD ["uv", "run", "uprent", "serve", "--host", "0.0.0.0", "--port", "8000"]
