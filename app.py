from flask import Flask, request
import os
import datetime

app = Flask(__name__)

# Verify token (same as Meta webhook verify token)
VERIFY_TOKEN = "aryanstore"

@app.route("/", methods=["GET"])
def home():
    return "Aryan Store Webhook Running"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔹 Webhook verification (Meta calls this once)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Verification failed", 403

    # 🔹 Incoming WhatsApp messages
    if request.method == "POST":
        data = request.json
        print("FULL PAYLOAD RECEIVED:")
        print(data)

        try:
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages")

            if messages:
                message = messages[0]

                from_number = message.get("from")
                text_body = message.get("text", {}).get("body", "")

                order_time = datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")

                print("================================")
                print("NEW ORDER RECEIVED")
                print("From:", from_number)
                print("Time:", order_time)
                print("Items Ordered:")
                print(text_body)
                print("================================")

        except Exception as e:
            print("ERROR WHILE READING MESSAGE:", e)

        return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
