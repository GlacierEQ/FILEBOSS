# Database Migrations

This directory contains database migration scripts managed by [Alembic](https://alembic.sqlalchemy.org/).

## Directory Structure

- `versions/` - Contains individual migration scripts
- `env.py` - Main migration environment configuration
- `script.py.mako` - Template for new migration files
- `README.md` - This file

## Common Tasks

### Create a New Migration

```bash
# Create a new migration with autogenerate
# (run after making model changes)
alembic revision --autogenerate -m "Description of changes"

# Create an empty migration (for manual changes)
alembic revision -m "Description of changes"
```

### Run Migrations

```bash
# Upgrade to the latest version
alembic upgrade head

# Upgrade to a specific version
alembic upgrade <revision>

# Run a specific number of migrations
alembic upgrade +2  # upgrade 2 versions
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific version
alembic downgrade <revision>

# Rollback all migrations
alembic downgrade base
```

### Other Useful Commands

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show migration history as a tree
alembic history --verbose

# Show SQL for a migration (without running it)
alembic upgrade <revision> --sql
```

## Best Practices

1. **Always** create a new migration when making schema changes
2. Test both `upgrade` and `downgrade` operations
3. Keep migrations small and focused on a single change when possible
4. Include descriptive messages with each migration
5. Never modify existing migration files after they've been committed
6. Use `alembic check` to verify the migration environment

## Troubleshooting

### Common Issues

- **Database connection issues**: Verify your `.env` file contains the correct database URL
- **Migration conflicts**: Use `alembic heads` to identify and resolve multiple heads
- **Autogenerate issues**: Sometimes manual intervention is needed for complex schema changes

### Resetting Migrations

If you need to start fresh:

```bash
# 1. Delete all migration files in versions/
# 2. Initialize fresh migrations
alembic revision --autogenerate -m "Initial migration"
# 3. Apply the migration
alembic upgrade head
```
