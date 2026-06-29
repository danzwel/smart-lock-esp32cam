import face_recognition
import cv2
import os
import requests
import time
import numpy as np

DATASET_DIR = "dataset/daniel"
ESP32_CAPTURE_URL = "http://192.168.17.107/capture"
ESP32_UNLOCK_URL = "http://192.168.17.107/unlock"
DASHBOARD_LOG_URL = "http://127.0.0.1:5000/face-log"

known_encodings = []
known_names = []

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

last_unlock_time = 0
last_unknown_log_time = 0
cooldown = 8

while True:
    try:
        response = requests.get(ESP32_CAPTURE_URL, timeout=5)
        img_array = np.frombuffer(response.content, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is None:
            print("Gagal decode gambar dari ESP32-CAM")
            continue

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
            access = "Denied"

            if True in matches:
                index = matches.index(True)
                name = known_names[index]
                access = "Granted"

                current_time = time.time()

                if current_time - last_unlock_time > cooldown:
                    print("Daniel dikenali, membuka pintu...")

                    unlock_response = requests.get(ESP32_UNLOCK_URL, timeout=5)
                    print("ESP32 response:", unlock_response.text)

                    requests.post(DASHBOARD_LOG_URL, json={
                        "name": name,
                        "status": "Granted"
                    })

                    last_unlock_time = current_time
            else:
                current_time = time.time()

                if current_time - last_unknown_log_time > cooldown:
                    requests.post(DASHBOARD_LOG_URL, json={
                        "name": "Unknown",
                        "status": "Denied"
                    })
                    last_unknown_log_time = current_time

            top, right, bottom, left = face_location
            color = (0, 255, 0) if access == "Granted" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(
                frame,
                f"{name} - {access}",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )

        cv2.imshow("ESP32-CAM Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)

cv2.destroyAllWindows()