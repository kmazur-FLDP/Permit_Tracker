

-- migrations/add_permit_audit_columns.sql

-- Add user tracking for who created a permit
ALTER TABLE permits
  ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);

-- Add user tracking for who last updated a permit
ALTER TABLE permits
  ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Optionally add timestamp of creation and last update (if not already present)
ALTER TABLE permits
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;