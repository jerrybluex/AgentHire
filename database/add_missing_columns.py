import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()

# Add missing columns to agents table
cols_to_add_agents = [
    ("tenant_id", "VARCHAR(64)"),
    ("principal_id", "VARCHAR(64)"),
    ("api_secret_encrypted", "TEXT"),
]

for col_name, col_type in cols_to_add_agents:
    try:
        cur.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_type}")
        print(f"Added {col_name} to agents")
    except Exception as e:
        if "already exists" in str(e):
            print(f"Column {col_name} already exists in agents")
        else:
            print(f"Error adding {col_name}: {e}")

# Add tenant_id to enterprises table
try:
    cur.execute("ALTER TABLE enterprises ADD COLUMN tenant_id VARCHAR(64)")
    print("Added tenant_id to enterprises")
except Exception as e:
    if "already exists" in str(e):
        print("Column tenant_id already exists in enterprises")
    else:
        print(f"Error adding tenant_id: {e}")

# Add tenant_id to job_postings table
try:
    cur.execute("ALTER TABLE job_postings ADD COLUMN tenant_id VARCHAR(64)")
    print("Added tenant_id to job_postings")
except Exception as e:
    if "already exists" in str(e):
        print("Column tenant_id already exists in job_postings")
    else:
        print(f"Error adding tenant_id: {e}")

conn.commit()
print("\nDone!")
