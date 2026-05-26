'''
import cv2
import os
import numpy as np
import pandas as pd
import joblib

from flask import Flask, render_template, request, redirect
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# FOLDERS
# -----------------------------
FACE_DIR = "static/faces"
ATTENDANCE_DIR = "static/attendance"
MODEL_DIR = "model"
MODEL_PATH = "model/face_model.pkl"

os.makedirs(FACE_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------------
# FACE DETECTOR
# -----------------------------
detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

# -----------------------------
# ATTENDANCE FILE
# -----------------------------
today = datetime.now().strftime("%Y-%m-%d")
attendance_file = f"{ATTENDANCE_DIR}/{today}.csv"

if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Name", "ID", "Time"])
    df.to_csv(attendance_file, index=False)


# -----------------------------
# TRAIN MODEL
# -----------------------------
def train_model():

    faces = []
    labels = []

    users = os.listdir(FACE_DIR)

    for user in users:

        user_path = os.path.join(FACE_DIR, user)

        for image_name in os.listdir(user_path):

            image_path = os.path.join(user_path, image_name)

            img = cv2.imread(image_path)

            if img is None:
                continue

            img = cv2.resize(img, (100, 100))

            faces.append(img.flatten())
            labels.append(user)

    if len(faces) == 0:
        return

    model = KNeighborsClassifier(n_neighbors=3)

    model.fit(faces, labels)

    joblib.dump(model, MODEL_PATH)

    print("Model Trained Successfully")


# -----------------------------
# EXTRACT FACE
# -----------------------------
def detect_face(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    return faces


# -----------------------------
# MARK ATTENDANCE
# -----------------------------
def mark_attendance(name):

    user_name = name.split("_")[0]
    user_id = name.split("_")[1]

    df = pd.read_csv(attendance_file)

    if int(user_id) not in list(df["ID"]):

        current_time = datetime.now().strftime("%H:%M:%S")

        new_row = {
            "Name": user_name,
            "ID": user_id,
            "Time": current_time
        }

        df.loc[len(df)] = new_row

        df.to_csv(attendance_file, index=False)

        print("Attendance Marked")


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():

    df = pd.read_csv(attendance_file)

    return render_template(
        "index.html",
        names=list(df["Name"]),
        ids=list(df["ID"]),
        times=list(df["Time"]),
        total=len(os.listdir(FACE_DIR))
    )


# -----------------------------
# ADD USER
# -----------------------------
@app.route("/add", methods=["POST"])
def add_user():

    name = request.form["name"]
    user_id = request.form["userid"]

    folder_name = f"{name}_{user_id}"

    user_path = os.path.join(FACE_DIR, folder_name)

    os.makedirs(user_path, exist_ok=True)

    cap = cv2.VideoCapture(0)

    count = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        faces = detect_face(frame)

        for (x, y, w, h) in faces:

            face = frame[y:y+h, x:x+w]

            face = cv2.resize(face, (100, 100))

            cv2.imwrite(
                f"{user_path}/{count}.jpg",
                face
            )

            count += 1

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            f"Images Captured: {count}/20",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        cv2.imshow("Adding User", frame)

        if cv2.waitKey(1) == 27 or count >= 20:
            break

    cap.release()
    cv2.destroyAllWindows()

    train_model()

    return redirect("/")


# -----------------------------
# TAKE ATTENDANCE
# -----------------------------
@app.route("/start")
def start_attendance():

    if not os.path.exists(MODEL_PATH):
        return "Please add users first."

    model = joblib.load(MODEL_PATH)

    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        faces = detect_face(frame)

        for (x, y, w, h) in faces:

            face = frame[y:y+h, x:x+w]

            face = cv2.resize(face, (100, 100))

            prediction = model.predict(
                face.flatten().reshape(1, -1)
            )[0]

            mark_attendance(prediction)

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (255, 0, 0),
                2
            )

            cv2.putText(
                frame,
                prediction,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        cv2.imshow("Attendance System", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    return redirect("/")


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
'''

import cv2
import os
import numpy as np
import pandas as pd
import joblib

from flask import Flask, render_template, request, redirect, send_file
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime

app = Flask(__name__)

# --------------------------------
# FOLDERS
# --------------------------------
FACE_DIR = "static/faces"
ATTENDANCE_DIR = "static/attendance"
MODEL_DIR = "model"

MODEL_PATH = "model/face_model.pkl"

os.makedirs(FACE_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# --------------------------------
# FACE DETECTOR
# --------------------------------
detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

# --------------------------------
# ATTENDANCE FILE
# --------------------------------
today = datetime.now().strftime("%Y-%m-%d")

attendance_file = f"{ATTENDANCE_DIR}/{today}.csv"

if not os.path.exists(attendance_file):

    df = pd.DataFrame(columns=["Name", "ID", "Time"])

    df.to_csv(attendance_file, index=False)


# --------------------------------
# TRAIN MODEL
# --------------------------------
def train_model():

    faces = []
    labels = []

    users = os.listdir(FACE_DIR)

    for user in users:

        user_path = os.path.join(FACE_DIR, user)

        for image_name in os.listdir(user_path):

            image_path = os.path.join(user_path, image_name)

            img = cv2.imread(image_path)

            if img is None:
                continue

            img = cv2.resize(img, (100, 100))

            faces.append(img.flatten())

            labels.append(user)

    if len(faces) == 0:
        return

    model = KNeighborsClassifier(n_neighbors=3)

    model.fit(faces, labels)

    joblib.dump(model, MODEL_PATH)

    print("Model Trained Successfully")


# --------------------------------
# DETECT FACE
# --------------------------------
def detect_face(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    return faces


# --------------------------------
# MARK ATTENDANCE
# --------------------------------
def mark_attendance(name):

    username = name.split("_")[0]
    userid = name.split("_")[1]

    df = pd.read_csv(attendance_file)

    if int(userid) not in list(df["ID"]):

        current_time = datetime.now().strftime("%H:%M:%S")

        new_row = {
            "Name": username,
            "ID": userid,
            "Time": current_time
        }

        df.loc[len(df)] = new_row

        df.to_csv(attendance_file, index=False)

        print("Attendance Marked")


# --------------------------------
# HOME PAGE
# --------------------------------
@app.route("/")
def home():

    df = pd.read_csv(attendance_file)

    return render_template(
        "index.html",
        names=list(df["Name"]),
        ids=list(df["ID"]),
        times=list(df["Time"]),
        total=len(os.listdir(FACE_DIR))
    )


# --------------------------------
# SEARCH USER
# --------------------------------
@app.route("/search", methods=["POST"])
def search():

    keyword = request.form["keyword"]

    df = pd.read_csv(attendance_file)

    result = df[
        df["Name"].astype(str).str.contains(keyword, case=False)
        |
        df["ID"].astype(str).str.contains(keyword)
    ]

    return render_template(
        "index.html",
        names=list(result["Name"]),
        ids=list(result["ID"]),
        times=list(result["Time"]),
        total=len(os.listdir(FACE_DIR))
    )


# --------------------------------
# EXPORT TO EXCEL
# --------------------------------
@app.route("/export")
def export_excel():

    excel_file = f"{ATTENDANCE_DIR}/{today}.xlsx"

    df = pd.read_csv(attendance_file)

    df.to_excel(excel_file, index=False)

    return send_file(
        excel_file,
        as_attachment=True
    )


# --------------------------------
# ADD USER
# --------------------------------
@app.route("/add", methods=["POST"])
def add_user():

    name = request.form["name"]

    userid = request.form["userid"]

    folder_name = f"{name}_{userid}"

    user_path = os.path.join(FACE_DIR, folder_name)

    os.makedirs(user_path, exist_ok=True)

    cap = cv2.VideoCapture(0)

    count = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        faces = detect_face(frame)

        for (x, y, w, h) in faces:

            face = frame[y:y+h, x:x+w]

            face = cv2.resize(face, (100, 100))

            cv2.imwrite(
                f"{user_path}/{count}.jpg",
                face
            )

            count += 1

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            f"Captured: {count}/20",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        cv2.imshow("Add User", frame)

        if cv2.waitKey(1) == 27 or count >= 20:
            break

    cap.release()

    cv2.destroyAllWindows()

    train_model()

    return redirect("/")


# --------------------------------
# START ATTENDANCE
# --------------------------------
@app.route("/start")
def start():

    if not os.path.exists(MODEL_PATH):

        return "Please Add Users First"

    model = joblib.load(MODEL_PATH)

    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        faces = detect_face(frame)

        for (x, y, w, h) in faces:

            face = frame[y:y+h, x:x+w]

            face = cv2.resize(face, (100, 100))

            prediction = model.predict(
                face.flatten().reshape(1, -1)
            )[0]

            mark_attendance(prediction)

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (255, 0, 0),
                2
            )

            cv2.putText(
                frame,
                prediction,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        cv2.imshow("Attendance System", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()

    cv2.destroyAllWindows()

    return redirect("/")


# --------------------------------
# RUN APP
# --------------------------------
if __name__ == "__main__":

    app.run(debug=True)