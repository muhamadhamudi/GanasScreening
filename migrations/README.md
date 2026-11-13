# Database schema

The initial schema is created idempotently with `db.create_all()` during application startup. Schema changes in future releases should be introduced through versioned SQLAlchemy/Alembic migrations before production rollout; do not delete the SQLite database to apply an update.
