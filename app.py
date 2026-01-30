from flask import Flask, request
import os
import datetime
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

VERIFY_TOKEN = "aryanstore"

# 🔹 OWNER WHATSAPP NUMBER (YOU)
OWNER_NUMBER = "917876772622"

# 🔹 WHATSAPP API DETAILS (FILL THESE)
ACCESS_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "952800504590356"

def generate_order_number():
    today = datetime.datetime.now().strftime("%Y%m%d")
    time_part = datetime.datetime.now().strftime("%H%M%S")
    return f"ARY-{today}-{time_part}"

def create_pdf(order_no, items_text):
    filename = f"/tmp/{order_no}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 40

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "ARYAN STORE")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Order No: {order_no}")
    y -= 15
    c.drawString(40, y, f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}")
    y -= 25

    # Table header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Item")
    c.drawString(400, y, "Amount")
    y -= 10
    c.line(40, y, 550, y)
    y -= 15

    # Items
    c.setFont("Helvetica", 11)
    for line in items_text.split("\n"):
        if y < 60:
            c.showPage()
            y = height - 60
        c.drawString(40, y, line)
        y -= 18

    y -= 20
    c.line(40, y, 550, y)
    y -= 20
    c.drawString(40, y, "Total Amount: __________________")

    c.save()
    return filename

def send_pdf_on_whatsapp(pdf_path, caption):
    # Upload media
    upload_url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    files = {
        "file": open(pdf_path, "rb"),
        "type": (None, "application/pdf"),
        "messaging_product": (None, "whatsapp")
    }

    upload_response = requests.post(upload_url, headers=headers, files=files)
    media_id = upload_response.json().get("id")

    # Send document
    message_url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_NUMBER,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption
        }
    }

    requests.post(
        message_url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )

@app.route("/", methods=["GET"])
def home():
    return "Aryan Store Webhook Running"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Verification failed", 403

    if request.method == "POST":
        data = request.json

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")

            if messages:
                msg = messages[0]
                items_text = msg["text"]["body"]

                order_no = generate_order_number()
                pdf_path = create_pdf(order_no, items_text)

                send_pdf_on_whatsapp(
                    pdf_path,
                    caption=f"New Order Received\nOrder No: {order_no}"
                )

        except Exception as e:
            print("ERROR:", e)

        return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
