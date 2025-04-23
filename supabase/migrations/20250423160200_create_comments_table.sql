-- migrations/create_comments_table.sql

CREATE TABLE IF NOT EXISTS comments (
  id         SERIAL PRIMARY KEY,
  permit_id  INTEGER NOT NULL REFERENCES permits(id) ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  content    TEXT    NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);