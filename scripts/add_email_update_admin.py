#!/usr/bin/env python3
import os, sys
from dotenv import load_dotenv

# allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from db import conn

def ensure_email_column():
    sql = """
    ALTER TABLE users
      ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    print("✅ Ensured `email` column exists on users table.")

def set_admin_email(admin_username, admin_email):
    sql = "UPDATE users SET email = %s WHERE username = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (admin_email, admin_username))
        conn.commit()
    print(f"✅ Set email for user '{admin_username}' to '{admin_email}'.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python add_email_and_update_admin.py <admin-username> <admin-email>")
        sys.exit(1)

    username, email = sys.argv[1], sys.argv[2]
    ensure_email_column()
    set_admin_email(username, email)