from flask import Flask, request
import os
import datetime
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from requests_toolbelt.multipart.encoder import MultipartEncoder

app = Flask(__name__)

VERIFY_TOKEN = "aryanstore"
OWNER_NUMBER = "917876772622"

ACCESS_TOKEN = "EAAcawvprIgwBQl5LDdDoaydqaWMX9F61LgWUeXXth1pkRNvCEtgTYhHQDteJGi8PNVhxtUomuZAkfd2MCRGxSQZAhJVGsZBrtWNjNZBGAJAZAWX2EbkWKoXVnq67dXyyNyOLYB8KMeA8aOZAQLZB9m7TgubZBCzVBl2u7EgOKdllySaPm2dJLJD5orQfCBX7SRqzD29Arjr8zOLW8PGYW5yNOZAA52SOpNXreNP7W64os0K9SVqZA3CRSS3TZC0V8GGES7KlrTr8VJKt4s4Xl2QukfNwwZDZD"
PHONE_NUMBER_ID = "952800504590356"


def generate_order_number():
    return "ARY-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def create_pdf(order_no, items_text):
    path = f"/tmp/{order_no}.pdf"

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, "ARYAN STORE")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Order No: {order_no}")
    y -= 15
    c.drawString(40, y, datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p"))
    y -= 25

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Item")
    c.drawString(400, y, "Amount")
    y -= 15

    c.setFont("Helvetica", 11)
    for line in items_text.split("\n"):
        if y < 60:
            c.showPage()
            y = h - 60
        c.drawString(40, y, line)
        y -= 18

    c.save()
    return path


def send_pdf_on_whatsapp(pdf_path, caption):
    print("🚀 Uploading PDF", flush=True)

    encoder = MultipartEncoder(
        fields={
            "messaging_product": "whatsapp",
            "type": "application/pdf",
            "file": (
                os.path.basename(pdf_path),
                open(pdf_path, "rb"),
                "application/pdf"
            )
        }
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": encoder.content_type
    }

    upload_url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"
    r = requests.post(upload_url, headers=headers, data=encoder)

    print("MEDIA UPLOAD RESPONSE:", r.text, flush=True)

    media_id = r.json().get("id")
    if not media_id:
        print("❌ Media upload failed", flush=True)
        return

    msg_url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_NUMBER,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption
        }
    }

    r2 = requests.post(
        msg_url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print("SEND MESSAGE RESPONSE:", r2.text, flush=True)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Invalid token", 403

    data = request.json
    print("📩 Webhook received", flush=True)

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        text = msg["text"]["body"]

        order_no = generate_order_number()
        pdf = create_pdf(order_no, text)

        send_pdf_on_whatsapp(pdf, f"New Order\nOrder No: {order_no}")

    except Exception as e:
        print("❌ ERROR:", e, flush=True)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
