FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --python 3.12 --frozen --no-cache

COPY . .

EXPOSE 7860

ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD [ "uv", "run", "frontend.py" ]