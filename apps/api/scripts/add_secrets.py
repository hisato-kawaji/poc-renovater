import os
from dotenv import load_dotenv
from google.cloud import secretmanager

load_dotenv("../../.env")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

def add_secret_version(secret_id, payload):
    client = secretmanager.SecretManagerServiceClient()
    parent = client.secret_path(project_id, secret_id)
    payload_bytes = payload.encode("UTF-8")
    response = client.add_secret_version(
        request={
            "parent": parent,
            "payload": {"data": payload_bytes},
        }
    )
    print(f"Added version {response.name}")

private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")

if private_key:
    private_key = private_key.strip('"')
    add_secret_version("GITHUB_APP_PRIVATE_KEY", private_key)

if webhook_secret:
    webhook_secret = webhook_secret.strip('"')
    add_secret_version("GITHUB_WEBHOOK_SECRET", webhook_secret)
