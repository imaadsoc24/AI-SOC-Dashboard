from flask import Flask, jsonify, render_template_string, send_file
import json, threading, time, requests, csv

app = Flask(__name__)

LOG_FILE = "logs.json"

BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ======================
# LOAD LOGS
# ======================
def get_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

# ======================
# AI ANALYSIS
# ======================
def ai_insights(logs):
    high = sum(1 for l in logs if l["level"]=="high")
    if high > 3:
        return "🚨 Multiple high threats detected"
    return "✅ System stable"

# ======================
# BACKGROUND ALERT
# ======================
def worker():
    while True:
        logs = get_logs()
        for l in logs:
            if l["level"]=="high":
                send_telegram(f"🚨 {l['ip']} HIGH Score:{l['threat_score']}")
        time.sleep(15)

threading.Thread(target=worker, daemon=True).start()

# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/alerts")
def alerts():
    return jsonify(get_logs())

@app.route("/insights")
def insights():
    return jsonify({"msg": ai_insights(get_logs())})

@app.route("/export")
def export():
    logs = get_logs()
    with open("export.csv","w") as f:
        writer = csv.DictWriter(f, fieldnames=["ip","level","time","threat_score","lat","lon"])
        writer.writeheader()
        writer.writerows(logs)
    return send_file("export.csv", as_attachment=True)

# ======================
# HTML
# ======================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI SOC Dashboard</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    background:#0f172a;
    color:white;
    font-family:Arial;
}

.container {
    display:flex;
    gap:20px;
    padding:20px;
}

.card {
    flex:1;
    background:rgba(255,255,255,0.05);
    padding:15px;
    border-radius:15px;
}

.alert {padding:8px;margin:5px;border-radius:8px;}
.high{background:red;}
.medium{background:orange;}
.low{background:green;}

#map {height:300px;}
</style>
</head>

<body>

<h2 style="text-align:center;">🚀 AI SOC Dashboard</h2>

<center>
<input id="search" placeholder="Search IP"/>
<button onclick="exportCSV()">Export CSV</button>
</center>

<div class="container">

<div class="card">
<h3>🚨 Alerts</h3>
<div id="alerts"></div>

<h3>🧠 AI Insights</h3>
<div id="ai"></div>

<h3>📊 Chart</h3>
<canvas id="chart"></canvas>
</div>

<div class="card">
<h3>🌍 Attack Map</h3>
<div id="map"></div>
</div>

</div>

<script>
let map = L.map('map').setView([20,0],2)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

async function load(){
    let res = await fetch('/alerts')
    let data = await res.json()

    let html=""
    let high=0, med=0, low=0

    map.eachLayer((l)=>{ if(l instanceof L.Marker) map.removeLayer(l)})

    data.forEach(a=>{
        html+=`<div class="alert ${a.level}">
        ${a.ip} | ${a.level} | ${a.threat_score}
        </div>`

        if(a.level=="high") high++
        else if(a.level=="medium") med++
        else low++

        if(a.lat && a.lon){
            L.circleMarker([a.lat,a.lon]).addTo(map)
        }
    })

    document.getElementById("alerts").innerHTML=html

    // chart
    new Chart(document.getElementById("chart"), {
        type:'bar',
        data:{
            labels:['High','Medium','Low'],
            datasets:[{data:[high,med,low]}]
        }
    })

    // AI
    let ai = await fetch('/insights')
    let aiData = await ai.json()
    document.getElementById("ai").innerText = aiData.msg
}

function exportCSV(){
    window.location='/export'
}

setInterval(load,3000)
load()
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
