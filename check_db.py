# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlite3
from config.settings import DB_PATH

# Dev utility: print the saved applications. Reports cleanly when there is
# no database yet instead of crashing on a missing table.
if not DB_PATH.exists():
    print(f"No database found at {DB_PATH}. Add a resume and save an application first.")
else:
    conn = sqlite3.connect(DB_PATH)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "applications" not in tables:
        print(f"Database at {DB_PATH} has no applications table yet. Nothing to show.")
    else:
        cursor = conn.execute('SELECT id, job_title, company_name, job_description_path FROM applications ORDER BY created_at DESC')
        rows = cursor.fetchall()

        print("Applications in database:")
        for i, row in enumerate(rows):
            print(f"Record {i+1}: ID={row[0]}, Title='{row[1]}', Company='{row[2]}', JobDescPath='{row[3]}'")

    conn.close()
