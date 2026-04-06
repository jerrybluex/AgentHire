import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()

# Check columns for key tables
tables = ['tenants', 'principals', 'credentials', 'enterprises', 'job_postings', 'applications', 
          'application_events', 'job_versions', 'contact_unlocks', 'enterprise_verification_cases', 'metering_events']

for table in tables:
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table}' 
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print(f"\n{table}:")
    for col in cols:
        print(f"  {col[0]}: {col[1]}")
