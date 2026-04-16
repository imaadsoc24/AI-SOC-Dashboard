from flask import Flask, render_template, jsonify
import random, time, requests

app = Flask(__name__)

# ==============================
# TELEGRAM CONFIG
# ==============================
BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass

# ==============================
# ALERT GENERATOR + AI SCORE
# ==============================
def generate_alert():
    ips = ["1.1.1.1", "8.8.8.8", "185.199.108.153", "142.250.183.206"]
    levels = ["low", "medium", "high"]

    level = random.choice(levels)
    score = random.randint(20, 100)

    alert = {
        "ip": random.choice(ips),
        "level": level,
        "time": time.strftime("%H:%M:%S"),
        "threat_score": score,
        "country": random.choice(["India", "US", "Germany", "Russia"])
    }

    # 🔴 Send Telegram if HIGH alert
    if level == "high":
        send_telegram(f"🚨 HIGH ALERT\nIP: {alert['ip']}\nScore: {score}")

    return alert

# ==============================
# ROUTES
# ==============================

# 🔥 THIS IS WHAT YOU WERE MISSING
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    data = [generate_alert() for _ in range(15)]
    return jsonify(data)

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
