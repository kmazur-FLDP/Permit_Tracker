# scripts/add_role_column.py

import os, sys
# ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from db import conn

def add_role_column():
    sql = """
    ALTER TABLE users
      ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
        print("✅ `users.role` column has been added (or already existed).")

if __name__ == '__main__':
    add_role_column()