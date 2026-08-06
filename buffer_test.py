import requests
import json

token = "04f993lGn4T2nrTFdVrewpOJJZzUVURXsDlwYSi7Xg6"

# Download real image
img_data = requests.get("https://picsum.photos/500").content
with open("real.jpg", "wb") as f:
    f.write(img_data)

# Upload to uguu.se
resp = requests.post(
    "https://uguu.se/upload.php",
    files={"files[]": open("real.jpg", "rb")}
)
uguu_url = resp.json()["files"][0]["url"]
print("Uguu URL:", uguu_url)

# Post to Buffer
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on InvalidInputError { message }
    ... on PostActionSuccess { post { id } }
  }
}
"""
variables = {
    "input": {
        "channelId": "6a74663499afb443491100c1",
        "text": "This is a test post from Uguu image upload.",
        "mode": "shareNow",
        "needsApproval": False,
        "schedulingType": "automatic",
        "metadata": {
            "facebook": { "type": "post" }
        },
        "assets": [{"image": {"url": uguu_url}}]
    }
}
resp2 = requests.post("https://api.buffer.com/", headers=headers, json={"query": mutation, "variables": variables})
print(json.dumps(resp2.json(), indent=2))
