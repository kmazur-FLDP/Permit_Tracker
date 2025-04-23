# scripts/create_admin.py

import os
import sys
# Ensure project root is on Python’s path so we can import db.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from werkzeug.security import generate_password_hash
from db import conn

def create_admin(username, password):
    password_hash = generate_password_hash(password)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, password_hash)
    )
    conn.commit()
    cur.close()
    print(f"Admin user '{username}' created.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_admin.py <username> <password>")
    else:
        create_admin(sys.argv[1], sys.argv[2])