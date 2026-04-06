import hmac
import hashlib
import json
import time

agent_id = "agt_3j4-HRcpTFVx"
agent_secret = "as_ZvJG6WMzHVTiKLGmCIJjX7pCG6wn0xwKPKow3UtFne8"
timestamp = int(time.time())

message = agent_id + str(timestamp)
signature = hmac.new(
    agent_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

print(json.dumps({"timestamp": timestamp, "signature": signature}, indent=2))
