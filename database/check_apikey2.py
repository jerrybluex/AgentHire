import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("SELECT id, enterprise_id, name, api_key_prefix, status FROM enterprise_api_keys LIMIT 5")
rows = cur.fetchall()
print(f"Total API keys: {len(rows)}")
for row in rows:
    print(row)
