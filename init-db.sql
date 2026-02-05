-- Grant permissions to nbauser on the public schema
-- This is required for PostgreSQL 15+ where public schema is no longer world-writable by default

GRANT ALL ON SCHEMA public TO nbauser;
GRANT ALL PRIVILEGES ON DATABASE nbaanalytics TO nbauser;

-- Allow nbauser to create tables and manage objects in public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nbauser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nbauser;