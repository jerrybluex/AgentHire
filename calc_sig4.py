import hmac
import hashlib
import json
import time

agent_id = "agt_FtYmG6Feef0L"
agent_secret = "as_Mtc5jXABC7qjfEAMblN0DmM-ydLhXF1mm5K_zE-LVKc"
timestamp = int(time.time())

message = agent_id + str(timestamp)
signature = hmac.new(
    agent_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

print(json.dumps({"agent_id": agent_id, "timestamp": timestamp, "signature": signature}, indent=2))
