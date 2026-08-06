import requests
import json
token = "04f993lGn4T2nrTFdVrewpOJJZzUVURXsDlwYSi7Xg6"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
query = """
query {
  __type(name: "ShareMode") { enumValues { name } }
}
"""
resp = requests.post("https://api.buffer.com/", headers=headers, json={"query": query})
print(resp.text)
