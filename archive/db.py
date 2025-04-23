import os
import pathlib
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

# Connect
conn = psycopg2.connect(
    DATABASE_URL,
    sslmode='require',
    cursor_factory=RealDictCursor
)
print("✅ Connected to PostgreSQL database")

# Only core table creation migrations for now
migration_files = [
     'create_permits_table.sql',
     'create_users_table.sql',
   'create_comments_table.sql',    # ← new migration
   'create_permit_audit_table.sql',  # ← new migration
   'create_attachments_table.sql',  # ← new migration
   'add_permit_audit_columns.sql',  # ← new migration
]

for fname in migration_files:
    print(f"🔄 Starting migration '{fname}'")
    path = pathlib.Path(__file__).parent / 'migrations' / fname

    # Read the SQL
    try:
        sql = path.read_text()
    except FileNotFoundError:
        print(f"⚠️ Migration file `{fname}` not found, skipping.")
        continue

    # Skip empty files
    if not sql.strip():
        print(f"⚠️ Migration file `{fname}` is empty, skipping.")
        continue

    # Execute the migration
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
        print(f"✅ `{fname}` applied")
    except Exception as e:
        print(f"⚠️ Migration `{fname}` failed: {e}")
        continue