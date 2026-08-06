import requests

with open("test.jpg", "wb") as f:
    f.write(b"dummy image data")

resp = requests.post(
    "https://catbox.moe/user/api.php",
    data={"reqtype": "fileupload"},
    files={"fileToUpload": open("test.jpg", "rb")}
)
print(resp.text)
