import sqlite3

con = sqlite3.connect('storage/aether.db')
cur = con.cursor()
for r in cur.execute("SELECT id, image_id, mode, scale, model, status, output_path, message FROM jobs ORDER BY created_at DESC LIMIT 10"):
    print(r)

