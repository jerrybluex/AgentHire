import hmac, hashlib, json, time, sys

agent_id = sys.argv[1]
agent_secret = sys.argv[2]
timestamp = int(time.time())
message = agent_id + str(timestamp)
signature = hmac.new(agent_secret.encode(), message.encode(), hashlib.sha256).hexdigest()
print(json.dumps({"agent_id": agent_id, "timestamp": timestamp, "signature": signature}))
