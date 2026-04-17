from flask import Flask, render_template, jsonify
import requests, random, time

app = Flask(__name__)

# ===== CONFIG =====
WAZUH_API = "https://dice-headlock-uncheck.ngrok-free.dev"
USERNAME = "wazuh"
PASSWORD = "Kle*s6F30b.GiLoyqu62.rlzD5lUuk?1"

# ===== TELEGRAM CONFIG =====
BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

# ===== TELEGRAM FUNCTION =====
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== TOKEN =====
def get_token():
    try:
        res = requests.post(
            f"{WAZUH_API}/security/user/authenticate?raw=true",
            auth=(USERNAME, PASSWORD),
            verify=False
        )
        return res.text
    except:
        return None

# ===== GET ALERTS =====
def get_wazuh_alerts():
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"{WAZUH_API}/alerts?limit=20",
            headers=headers,
            verify=False
        )

        return res.json()["data"]["affected_items"]

    except:
        # fallback (render safe)
        return [{
            "timestamp": time.strftime("%H:%M:%S"),
            "tag": "demo",
            "level": "info",
            "description": "Demo alert"
        } for _ in range(10)]

# ===== MITRE MAPPING =====
def map_mitre(desc):
    desc = str(desc).lower()

    if "ssh" in desc:
        return "T1110 - Brute Force"
    elif "user" in desc:
        return "T1078 - Valid Accounts"
    elif "process" in desc:
        return "T1059 - Command Execution"
    elif "file" in desc:
        return "T1005 - Data from Local System"
    else:
        return "T1046 - Network Scan"

# ===== ROUTES =====
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    logs = get_wazuh_alerts()
    alerts = []

    for log in logs:
        desc = log.get("description", "")
        level_raw = log.get("level", "info")

        level = "high" if "error" in level_raw else "medium"
        score = 80 if level == "high" else 50

        alert = {
            "ip": log.get("tag", "local"),
            "level": level,
            "time": log.get("timestamp", ""),
            "desc": desc,
            "mitre": map_mitre(desc),
            "score": score,
            "lat": random.uniform(-50, 50),
            "lon": random.uniform(-100, 100)
        }

        alerts.append(alert)

        # 🚨 TELEGRAM ALERT
        if level == "high":
            send_telegram(f"🚨 ALERT\n{alert}")

    return jsonify(alerts)

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
