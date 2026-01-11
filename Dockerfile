FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN chmod +x /bin/uv

COPY pyproject.toml uv.lock ./

COPY app /app/app
COPY tests /app/tests

RUN uv pip install --system .[dev]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
