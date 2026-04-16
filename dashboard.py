from flask import Flask, jsonify, render_template, send_file
import json, requests, csv, threading, time, os

app = Flask(__name__)

LOG_FILE = "logs.json"

BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= LOAD LOGS =================
def load_logs():
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except:
        return []

# ================= AI ENGINE =================
def ai_analysis(logs):
    high = sum(1 for l in logs if l["level"]=="high")
    if high > 5:
        return "🚨 Critical attack spike detected"
    elif high > 2:
        return "⚠️ Suspicious activity increasing"
    return "✅ System stable"

# ================= BACKGROUND ALERT =================
def worker():
    while True:
        logs = load_logs()
        for l in logs:
            if l["level"] == "high":
                send_telegram(f"🚨 HIGH ALERT: {l['ip']} Score:{l['threat_score']}")
        time.sleep(20)

threading.Thread(target=worker, daemon=True).start()

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    return jsonify(load_logs())

@app.route("/ai")
def ai():
    return jsonify({"msg": ai_analysis(load_logs())})

@app.route("/export")
def export():
    logs = load_logs()
    with open("export.csv","w") as f:
        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
        writer.writeheader()
        writer.writerows(logs)
    return send_file("export.csv", as_attachment=True)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
