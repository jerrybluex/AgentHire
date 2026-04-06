import hashlib
import psycopg2
conn = psycopg2.connect('postgresql://agenthire:agenthire123@localhost:5432/agenthire')
cur = conn.cursor()

api_key = "ak_s_D0Oi6jmy8WIcd9L6Dn_bLoggTZZh3Yp5RDwM-eINo"
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
api_key_prefix = api_key[:12]  # First 12 chars as prefix

enterprise_id = "ent_yJF_6A7jlpE_"
print(f"API key prefix: {api_key_prefix}")
print(f"API key hash: {api_key_hash}")

cur.execute("""
    INSERT INTO enterprise_api_keys (id, enterprise_id, name, api_key_hash, api_key_prefix, plan, rate_limit, status)
    VALUES ('key_fix001', %s, 'Primary API Key', %s, %s, 'pay_as_you_go', 100, 'active')
""", (enterprise_id, api_key_hash, api_key_prefix))
conn.commit()
print(f"Inserted: {cur.rowcount} rows")
