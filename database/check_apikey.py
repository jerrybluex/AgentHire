import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("""
    SELECT id, enterprise_id, name, api_key_prefix, status 
    FROM enterprise_api_keys 
    WHERE enterprise_id = 'ent_yJF_6A7jlpE_'
""")
for row in cur.fetchall():
    print(row)
