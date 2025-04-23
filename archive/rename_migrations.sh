#!/usr/bin/env bash

# This script renames migration files in supabase/migrations to include timestamp prefixes,
# then pushes them to Supabase. It skips any files that are already renamed.

# Define the mapping of original filenames to timestamped filenames
declare -a mappings=(
  "create_users_table.sql:20250423160000_create_users_table.sql"
  "create_permits_table.sql:20250423160100_create_permits_table.sql"
  "create_comments_table.sql:20250423160200_create_comments_table.sql"
  "create_attachments_table.sql:20250423160300_create_attachments_table.sql"
  "create_permit_audit_table.sql:20250423160400_create_permit_audit_table.sql"
  "add_permit_audit_columns.sql:20250423160500_add_permit_audit_columns.sql"
  "add_role_column.sql:20250423160600_add_role_column.sql"
  "add_archived_column.sql:20250423160700_add_archived_column.sql"
  "add_email_column.sql:20250423160800_add_email_column.sql"
)

# Navigate to the migrations directory
cd supabase/migrations || { echo "Directory supabase/migrations not found"; exit 1; }

# Process each mapping
for map in "${mappings[@]}"; do
  IFS=":" read -r old_name new_name <<< "$map"
  if [[ -e "$old_name" ]]; then
    mv "$old_name" "$new_name"
    echo "Renamed $old_name -> $new_name"
  else
    echo "Skipping $old_name (not found)"
  fi
done

echo -e "\nFinal migration files:"
ls -1 *.sql

# Return to project root and push migrations
cd - >/dev/null || exit 1

echo -e "\nPushing migrations to Supabase..."
supabase db push
