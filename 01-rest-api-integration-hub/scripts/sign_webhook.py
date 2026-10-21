import hashlib
import hmac
import os
import time

body = os.environ.get("SIGN_BODY")
if body is None:
    raise SystemExit("SIGN_BODY must be defined")
secret = os.environ.get("WEBHOOK_HMAC_SECRET")
if not secret:
    raise SystemExit("WEBHOOK_HMAC_SECRET must be set (see .env.example)")
timestamp = os.environ.get("SIGN_TIMESTAMP")
if not timestamp:
    timestamp = str(int(time.time()))
signing = f"{timestamp}.{body}"
signature = "sha256=" + hmac.new(secret.encode(), signing.encode(), hashlib.sha256).hexdigest()
print(timestamp)
print(signature)
