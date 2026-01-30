from flask import Flask, request
import os
import datetime
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

# 🔐 Webhook verify token
VERIFY_TOKEN = "aryanstore"

# 📞 OWNER WHATSAPP NUMBER
OWNER_NUMBER = "917876772622"

# 🔑 WHATSAPP CLOUD API DETAILS
ACCESS_TOKEN = "EAAcawvprIgwBQiJw988wMwc3HC4iahoGG0eyLKIt59x8BUNl7P4htg5Ia2UW6Egdl9CytrDzGx1wjmOj1rokDZCot49w3xFyCi5ZArypJLzoaKZCQpgnCF7lqsKbkbQSazSdF5IxmSAX4TcmPt4cZCK7wij3gBXBU4UcMv3G2a9e6eNFTer9qQUwgGto5IQetsIIkf3CAtEWGQwtnpWx9W9bugPAJXlDvZByAqZAXF1BTv7TRZBOuyL2Xe2KN2cBFTHyYWQlqcc3kgRsDXYwc4i"

PHONE_NUMBER_ID = "952800504590356"


# -------------------- UTILITIES --------------------

def generate_order_number():
    return "ARY-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def create_pdf(order_no, items_text):
    file_path = f"/tmp/{order_no}.pdf"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "ARYAN STORE")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Order No: {order_no}")
    y -= 15
    c.drawString(
        40, y,
        f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
    )
    y -= 25

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Item")
    c.drawString(400, y, "Amount")
    y -= 10
    c.line(40, y, 550, y)
    y -= 18

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
    return file_path


def send_pdf_on_whatsapp(pdf_path, caption):
    try:
        print("🚀 UPLOADING PDF", flush=True)

        upload_url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        # ✅ FINAL FIX — everything as multipart
        files = {
            "file": (
                "order.pdf",
                open(pdf_path, "rb"),
                "application/pdf"
            ),
            "messaging_product": (None, "whatsapp"),
            "type": (None, "application/pdf")
        }

        upload_response = requests.post(
            upload_url,
            headers=headers,
            files=files
        )

        print("MEDIA UPLOAD RESPONSE:", upload_response.text, flush=True)

        upload_json = upload_response.json()
        media_id = upload_json.get("id")

        if not media_id:
            print("❌ MEDIA ID NOT RECEIVED – STOPPING", flush=True)
            return

        print("✅ MEDIA ID RECEIVED:", media_id, flush=True)

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

        send_response = requests.post(
            message_url,
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        print("SEND MESSAGE RESPONSE:", send_response.text, flush=True)

    except Exception as e:
        print("❌ SEND PDF ERROR:", e, flush=True)


# -------------------- ROUTES --------------------

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
        print("🔥 POST RECEIVED FROM META", flush=True)

        data = request.json
        print(data, flush=True)

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")

            if messages:
                msg = messages[0]
                items_text = msg["text"]["body"]

                print("📦 ITEMS RECEIVED:", flush=True)
                print(items_text, flush=True)

                order_no = generate_order_number()
                print("🧾 ORDER NO:", order_no, flush=True)

                pdf_path = create_pdf(order_no, items_text)
                print("📄 PDF CREATED:", pdf_path, flush=True)

                send_pdf_on_whatsapp(
                    pdf_path,
                    caption=f"New Order Received\nOrder No: {order_no}"
                )

        except Exception as e:
            print("❌ ERROR IN WEBHOOK:", e, flush=True)

        return "EVENT_RECEIVED", 200


# -------------------- MAIN --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
