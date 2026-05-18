from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)

WEBHOOK_USERNAME = os.getenv("WEBHOOK_USERNAME")
WEBHOOK_PASSWORD = os.getenv("WEBHOOK_PASSWORD")


# =========================
# Basic Auth 验证
# =========================

def verify_basic_auth(auth_header: str):

    if not auth_header:
        return False

    try:
        scheme, credentials = auth_header.split()

        if scheme.lower() != "basic":
            return False

        import base64

        decoded = base64.b64decode(credentials).decode()

        username, password = decoded.split(":")

        return (
            username == WEBHOOK_USERNAME
            and password == WEBHOOK_PASSWORD
        )

    except Exception:
        return False


# =========================
# Health Check
# =========================

@app.get("/")
async def health():
    return {
        "status": "ok"
    }


# =========================
# GPS Webhook
# =========================

@app.post("/webhook/gps")
async def gps_webhook(request: Request):

    # -------------------------
    # Basic Auth
    # -------------------------

    auth_header = request.headers.get("Authorization")

    if not verify_basic_auth(auth_header):

        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"},
            headers={
                "WWW-Authenticate": "Basic"
            }
        )

    # -------------------------
    # SNS Message Type
    # -------------------------

    message_type = request.headers.get(
        "x-amz-sns-message-type"
    )

    body = await request.json()

    logging.info(f"Message Type: {message_type}")
    logging.info(body)

    # =========================
    # Subscription Confirmation
    # =========================

    if message_type == "SubscriptionConfirmation":

        subscribe_url = body.get("SubscribeURL")

        if subscribe_url:

            try:

                response = requests.get(subscribe_url)

                logging.info(
                    f"Subscription confirmed: {response.status_code}"
                )

            except Exception as e:

                logging.error(
                    f"Subscription confirmation failed: {str(e)}"
                )

                raise HTTPException(
                    status_code=500,
                    detail="Subscription confirmation failed"
                )

    # =========================
    # GPS Notification
    # =========================

    elif message_type == "Notification":

        data = body.get("data", {})

        logging.info("GPS DATA RECEIVED")

        logging.info(
            f"Vehicle: {data.get('vehicle', {}).get('name')}"
        )

        logging.info(
            f"Driver: {data.get('driver', {}).get('driverFirstName')}"
        )

        logging.info(
            f"Latitude: {data.get('latitude')}"
        )

        logging.info(
            f"Longitude: {data.get('longitude')}"
        )

        logging.info(
            f"Speed: {data.get('speedKmph')}"
        )

        # TODO:
        # 存数据库
        # 推送Redis/Kafka
        # AI Dispatcher分析
        # Geofence判断

    return {
        "success": True
    }