import sqlite3
conn = sqlite3.connect('backend/db.sqlite3')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

if 'menus_jour' in tables:
    c.execute("SELECT date_menu, COUNT(*) FROM menus_jour GROUP BY date_menu ORDER BY date_menu DESC LIMIT 10")
    rows = c.fetchall()
    print("\nMenus par date:")
    for r in rows:
        print(f"  {r[0]}: {r[1]} plats")
conn.close()
