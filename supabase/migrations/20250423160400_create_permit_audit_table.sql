-- migrations/create_permit_audit_table.sql
CREATE TABLE IF NOT EXISTS permit_audit (
  id         SERIAL PRIMARY KEY,
  permit_id  INTEGER  NOT NULL REFERENCES permits(id),
  user_id    INTEGER  NOT NULL REFERENCES users(id),
  action     TEXT     NOT NULL,
  timestamp  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);