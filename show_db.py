import sqlite3

conn = sqlite3.connect("support_chat.db")
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';")]
print("tables:", tables)

for t in tables:
    try:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    except Exception as e:
        cnt = f"ERR: {e}"
    print(t, cnt)

conn.close()
