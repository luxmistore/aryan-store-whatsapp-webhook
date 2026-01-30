from flask import Flask, request
import os
import datetime
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

VERIFY_TOKEN = "aryanstore"
OWNER_NUMBER = "917876772622"

ACCESS_TOKEN = "EAAcawvprIgwBQp1t4QCtoExiGw2EeGbFKSbyd7kYik0oL1ZAZBUQ3NUYpx44bZCJ5l5XVEdUXUXzXzjzE8pX36ZA0i4jTgsyToLdPrjDJOs1VdH6TTArr2XxOXqM3VuYbw1X0HmXJHMQZCxu8IrYbVdSL6AfPKjfzx6HomVxx0AlZCh7XnL9tg2BcgZCaz7sBsRBYZADm436BEEjkwQZByHuU3bLMM2NsoOaQKNyv7jmLSHsNQh5Pjr8dIEIUZCgaiZATm4AdLcKDAyTDZBljZBdCUngRkAZDZD"
PHONE_NUMBER_ID = "952800504590356"


# -------------------- UTILITIES --------------------

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
    c.drawString(
        40, y,
        f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
    )
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


def send_text_on_whatsapp(message):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": OWNER_NUMBER,
        "type": "text",
        "text": {"body": message}
    }

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print("TEXT MESSAGE RESPONSE:", r.text, flush=True)


# -------------------- ROUTES --------------------

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
        items_text = msg["text"]["body"]

        order_no = generate_order_number()
        pdf_path = create_pdf(order_no, items_text)

        message = (
            f"🧾 New Order Received\n"
            f"Order No: {order_no}\n\n"
            f"Items:\n{items_text}\n\n"
            f"(PDF generated and ready to print)"
        )

        send_text_on_whatsapp(message)

        print("✅ ORDER PROCESSED:", pdf_path, flush=True)

    except Exception as e:
        print("❌ ERROR:", e, flush=True)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
