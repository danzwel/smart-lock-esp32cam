import os
import face_recognition

from config import DATASET_DIR


ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def load_known_faces():
    known_encodings = []
    known_names = []

    print("Loading dataset...")

    if not os.path.exists(DATASET_DIR):
        print(f"Folder dataset tidak ditemukan: {DATASET_DIR}")
        print("Dataset loaded.")
        return known_encodings, known_names

    # Format utama yang dipakai:
    # dataset/
    # ├── daniel/
    # │   ├── 1.jpg
    # │   └── 2.jpg
    # └── dzikri/
    #     ├── 1.jpg
    #     └── 2.jpg
    for person_name in sorted(os.listdir(DATASET_DIR)):
        person_folder = os.path.join(DATASET_DIR, person_name)

        if not os.path.isdir(person_folder):
            continue

        loaded_count = 0

        for filename in sorted(os.listdir(person_folder)):
            if not filename.lower().endswith(ALLOWED_IMAGE_EXTENSIONS):
                continue

            path = os.path.join(person_folder, filename)

            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
            except Exception as e:
                print(f"Gagal membaca {person_name}/{filename}: {e}")
                continue

            if len(encodings) > 0:
                known_encodings.append(encodings[0])
                known_names.append(person_name)
                loaded_count += 1
                print(f"Loaded: {person_name}/{filename}")
            else:
                print(f"Tidak ada wajah: {person_name}/{filename}")

        if loaded_count == 0:
            print(f"Peringatan: folder '{person_name}' tidak punya foto wajah yang valid")

    print(f"Dataset loaded. Total wajah: {len(known_encodings)}")
    return known_encodings, known_names


def recognize_face(rgb_frame, known_encodings, known_names, tolerance=0.5):
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    results = []

    if len(known_encodings) == 0:
        for face_location in face_locations:
            results.append({
                "name": "Unknown",
                "status": "Denied",
                "location": face_location
            })
        return results

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(
            known_encodings,
            face_encoding,
            tolerance=tolerance
        )

        face_distances = face_recognition.face_distance(
            known_encodings,
            face_encoding
        )

        name = "Unknown"
        status = "Denied"

        if len(face_distances) > 0:
            best_match_index = face_distances.argmin()

            if matches[best_match_index]:
                name = known_names[best_match_index]
                status = "Granted"

        results.append({
            "name": name,
            "status": status,
            "location": face_location
        })

    return results
