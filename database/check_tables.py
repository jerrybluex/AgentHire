import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables: {tables}")
print(f"Count: {len(tables)}")
