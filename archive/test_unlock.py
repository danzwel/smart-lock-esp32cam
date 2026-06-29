import requests

ESP32_URL = "http://192.168.17.107/unlock"

try:
    response = requests.get(ESP32_URL, timeout=5)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Gagal kirim unlock:", e)