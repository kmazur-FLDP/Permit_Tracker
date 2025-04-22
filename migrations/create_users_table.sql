CREATE TABLE IF NOT EXISTS users (
  id            SERIAL PRIMARY KEY,
  username      TEXT   UNIQUE NOT NULL,
  password_hash TEXT   NOT NULL,
  role          TEXT   NOT NULL DEFAULT 'user'
);