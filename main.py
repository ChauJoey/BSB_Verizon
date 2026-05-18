from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import logging
import os
import json
import base64

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)

WEBHOOK_USERNAME = os.getenv("WEBHOOK_USERNAME")
WEBHOOK_PASSWORD = os.getenv("WEBHOOK_PASSWORD")


# =========================================
# Basic Auth
# =========================================

def verify_basic_auth(auth_header: str):

    if not auth_header:
        return False

    try:

        scheme, credentials = auth_header.split()

        if scheme.lower() != "basic":
            return False

        decoded = base64.b64decode(
            credentials
        ).decode()

        username, password = decoded.split(":")

        return (
            username == WEBHOOK_USERNAME
            and password == WEBHOOK_PASSWORD
        )

    except Exception as e:

        logging.error(str(e))

        return False


# =========================================
# Health Check
# =========================================

@app.get("/")
async def root():

    return {
        "status": "ok"
    }


@app.get("/webhook/gps")
async def gps_get():

    return {
        "webhook": "running"
    }


# =========================================
# GPS Webhook
# =========================================

@app.post("/webhook/gps")
async def gps_webhook(request: Request):

    # -------------------------------------
    # Basic Auth
    # -------------------------------------

    auth_header = request.headers.get(
        "Authorization"
    )

    if not verify_basic_auth(auth_header):

        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized"
            },
            headers={
                "WWW-Authenticate": "Basic"
            }
        )

    # -------------------------------------
    # SNS Message Type
    # -------------------------------------

    message_type = request.headers.get(
        "x-amz-sns-message-type"
    )

    logging.info(f"Message Type: {message_type}")

    # -------------------------------------
    # Read raw body
    # SNS uses text/plain
    # -------------------------------------

    raw_body = await request.body()

    body = json.loads(
        raw_body.decode()
    )

    logging.info(body)

    # =====================================
    # Subscription Confirmation
    # =====================================

    if message_type == "SubscriptionConfirmation":

        subscribe_url = body.get(
            "SubscribeURL"
        )

        logging.info(
            f"Confirming subscription: {subscribe_url}"
        )

        try:

            response = requests.get(
                subscribe_url
            )

            logging.info(
                f"Subscription confirmed: {response.status_code}"
            )

        except Exception as e:

            logging.error(
                f"Subscription confirmation failed: {str(e)}"
            )

    # =====================================
    # GPS Notification
    # =====================================

    elif message_type == "Notification":

        data = body.get("data", {})

        logging.info(
            "GPS DATA RECEIVED"
        )

        vehicle = data.get("vehicle", {})
        driver = data.get("driver", {})
        address = data.get("address", {})

        logging.info(
            f"Vehicle: {vehicle.get('name')}"
        )

        logging.info(
            f"Driver: "
            f"{driver.get('driverFirstName')} "
            f"{driver.get('driverLastName')}"
        )

        logging.info(
            f"Latitude: {data.get('latitude')}"
        )

        logging.info(
            f"Longitude: {data.get('longitude')}"
        )

        logging.info(
            f"Speed: {data.get('speedKmph')} km/h"
        )

        logging.info(
            f"State: {data.get('displayState')}"
        )

        logging.info(
            f"Address: "
            f"{address.get('addressLine1')}"
        )

        # TODO:
        # Save to PostgreSQL
        # Push to Redis/Kafka
        # AI Dispatcher
        # Geofence Logic

    else:

        logging.warning(
            f"Unknown message type: {message_type}"
        )

    # =====================================
    # MUST return 200
    # =====================================

    return {
        "success": True
    }