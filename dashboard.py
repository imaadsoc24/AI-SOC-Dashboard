from flask import Flask, render_template_string, jsonify
import json
import time
import threading
import requests

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
LOG_FILE = "/var/ossec/logs/alerts/alerts.json"

# Telegram
BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

# ==============================
# TELEGRAM ALERT
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ==============================
# READ WAZUH LOGS
# ==============================
def get_logs():
    alerts = []

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-20:]

        for line in lines:
            data = json.loads(line)

            level_num = data.get("rule", {}).get("level", 0)

            alert = {
                "ip": data.get("data", {}).get("srcip", "unknown"),
                "level": "high" if level_num > 10 else "medium",
                "time": data.get("timestamp", ""),
                "threat_score": level_num * 10,
                "country": "Unknown"
            }

            # Telegram for high alerts
            if level_num > 12:
                send_telegram(f"🚨 HIGH ALERT {alert['ip']} Score:{alert['threat_score']}")

            alerts.append(alert)

    except Exception as e:
        print("Error:", e)

    return alerts

# ==============================
# BACKGROUND LOOP
# ==============================
def background_worker():
    while True:
        get_logs()
        time.sleep(10)

threading.Thread(target=background_worker, daemon=True).start()

# ==============================
# ROUTES
# ==============================
@app.route("/")
def home():
    return "AI SOC Dashboard Running 🚀"

@app.route("/dashboard")
def dashboard():
    return render_template_string(HTML)

@app.route("/alerts")
def alerts():
    return jsonify(get_logs())

# ==============================
# HTML DASHBOARD (GLASS UI + MAP + SEARCH)
# ==============================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI SOC Dashboard</title>

<style>
body {
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: white;
    font-family: Arial;
}

.container {
    display: flex;
    gap: 20px;
}

.card {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
}

.alert {
    padding: 10px;
    margin: 5px;
    border-radius: 10px;
}

.high { background: red; }
.medium { background: orange; }
.low { background: green; }
</style>
</head>

<body>

<h2>🚀 AI SOC Dashboard</h2>

<input id="search" placeholder="Search IP..." onkeyup="filterAlerts()"/>

<div class="container">

<div class="card">
<h3>📊 Alerts</h3>
<div id="alerts"></div>
</div>

<div class="card">
<h3>🌍 Attack Map</h3>
<div id="map">Map coming from data...</div>
</div>

</div>

<script>
async function loadAlerts(){
    let res = await fetch('/alerts')
    let data = await res.json()

    let html = ""
    data.forEach(a=>{
        html += `<div class="alert ${a.level}">
        ${a.time} | ${a.ip} | ${a.level} | ${a.threat_score}
        </div>`
    })

    document.getElementById("alerts").innerHTML = html
}

function filterAlerts(){
    let input = document.getElementById("search").value.toLowerCase()
    let alerts = document.getElementsByClassName("alert")

    for(let a of alerts){
        if(a.innerText.toLowerCase().includes(input)){
            a.style.display = "block"
        } else {
            a.style.display = "none"
        }
    }
}

setInterval(loadAlerts, 3000)
</script>

</body>
</html>
"""

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
