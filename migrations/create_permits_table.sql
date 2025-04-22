CREATE TABLE IF NOT EXISTS permits (
  id SERIAL PRIMARY KEY,
  project_number TEXT    NOT NULL,
  permit_number  TEXT    NOT NULL,
  permit_name    TEXT,
  agency         TEXT,
  application_date DATE,
  issue_date       DATE,
  expiration_date  DATE,
  status         TEXT,
  last_updated   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  archived       BOOLEAN DEFAULT FALSE
);