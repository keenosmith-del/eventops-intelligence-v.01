# Core Infrastructure

## Purpose

Shared infrastructure components for the
EventOps Intelligence backend.

## Database Connectivity

Module: database.py

The connect_db() function establishes PostgreSQL
connections using Psycopg 3.

## Configuration

Local development reads the repository root .env.

Required values:

- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

Optional values:

- POSTGRES_HOST (defaults to 127.0.0.1)
- POSTGRES_PORT (defaults to 55432)
- DATABASE_URL (takes precedence when supplied)

Production hosting should provide DATABASE_URL
through secure environment configuration.

## Connection Management

Connections are managed using context managers.

Successful operations commit when the context exits.

Failed operations roll back automatically.

Connections are closed after use.

## Security

- No hardcoded database credentials
- Local environment files excluded from Git
- Credentials remain server-side
- Five-second connection timeout
- No public database exposure required

## Current Status

Database connection functionality is implemented.

Knowledge-record persistence, transaction handling
at the repository layer, and database integration
tests will be implemented next.

## Future Improvements

- Connection pooling
- Asynchronous database access where appropriate
- Database readiness checks
- Integration test isolation
- Production connection monitoring
  EOF
