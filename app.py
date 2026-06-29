from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    jsonify
)
from datetime import datetime
import requests
import csv
import os

from crypto_utils import encrypt_log
from face_service import start_face_service

app = Flask(__name__)

from config import (
    ESP32_BASE_URL,
    ESP32_UNLOCK_URL,
    ESP32_STREAM_URL,
    LOG_FILE,
    ENCRYPTED_LOG_FILE,
    AES_KEY
)

logs = []
door_status = "LOCKED"


def load_logs():
    global logs

    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        loaded_logs = []

        for row in reader:
            loaded_logs.append({
                "time": row.get("time") or row.get("waktu") or "-",
                "action": row.get("action") or row.get("nama") or "-",
                "status": row.get("status") or "-"
            })

        logs = loaded_logs
        logs.reverse()


def save_encrypted_log(log):
    encrypted = encrypt_log(log)
    file_exists = os.path.exists(ENCRYPTED_LOG_FILE)

    with open(ENCRYPTED_LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        fieldnames = ["time", "iv", "ciphertext"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "time": log["time"],
            "iv": encrypted["iv"],
            "ciphertext": encrypted["ciphertext"]
        })


def save_log(action, status):
    log = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "status": status
    }

    logs.insert(0, log)

    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        fieldnames = ["time", "action", "status"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(log)

    save_encrypted_log(log)


def check_esp32_status():
    try:
        response = requests.get(ESP32_BASE_URL, timeout=2)
        return "Online" if response.status_code == 200 else "Offline"
    except Exception:
        return "Offline"

@app.route("/")
def home():
    return render_template(
        "dashboard.html",
        door_status=door_status,
        stream_url=ESP32_STREAM_URL
    )


@app.route("/api/logs")
def api_logs():
    esp32_status = check_esp32_status()

    total_access = len(logs)
    total_granted = sum(1 for log in logs if log["status"] in ["Success", "Granted"])
    total_denied = sum(1 for log in logs if log["status"] in ["Denied", "Failed"])

    last_log = logs[0] if logs else None
    last_access_time = last_log["time"] if last_log else "-"
    last_action = last_log["action"] if last_log else "-"

    last_face = "-"
    for log in logs:
        if log["action"].startswith("Face Recognition"):
            last_face = log["action"].replace("Face Recognition - ", "")
            break

    return jsonify({
        "door_status": door_status,
        "esp32_status": esp32_status,
        "total_access": total_access,
        "total_granted": total_granted,
        "total_denied": total_denied,
        "last_access_time": last_access_time,
        "last_action": last_action,
        "last_face": last_face,
        "logs": logs[:20]
    })


@app.route("/unlock", methods=["POST"])
def unlock():
    global door_status

    try:
        response = requests.get(ESP32_UNLOCK_URL, timeout=5)

        if response.status_code == 200:
            door_status = "UNLOCKED"
            status = "Success"
        else:
            status = "Failed"

    except Exception:
        status = "ESP32 Offline"

    save_log("Manual Unlock", status)

    return redirect(url_for("home"))


@app.route("/face-log", methods=["POST"])
def face_log():
    global door_status

    data = request.get_json()

    name = data.get("name", "Unknown")
    status = data.get("status", "Denied")

    if status == "Granted":
        door_status = "UNLOCKED"

    save_log(f"Face Recognition - {name}", status)

    return jsonify({
        "message": "Face log saved",
        "name": name,
        "status": status
    })


if __name__ == "__main__":
    load_logs()
    start_face_service(save_log)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)