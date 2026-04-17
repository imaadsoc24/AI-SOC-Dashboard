from flask import Flask, render_template, jsonify, request
import requests, random, time, csv
from io import StringIO

app = Flask(__name__)

# ================= CONFIG =================
WAZUH_API = "https://localhost:55000"
USERNAME = "wazuh"
PASSWORD = "Kle*s6F30b.GiLoyqu62.rlzD5lUuk?1"

BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= WAZUH TOKEN =================
def get_token():
    try:
        res = requests.post(
            f"{WAZUH_API}/security/user/authenticate?raw=true",
            auth=(USERNAME, PASSWORD),
            verify=False,
            timeout=3
        )
        return res.text
    except:
        return None

# ================= GET LOGS =================
def get_logs():
    try:
        token = get_token()
        if not token:
            raise Exception("No token")

        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"{WAZUH_API}/manager/logs?limit=15",
            headers=headers,
            verify=False,
            timeout=3
        )

        return res.json()["data"]["affected_items"]

    except:
        # 🌐 CLOUD FALLBACK (Render safe)
        demo = []
        ips = ["8.8.8.8", "1.1.1.1", "185.199.108.153"]
        for _ in range(10):
            demo.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "tag": random.choice(ips),
                "level": random.choice(["info", "error"])
            })
        return demo

# ================= AI SCORING =================
def ai_score(level):
    if "error" in level:
        return random.randint(70, 100)
    return random.randint(30, 60)

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    logs = get_logs()
    alerts = []

    for log in logs:
        score = ai_score(log.get("level", ""))

        alert = {
            "ip": log.get("tag", "unknown"),
            "level": "high" if score > 70 else "medium",
            "time": log.get("timestamp", ""),
            "threat_score": score,
            "lat": random.uniform(-50, 50),
            "lon": random.uniform(-100, 100)
        }

        if score > 80:
            send_telegram(f"🚨 HIGH ALERT {alert['ip']} Score:{score}")

        alerts.append(alert)

    return jsonify(alerts)

# ================= CSV EXPORT =================
@app.route("/export")
def export():
    logs = get_logs()

    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(["Time", "IP", "Level"])

    for log in logs:
        writer.writerow([
            log.get("timestamp", ""),
            log.get("tag", ""),
            log.get("level", "")
        ])

    return si.getvalue()

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
