from flask import Flask, render_template_string, request, redirect, session, send_file
import json, requests, csv, io

app = Flask(__name__)
app.secret_key = "soc_secret_key"

LOG_FILE = "/var/ossec/logs/alerts/alerts.json"

USERNAME = "admin"
PASSWORD = "admin123"

blocked_ips = set()

# 🌍 GEO
def get_geo(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return res.get("country", "Unknown")
    except:
        return "Unknown"

# 🔐 LOGIN PAGE
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    color:white;
    font-family:Arial;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}

.card {
    background:#111827;
    padding:30px;
    border-radius:15px;
    width:300px;
    text-align:center;
}

input {
    width:90%;
    padding:10px;
    margin:10px;
    border:none;
    border-radius:5px;
}

button {
    padding:10px;
    width:100%;
    background:#3b82f6;
    color:white;
    border:none;
    border-radius:5px;
    cursor:pointer;
}
</style>
</head>
<body>

<div class="card">
<h2>🔐 AI SOC Login</h2>

<form method="POST">
<input name="u" placeholder="Username" required>
<input name="p" type="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>

</div>

</body>
</html>
"""

# 🚀 DASHBOARD
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="3">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {background:#0f172a;color:white;font-family:Arial;padding:20px;}
.light {background:white;color:black;}

.header {text-align:center;margin-bottom:20px;}

.stats {display:flex;gap:10px;}
.box {flex:1;background:#1e293b;padding:10px;border-radius:10px;text-align:center;}

.card {padding:10px;margin:10px 0;border-radius:10px;}
.low{background:#16a34a;}
.medium{background:#facc15;color:black;}
.high{background:#dc2626;}

.alert{background:red;padding:10px;border-radius:10px;}
.ai{background:#2563eb;padding:10px;border-radius:10px;}

button{margin:5px;padding:8px;border:none;border-radius:5px;cursor:pointer;}
</style>

<script>
function toggleMode(){
document.body.classList.toggle("light");
}
</script>

</head>

<body>

<div class="header">
<h1>🚀 AI SOC Dashboard</h1>

<button onclick="toggleMode()">🌗 Theme</button>
<a href="/export"><button>📁 Export CSV</button></a>
<a href="/logout"><button>🚪 Logout</button></a>
</div>

{% if brute %}
<div class="alert">
🚨 BRUTE FORCE DETECTED ({{failed}} attempts)
</div>
{% endif %}

<div class="ai">
🧠 {{ai}}
</div>

<div class="stats">
<div class="box">Total<br>{{total}}</div>
<div class="box">High<br>{{high}}</div>
<div class="box">Medium<br>{{med}}</div>
<div class="box">Low<br>{{low}}</div>
</div>

<canvas id="chart"></canvas>

<script>
new Chart(document.getElementById("chart"), {
type:'bar',
data:{
labels:['Low','Medium','High'],
datasets:[{data:[{{low}},{{med}},{{high}}]}]
}
});
</script>

{% for a in alerts %}
<div class="card {{a.color}}">
Time: {{a.time}}<br>
IP: {{a.ip}} ({{a.geo}})<br>
Rule: {{a.rule}}<br>
{% if a.ip in blocked %}❌ BLOCKED{% endif %}
</div>
{% endfor %}

</body>
</html>
"""

# 🔐 LOGIN ROUTE
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("u") == USERNAME and request.form.get("p") == PASSWORD:
            session["user"] = True
            return redirect("/dashboard")
        else:
            return LOGIN_HTML + "<p style='color:red;text-align:center;'>Invalid Credentials</p>"

    return LOGIN_HTML


# 🚀 DASHBOARD ROUTE
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    alerts=[]
    failed=0
    brute=False
    ai="System normal"

    try:
        with open(LOG_FILE) as f:
            lines=f.readlines()[-50:]

            for line in lines:
                log=json.loads(line)

                rule=log.get("rule",{})
                desc=rule.get("description","").lower()
                level=rule.get("level",0)
                ip=log.get("data",{}).get("srcip","N/A")

                geo=get_geo(ip) if ip!="N/A" else "Local"

                if "failed" in desc or "invalid" in desc or "unknown" in desc:
                    failed+=1

                if failed>=5:
                    brute=True
                    ai="Multiple failed login attempts detected (Brute Force)"
                    if ip!="N/A":
                        blocked_ips.add(ip)

                if level<=3: color="low"
                elif level<=7: color="medium"
                else: color="high"

                alerts.append({
                    "time":log.get("timestamp"),
                    "ip":ip,
                    "geo":geo,
                    "rule":rule.get("description"),
                    "color":color
                })

    except Exception as e:
        print(e)

    low=len([a for a in alerts if a["color"]=="low"])
    med=len([a for a in alerts if a["color"]=="medium"])
    high=len([a for a in alerts if a["color"]=="high"])
    total=len(alerts)

    return render_template_string(
        DASHBOARD_HTML,
        alerts=alerts,
        low=low,
        med=med,
        high=high,
        total=total,
        brute=brute,
        failed=failed,
        ai=ai,
        blocked=blocked_ips
    )


# 📁 EXPORT
@app.route("/export")
def export():
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["Time","IP","Rule"])

    with open(LOG_FILE) as f:
        for line in f.readlines()[-50:]:
            log=json.loads(line)
            writer.writerow([
                log.get("timestamp"),
                log.get("data",{}).get("srcip"),
                log.get("rule",{}).get("description")
            ])

    output.seek(0)
    return send_file(io.BytesIO(output.read().encode()),
                     download_name="alerts.csv",
                     as_attachment=True)


# 🚪 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
