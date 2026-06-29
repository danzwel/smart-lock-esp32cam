import face_recognition
import cv2
import os
import requests
import time
import csv
from datetime import datetime

ESP32_URL = "http://192.168.17.107/unlock"
last_unlock_time = 0
UNLOCK_COOLDOWN = 10

LOG_FILE = "access_log.csv"

DATASET_DIR = "dataset/daniel"

known_encodings = []
known_names = []

def write_log(name, status):
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["waktu", "nama", "status"])

        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([waktu, name, status])

print("Loading dataset...")

for filename in os.listdir(DATASET_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(DATASET_DIR, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append("Daniel")
            print(f"Loaded: {filename}")
        else:
            print(f"Tidak ada wajah: {filename}")

print("Dataset loaded.")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(
            known_encodings,
            face_encoding,
            tolerance=0.5
        )

        name = "Unknown"

        if True in matches:
            index = matches.index(True)
            name = known_names[index]

            if name == "Daniel":
                current_time = time.time()

                if current_time - last_unlock_time > UNLOCK_COOLDOWN:
                    try:
                        response = requests.get(ESP32_URL, timeout=3)
                        print("Unlock sent:", response.text)
                        write_log(name, "Unlocked")
                        last_unlock_time = current_time
                    except Exception as e:
                        print("Gagal kirim unlock:", e)
                        write_log(name, "Unlock Failed")

        top, right, bottom, left = face_location

        if name == "Daniel":
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        if name == "Unknown":
            current_time = time.time()

            if current_time - last_unlock_time > UNLOCK_COOLDOWN:
                print("Unknown face detected")
                write_log(name, "Denied")
                last_unlock_time = current_time

    cv2.imshow("Face Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()