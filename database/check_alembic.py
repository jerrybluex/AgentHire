import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("SELECT version FROM alembic_version")
print(f"Alembic version: {cur.fetchone()}")
