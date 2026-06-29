import threading
import time
import requests
import cv2
import numpy as np
import os

from config import (
    ESP32_CAPTURE_URL,
    ESP32_UNLOCK_URL,
    FACE_COOLDOWN,
    UNKNOWN_COOLDOWN
)

LAST_FACE_IMAGE = "static/last_face.jpg"

from face_utils import load_known_faces, recognize_face


def start_face_service(save_log_callback):
    thread = threading.Thread(
        target=face_recognition_loop,
        args=(save_log_callback,),
        daemon=True
    )
    thread.start()
    print("Face recognition service started.")


def face_recognition_loop(save_log_callback):
    known_encodings, known_names = load_known_faces()

    last_unlock_time = 0
    last_unknown_log_time = 0

    while True:
        try:
            response = requests.get(ESP32_CAPTURE_URL, timeout=5)
            img_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is None:
                print("Gagal decode gambar dari ESP32-CAM")
                time.sleep(1)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = recognize_face(
                rgb_frame,
                known_encodings,
                known_names
            )

            if results:
                os.makedirs("static", exist_ok=True)
                cv2.imwrite(LAST_FACE_IMAGE, frame)

            for result in results:
                name = result["name"]
                status = result["status"]

                current_time = time.time()

                if status == "Granted":
                    if current_time - last_unlock_time > FACE_COOLDOWN:
                        print(f"{name} dikenali, membuka pintu...")

                        try:
                            unlock_response = requests.get(
                                ESP32_UNLOCK_URL,
                                timeout=5
                            )
                            print("ESP32 response:", unlock_response.text)

                            save_log_callback(
                                f"Face Recognition - {name}",
                                "Granted"
                            )

                            last_unlock_time = current_time

                        except Exception as e:
                            print("Gagal menghubungi ESP32:", e)
                            save_log_callback(
                                f"Face Recognition - {name}",
                                "ESP32 Offline"
                            )

                else:
                    if current_time - last_unknown_log_time > UNKNOWN_COOLDOWN:
                        print("Unknown face detected")

                        save_log_callback(
                            "Face Recognition - Unknown",
                            "Denied"
                        )

                        last_unknown_log_time = current_time

            time.sleep(0.5)

        except Exception as e:
            print("Face service error:", e)
            time.sleep(2)