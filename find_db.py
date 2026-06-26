import sqlite3
import os
# Find all db.sqlite3 files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.sqlite3'):
            print(os.path.join(root, file))
