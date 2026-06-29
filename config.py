# ==========================
# SMART LOCK CONFIG
# ==========================

ESP32_BASE_URL = "http://192.168.153.107"
ESP32_UNLOCK_URL = f"{ESP32_BASE_URL}/unlock"
ESP32_STREAM_URL = f"{ESP32_BASE_URL}:81/stream"
ESP32_CAPTURE_URL = f"{ESP32_BASE_URL}/capture"

LOG_FILE = "access_log.csv"
ENCRYPTED_LOG_FILE = "encrypted_access_log.csv"

DATASET_DIR = "dataset"

AES_KEY = b"1234567890abcdef"  # 16 byte = AES-128

FACE_COOLDOWN = 8
UNKNOWN_COOLDOWN = 8