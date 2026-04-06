import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
cur.execute("""
    UPDATE enterprise_verification_cases 
    SET status = 'under_review', reviewed_by = 'admin', reviewed_at = NOW()
    WHERE id = 'evc_RmDWqOkAujxA'
""")
conn.commit()
print(f"Updated rows: {cur.rowcount}")
cur.execute("SELECT id, status FROM enterprise_verification_cases WHERE id = 'evc_RmDWqOkAujxA'")
print(cur.fetchone())
