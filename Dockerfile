FROM python:3.14-slim
WORKDIR /app
COPY pyproject.toml .
COPY cartei_db/ cartei_db/
COPY alembic.ini .
COPY migrations/ migrations/
RUN pip install --no-cache-dir .
CMD ["alembic", "upgrade", "head"]
