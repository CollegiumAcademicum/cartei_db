# Cartei DB

Shared PostgreSQL data layer for CArtei tenant management.

## Setup

```bash
cp .env.example .env
# fill in passwords in .env
./db-init.sh
```

This starts the DB container, runs Alembic migrations, and applies role grants.

## Running tests

```bash
DATABASE_URL=postgresql+psycopg://cartei:cartei@localhost:5432/cartei uv run pytest
```

## Using in a microservice

```toml
# pyproject.toml
dependencies = [
    "cartei-db @ git+https://github.com/CollegiumAcademicum/cartei_db.git",
]
```

```python
from cartei_db.models import Tenant
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine(os.environ["DATABASE_URL"])
with Session(engine) as s:
    tenants = s.query(Tenant).all()
```

Each service connects with its own scoped DB user (see `db-grants.sql`).
