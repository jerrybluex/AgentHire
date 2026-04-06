import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()
# Convert text[] to JSON by casting each element and creating a JSON array
cur.execute("""
    ALTER TABLE job_postings 
    ALTER COLUMN responsibilities 
    TYPE JSON 
    USING CASE WHEN responsibilities IS NULL THEN NULL ELSE array_to_json(responsibilities)::JSON END
""")
conn.commit()
print("Changed responsibilities from text[] to JSON")
