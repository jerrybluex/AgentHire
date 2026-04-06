import hmac
import hashlib
import json
import time

agent_id = "agt_tBMYxokB-7_1"
agent_secret = "as_S9Yw7j4sSJgbXCinoGMC3VjedstNHu_WUql2Nfxcjgk"
timestamp = int(time.time())

message = agent_id + str(timestamp)
signature = hmac.new(
    agent_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

payload = {
    "agent_id": agent_id,
    "timestamp": timestamp,
    "signature": signature
}

print(json.dumps(payload, indent=2))
