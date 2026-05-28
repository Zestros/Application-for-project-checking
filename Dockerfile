FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY project_health ./project_health

RUN python -m pip install --no-cache-dir .

WORKDIR /workspace

ENTRYPOINT ["pha"]
CMD ["scan", "."]
