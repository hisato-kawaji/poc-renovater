import requests
import io
import zipfile

# 1. Create a dummy zip
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
    zf.writestr("package.json", '{"name": "test-project"}')
    zf.writestr("src/index.js", 'console.log("hello");')

zip_buffer.seek(0)

print("1. Uploading...")
res = requests.post("http://localhost:8000/api/uploads", files={"file": ("test.zip", zip_buffer, "application/zip")})
print(res.status_code, res.text)
upload_id = res.json().get("uploadId")

print(f"2. Analyzing {upload_id}...")
res = requests.post("http://localhost:8000/api/agents:analyze", json={"uploadId": upload_id})
print(res.status_code, res.text)

print("3. Registering...")
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}:register")
print(res.status_code, res.text)

print("4. Planning Issues...")
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}/issues:plan")
print(res.status_code, res.text)

print("5. Implementing Issue 1...")
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}/issues/1:implement")
print(res.status_code, res.text)

print("6. Reviewing & Deploying PR 1...")
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}/pulls/1:review")
print(res.status_code, res.text)
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}/pulls/1:deploy-preview")
print(res.status_code, res.text)

print("7. Approving PR 1...")
res = requests.post(f"http://localhost:8000/api/agents/{upload_id}/pulls/1:approve")
print(res.status_code, res.text)
