from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

# ==============================
# FAKE ALERT GENERATOR (FINAL)
# ==============================

def generate_alert():
    ips = ["1.1.1.1", "8.8.8.8", "185.199.108.153", "142.250.183.206"]
    levels = ["low", "medium", "high"]

    level = random.choice(levels)

    return {
        "ip": random.choice(ips),
        "level": level,
        "message": "Suspicious activity detected",
        "time": time.strftime("%H:%M:%S"),
        "threat_score": random.randint(1, 100)
    }

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return "AI SOC Dashboard Running 🚀"

@app.route("/alerts")
def alerts():
    data = [generate_alert() for _ in range(20)]
    return jsonify(data)

# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
