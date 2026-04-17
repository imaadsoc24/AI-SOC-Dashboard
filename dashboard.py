from flask import Flask, render_template, jsonify
import requests, random, time, csv
from io import StringIO
import geoip2.database

app = Flask(__name__)

# ================= CONFIG =================
WAZUH_API = "https://localhost:55000"
USERNAME = "wazuh"
PASSWORD = "Kle*s6F30b.GiLoyqu62.rlzD5lUuk?1"

BOT_TOKEN = "8749610900:AAGd7oHByeYFHzqkP1iZ4UMQStSihA4tQoE"
CHAT_ID = "1452519845"

VT_API = "ec18f73ed6585bd3a9a3ba396486a534f9930bbdf1f50a47c71a4c5ecb0e1f62"

# GeoIP DB file
GEO_DB = "GeoLite2-City.mmdb"

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= MITRE =================
def map_mitre(log):
    desc = str(log).lower()

    if "ssh" in desc:
        return "T1110 - Brute Force"
    elif "user" in desc:
        return "T1078 - Valid Accounts"
    elif "process" in desc:
        return "T1059 - Command Execution"
    elif "file" in desc:
        return "T1005 - Data Access"
    else:
        return "T1046 - Network Scan"

# ================= GEOIP =================
def get_geo(ip):
    try:
        reader = geoip2.database.Reader(GEO_DB)
        res = reader.city(ip)
        return res.location.latitude, res.location.longitude
    except:
        return random.uniform(-50,50), random.uniform(-100,100)

# ================= VIRUSTOTAL =================
def check_vt(ip):
    try:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        headers = {"x-apikey": VT_API}
        r = requests.get(url, headers=headers)
        data = r.json()

        malicious = data["data"]["attributes"]["last_analysis_stats"]["malicious"]
        return malicious
    except:
        return 0

# ================= TOKEN =================
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
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(
            f"{WAZUH_API}/manager/logs?limit=15",
            headers=headers,
            verify=False,
            timeout=3
        )

        return res.json()["data"]["affected_items"]

    except:
        # fallback (for Render)
        demo = []
        ips = ["8.8.8.8","1.1.1.1","185.199.108.153"]
        for _ in range(10):
            demo.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "tag": random.choice(ips),
                "level": random.choice(["info","error"])
            })
        return demo

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts():
    logs = get_logs()
    alerts = []

    for log in logs:
        ip = log.get("tag","unknown")

        score = random.randint(30,100)
        vt_score = check_vt(ip)

        if vt_score > 0:
            score += 20

        lat, lon = get_geo(ip)

        mitre = map_mitre(log)

        alert = {
            "ip": ip,
            "level": "high" if score > 70 else "medium",
            "time": log.get("timestamp",""),
            "threat_score": score,
            "mitre": mitre,
            "lat": lat,
            "lon": lon
        }

        if score > 85:
            send_telegram(f"🚨 HIGH ALERT {ip} | {mitre} | Score:{score}")

        alerts.append(alert)

    return jsonify(alerts)

# ================= CSV =================
@app.route("/export")
def export():
    logs = get_logs()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Time","IP","Level"])

    for log in logs:
        writer.writerow([
            log.get("timestamp",""),
            log.get("tag",""),
            log.get("level","")
        ])

    return si.getvalue()

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
