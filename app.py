from flask import Flask, render_template, request, jsonify
import os
import base64
import cv2
import numpy as np
import face_recognition
import json
from user_agents import parse  # 📌 for device-based page routing

app = Flask(__name__)
app.secret_key = "supersecretkey"

REGISTERED_FACES_DIR = "registered_faces"
INFO_FILE = "people_info.json"

os.makedirs(REGISTERED_FACES_DIR, exist_ok=True)

# ---------------- Home Page (Device-Specific) ----------------
@app.route("/")
def home():
    user_agent = request.headers.get("User-Agent")
    ua = parse(user_agent)

    if ua.is_mobile:
        return render_template("index_mobile.html")
    elif ua.is_tablet:
        return render_template("index_tablet.html")
    else:
        return render_template("index_laptop.html")

# ---------------- Register Page ----------------
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_submit", methods=["POST"])
def register_submit():
    data = request.json

    name = data.get("name", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    age = data.get("age", "").strip()
    occupation = data.get("occupation", "").strip()
    country = data.get("country", "").strip()
    images = data.get("images", [])

    if not name or not images:
        return jsonify({"success": False, "message": "Name and images are required."})

    encodings = []
    for i, img_b64 in enumerate(images):
        img_data = img_b64.split(",")[1]
        img_bytes = base64.b64decode(img_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        img_path = os.path.join(REGISTERED_FACES_DIR, f"{name}_{i}.png")
        cv2.imwrite(img_path, img)

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_enc = face_recognition.face_encodings(rgb_img)
        if face_enc:
            encodings.append(face_enc[0])

    if len(encodings) == 0:
        return jsonify({"success": False, "message": "No face found in images."})

    id_img_path = os.path.join(REGISTERED_FACES_DIR, f"{name}_id.png")
    cv2.imwrite(id_img_path, cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR))

    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r") as f:
            people_info = json.load(f)
    else:
        people_info = {}

    people_info[name] = {
        "Name": name,
        "Full Name": full_name,
        "Age": age,
        "Occupation": occupation,
        "Country": country
    }

    with open(INFO_FILE, "w") as f:
        json.dump(people_info, f, indent=4)

    return jsonify({"success": True, "message": f"Registered {full_name} with {len(encodings)} captures."})

# ---------------- Recognize Page ----------------
@app.route("/recognize")
def recognize():
    return render_template("recognize.html")

@app.route("/recognize_submit", methods=["POST"])
def recognize_submit():
    data = request.json
    img_b64 = data.get("image", "")

    if not img_b64:
        return jsonify({"success": False, "message": "No image received."})

    img_data = img_b64.split(",")[1]
    img_bytes = base64.b64decode(img_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if not os.path.exists(INFO_FILE):
        return jsonify({"success": False, "message": "No registered faces database."})

    with open(INFO_FILE, "r") as f:
        people_info = json.load(f)

    known_face_encodings = []
    known_face_names = []

    for name, info in people_info.items():
        id_img_path = os.path.join(REGISTERED_FACES_DIR, f"{name}_id.png")
        if os.path.exists(id_img_path):
            known_image = face_recognition.load_image_file(id_img_path)
            encodings = face_recognition.face_encodings(known_image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(name)

    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    if not face_encodings:
        return jsonify({"success": False, "message": "No face detected in the image."})

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        if True in matches:
            match_index = matches.index(True)
            matched_name = known_face_names[match_index]
            matched_info = people_info.get(matched_name, {})

            id_img_path = os.path.join(REGISTERED_FACES_DIR, f"{matched_name}_id.png")
            with open(id_img_path, "rb") as img_file:
                id_img_b64 = "data:image/png;base64," + base64.b64encode(img_file.read()).decode()

            return jsonify({
                "success": True,
                "message": "Face recognized.",
                "info": matched_info,
                "id_image": id_img_b64
            })

    return jsonify({"success": False, "message": "No matching face found."})

# ---------------- Student List Page ----------------
@app.route("/student_list")
def student_list():
    if not os.path.exists(INFO_FILE):
        return render_template("student_list.html", students=[])

    with open(INFO_FILE, "r") as f:
        people_info = json.load(f)

    student_list = []
    for name, info in people_info.items():
        id_img_path = os.path.join(REGISTERED_FACES_DIR, f"{name}_id.png")
        id_img_data = ""
        if os.path.exists(id_img_path):
            with open(id_img_path, "rb") as img_file:
                id_img_data = "data:image/png;base64," + base64.b64encode(img_file.read()).decode()

        student_list.append({
            "name": info.get("Full Name", name),
            "age": info.get("Age", "N/A"),
            "occupation": info.get("Occupation", "N/A"),
            "country": info.get("Country", "N/A"),
            "photo": id_img_data
        })

    return render_template("student_list.html", students=student_list)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
