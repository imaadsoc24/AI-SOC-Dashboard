from flask import Flask, jsonify, render_template_string
import json
import threading
import time
import requests

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
LOG_FILE = "logs.json"

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
# READ LOGS (SAFE)
# ==============================
def get_logs():
    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
            return data
    except:
        # fallback if file missing
        return [
            {"ip":"8.8.8.8","level":"high","time":"live","threat_score":90},
            {"ip":"1.1.1.1","level":"medium","time":"live","threat_score":60}
        ]

# ==============================
# BACKGROUND ALERT LOOP
# ==============================
def background_worker():
    while True:
        logs = get_logs()

        for alert in logs:
            if alert["level"] == "high":
                send_telegram(f"🚨 HIGH ALERT {alert['ip']} Score:{alert['threat_score']}")

        time.sleep(15)

threading.Thread(target=background_worker, daemon=True).start()

# ==============================
# ROUTES
# ==============================
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/alerts")
def alerts():
    return jsonify(get_logs())

# ==============================
# FRONTEND (GLASS UI + SEARCH)
# ==============================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI SOC Dashboard</title>

<style>
body {
    margin:0;
    font-family: Arial;
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: white;
}

.container {
    display: flex;
    gap: 20px;
    padding: 20px;
}

.card {
    flex:1;
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
}

h2 {
    text-align: center;
}

.alert {
    padding: 10px;
    margin: 5px 0;
    border-radius: 10px;
}

.high { background: #ff3b3b; }
.medium { background: orange; }
.low { background: green; }

input {
    margin: 10px;
    padding: 8px;
    width: 200px;
    border-radius: 5px;
    border:none;
}
</style>
</head>

<body>

<h2>🚀 AI SOC Dashboard</h2>

<center>
<input id="search" placeholder="Search IP..." onkeyup="filterAlerts()">
</center>

<div class="container">

<div class="card">
<h3>🚨 Alerts</h3>
<div id="alerts"></div>
</div>

<div class="card">
<h3>🌍 Attack Map</h3>
<p>Map will be added next step 🔥</p>
</div>

</div>

<script>
async function loadAlerts(){
    let res = await fetch('/alerts');
    let data = await res.json();

    let html = "";
    data.forEach(a=>{
        html += `<div class="alert ${a.level}">
        ${a.time} | ${a.ip} | ${a.level.toUpperCase()} | Score: ${a.threat_score}
        </div>`;
    });

    document.getElementById("alerts").innerHTML = html;
}

function filterAlerts(){
    let input = document.getElementById("search").value.toLowerCase();
    let alerts = document.getElementsByClassName("alert");

    for(let a of alerts){
        if(a.innerText.toLowerCase().includes(input)){
            a.style.display = "block";
        } else {
            a.style.display = "none";
        }
    }
}

setInterval(loadAlerts, 3000);
loadAlerts();
</script>

</body>
</html>
"""

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
