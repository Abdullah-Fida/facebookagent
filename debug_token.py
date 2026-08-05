import requests
from core.config import load_config

config = load_config()
token = config.facebook_access_token

# Check /me
r = requests.get(f"https://graph.facebook.com/v19.0/me?access_token={token}")
print("GET /me response:")
print(r.json())

# Check permissions
r2 = requests.get(f"https://graph.facebook.com/v19.0/me/permissions?access_token={token}")
print("\nPermissions:")
print(r2.json())
