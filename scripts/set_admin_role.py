# scripts/set_admin_role.py

import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from db import conn

def set_admin_role(username='admin'):
    sql = "UPDATE users SET role = 'admin' WHERE username = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (username,))
        conn.commit()
        print(f"✅ Role for user '{username}' set to admin.")

if __name__ == '__main__':
    set_admin_role()