import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("ALTER TABLE agents ALTER COLUMN agent_secret_hash DROP NOT NULL")
conn.commit()
print("Made agent_secret_hash nullable")
