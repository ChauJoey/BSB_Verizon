import os
import base64
import requests

from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
USERNAME = os.getenv("VC_USERNAME")
PASSWORD = os.getenv("VC_PASSWORD")

# =========================
# 获取 token
# =========================

credentials = f"{USERNAME}:{PASSWORD}"

encoded_credentials = base64.b64encode(
    credentials.encode()
).decode()

token_url = "https://fim.api.us.fleetmatics.com/token"

headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Accept": "application/json"
}

response = requests.get(
    token_url,
    headers=headers
)

token = response.text.strip()

print("Token OK")

# =========================
# 调 Driver API
# =========================

api_url = "https://fim.api.us.fleetmatics.com:443/cmd/v1/drivers"

api_headers = {
    "Authorization": (
        f"Atmosphere atmosphere_app_id={APP_ID}, "
        f"Bearer {token}"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json"
}

api_response = requests.get(
    api_url,
    headers=api_headers
)

print("\nStatus:", api_response.status_code)

print("\nResponse:")
print(api_response.text)