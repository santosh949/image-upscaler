import sqlite3

con = sqlite3.connect('storage/aether.db')
cur = con.cursor()
query = "SELECT id, original_filename, width, height, storage_path FROM images WHERE original_filename NOT IN ('test_input.png', 'safe.png') ORDER BY created_at ASC"
for row in cur.execute(query):
    print(row)

