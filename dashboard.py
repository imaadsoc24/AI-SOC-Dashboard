from flask import Flask, render_template, jsonify
import requests, random, time

app = Flask(__name__)

# ===== CONFIG =====
WAZUH_API = "https://localhost:55000"
USERNAME = "wazuh"
PASSWORD = "Kle*s6F30b.GiLoyqu62.rlzD5lUuk?1"

# 🔔 TELEGRAM CONFIG
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

# ===== GET REAL ALERTS =====
def get_wazuh_alerts():
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"{WAZUH_API}/alerts?limit=15",
            headers=headers,
            verify=False
        )

        return res.json()["data"]["affected_items"]

    except:
        # fallback (for Render)
        return [{
            "agent": {"name": "demo"},
            "rule": {"level": random.randint(3,15), "description": "Demo alert"},
            "timestamp": time.strftime("%H:%M:%S"),
            "data": {"srcip": random.choice(["8.8.8.8","1.1.1.1"])}
        } for _ in range(10)]

# ===== MITRE =====
def map_mitre(rule_id):
    if rule_id < 5:
        return "T1046 - Network Scan"
    elif rule_id < 10:
        return "T1110 - Brute Force"
    elif rule_id < 15:
        return "T1059 - Command Execution"
    else:
        return "T1078 - Valid Accounts"

# ===== ROUTE =====
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    logs = get_wazuh_alerts()
    alerts = []

    for log in logs:
        ip = log.get("data", {}).get("srcip", "local")
        level = log.get("rule", {}).get("level", 0)
        desc = log.get("rule", {}).get("description", "unknown")
        agent = log.get("agent", {}).get("name", "unknown")

        mitre = map_mitre(level)

        alert = {
            "ip": ip,
            "level": "high" if level > 10 else "medium",
            "time": log.get("timestamp", ""),
            "desc": desc,
            "agent": agent,
            "mitre": mitre,
            "lat": random.uniform(-50,50),
            "lon": random.uniform(-100,100)
        }

        # 🚨 TELEGRAM ALERT (ONLY HIGH)
        if level > 12:
            send_telegram(
                f"🚨 HIGH ALERT\n"
                f"IP: {ip}\n"
                f"Agent: {agent}\n"
                f"Attack: {desc}\n"
                f"MITRE: {mitre}\n"
                f"Time: {alert['time']}"
            )

        alerts.append(alert)

    return jsonify(alerts)

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
