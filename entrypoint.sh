#!/bin/bash
set -e  # Exit on error

echo "Starting migration process..."
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Database host: $DB_HOST"
echo "Database name: $DB_NAME"

if [ "${1}" = "migrate" ]; then
    echo "Running database migrations..."
    # Show current migration version
    echo "Current migration version:"
    python -m alembic current
    
    # Show pending migrations
    echo "Migration history:"
    python -m alembic history
    
    echo "Running upgrade to head..."
    # Run migrations
    python -m alembic upgrade head
    
    # Verify final version
    echo "Final migration version:"
    python -m alembic current
    
    # Exit code handling
    if [ $? -eq 0 ]; then
        echo "Migration completed successfully"
        echo "Migration history after upgrade:"
        python -m alembic history
    else
        echo "Migration failed"
        exit 1
    fi
elif [ "${1}" = "uvicorn" ]; then
    echo "Starting FastAPI application..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    exec "$@"
fi