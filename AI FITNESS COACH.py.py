import cv2
import mediapipe as mp
import numpy as np
import time
import csv
from datetime import datetime

# ---------------- INIT ----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6,
                    min_tracking_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
time.sleep(2)

if not cap.isOpened():
    print("Camera not accessible")
    exit()

TARGET_REPS = 10
REP_COOLDOWN = 0.8  # balanced

categories = {
    1: ("UPPER BODY", ["Bicep Curl", "Shoulder Press", "Push-ups", "Pull-ups"]),
    2: ("LOWER BODY", ["Squats", "Lunges", "Calf Raises"]),
    3: ("CORE", ["Plank", "Crunches", "Mountain Climbers"]),
    4: ("FULL BODY / CARDIO", ["Jumping Jacks", "High Knees"])
}

mode = "CATEGORY"
category = None
exercise = None
cat_key = None

reps = 0
sets = 0
stage = None
last_rep_time = 0

# ---------- PLANK TIMER ----------
plank_start_time = None
plank_elapsed = 0
plank_running = False

# ---------- PERFORMANCE ----------
angle_history = []
smoothness_score = 0
depth_score = 0
performance_score = 0
form_warning = ""

LOG_FILE = "performance_log.csv"

def log_performance(ex_name, count, smoothness, depth, score):
    file_exists = False
    try:
        with open(LOG_FILE, 'r'):
            file_exists = True
    except:
        pass

    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Exercise", "Reps", "Smoothness", "Depth", "Score"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"),
                         ex_name, count, smoothness, depth, score])

# ---------- ANGLE ----------
def safe_angle(a, b, c, frame_shape):
    h, w = frame_shape[:2]
    a = np.array([a[0] * w, a[1] * h])
    b = np.array([b[0] * w, b[1] * h])
    c = np.array([c[0] * w, c[1] * h])

    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return 180
    cosang = np.clip(np.dot(ba, bc) / denom, -1, 1)
    return np.degrees(np.arccos(cosang))

def calculate_performance(angle_list):
    if len(angle_list) < 6:
        return 0, 0, 0, ""

    velocity = np.diff(angle_list)
    smoothness = max(0, 100 - int(np.std(velocity) * 12))

    min_ang = min(angle_list)
    depth = max(40, min(100, int((180 - min_ang) * 0.7)))

    warning = ""
    if smoothness < 55:
        warning = "Control movement"

    final_score = int(smoothness * 0.5 + depth * 0.5)
    return smoothness, depth, final_score, warning


cv2.namedWindow("AI Gym Trainer", cv2.WINDOW_NORMAL)

# ================= MAIN LOOP =================
while True:
    if cv2.getWindowProperty("AI Gym Trainer", cv2.WND_PROP_VISIBLE) < 1:
        break

    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = pose.process(rgb)
    now = time.time()

    # -------- CATEGORY --------
    if mode == "CATEGORY":
        cv2.putText(frame, "SELECT CATEGORY (1-4)", (40, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        y = 120
        for k, v in categories.items():
            cv2.putText(frame, f"{k}. {v[0]}", (40, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            y += 50

        cv2.putText(frame, "ESC : Exit",
                    (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # -------- EXERCISE --------
    elif mode == "EXERCISE":
        cv2.putText(frame, f"{category} EXERCISES", (40, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        y = 120
        for i, ex in enumerate(categories[cat_key][1]):
            cv2.putText(frame, f"{i+1}. {ex}", (40, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            y += 40

        cv2.putText(frame, "Press B : Back",
                    (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # -------- TRACK --------
    elif mode == "TRACK":
        cv2.putText(frame, exercise, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3)

        if exercise == "Plank":
            if plank_running:
                plank_elapsed = now - plank_start_time

            display_time = max(0, int(plank_elapsed) - 2)
            mins = display_time // 60
            secs = display_time % 60

            cv2.putText(frame, f"Time: {mins:02d}:{secs:02d}",
                        (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

            cv2.putText(frame, "Press S : Start | Any Key : Stop",
                        (20, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        elif res.pose_landmarks:
            mp_draw.draw_landmarks(frame, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            lm = res.pose_landmarks.landmark
            def p(i): return [lm[i].x, lm[i].y]
            def v(i): return lm[i].visibility > 0.5

            ang = None
            down_th = up_th = None

            if exercise in ["Bicep Curl", "Shoulder Press"] and v(11) and v(13) and v(15):
                ang = safe_angle(p(11), p(13), p(15), frame.shape)
                down_th, up_th = 150, 90

            elif exercise in ["Push-ups", "Pull-ups"] and v(11) and v(13) and v(15):
                ang = safe_angle(p(11), p(13), p(15), frame.shape)
                down_th, up_th = 160, 100

            elif exercise in ["Squats", "Lunges"] and v(23) and v(25) and v(27):
                ang = safe_angle(p(23), p(25), p(27), frame.shape)
                down_th, up_th = 155, 110

            elif exercise == "Calf Raises" and v(25) and v(27) and v(31):
                ang = safe_angle(p(25), p(27), p(31), frame.shape)
                down_th, up_th = 170, 150

            elif exercise == "Crunches" and v(11) and v(23) and v(25):
                ang = safe_angle(p(11), p(23), p(25), frame.shape)
                down_th, up_th = 140, 100

            elif exercise in ["Jumping Jacks", "High Knees"] and v(11) and v(23) and v(25):
                ang = safe_angle(p(11), p(23), p(25), frame.shape)
                down_th, up_th = 150, 120

            if ang is not None:
                angle_history.append(ang)
                if len(angle_history) > 25:
                    angle_history.pop(0)

                if stage is None:
                    stage = "up"

                if ang < up_th:
                    stage = "down"

                if stage == "down" and ang > down_th:
                    if now - last_rep_time > REP_COOLDOWN:
                        reps += 1
                        smoothness_score, depth_score, performance_score, form_warning = \
                            calculate_performance(angle_history)
                        log_performance(exercise, reps,
                                        smoothness_score, depth_score, performance_score)
                        last_rep_time = now
                        stage = "up"

                        if reps >= TARGET_REPS:
                            sets += 1
                            reps = 0

            cv2.putText(frame, f"Reps: {reps}/{TARGET_REPS}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, f"Sets: {sets}", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(frame, f"Performance: {performance_score}%", (20, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

            if form_warning:
                cv2.putText(frame, f"Form: {form_warning}", (20, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.putText(frame, "Press B : Back | R : Reset",
                    (20, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    cv2.imshow("AI Gym Trainer", frame)
    key = cv2.waitKey(10) & 0xFF

    # -------- KEY HANDLING --------
    if mode == "CATEGORY":
        if key in [ord('1'), ord('2'), ord('3'), ord('4')]:
            cat_key = int(chr(key))
            category = categories[cat_key][0]
            mode = "EXERCISE"

    elif mode == "EXERCISE":
        if key == ord('b'):
            mode = "CATEGORY"
        elif ord('1') <= key <= ord('9'):
            idx = int(chr(key)) - 1
            if idx < len(categories[cat_key][1]):
                exercise = categories[cat_key][1][idx]
                mode = "TRACK"
                reps = 0
                sets = 0
                stage = None
                angle_history.clear()
                plank_elapsed = 0
                plank_running = False

    elif mode == "TRACK":
        if exercise == "Plank":
            if key == ord('s'):
                plank_running = True
                plank_start_time = now
            elif key not in [255, ord('b'), ord('r'), 27]:
                plank_running = False

        if key == ord('b'):
            mode = "EXERCISE"
            plank_running = False

        elif key == ord('r'):
            reps = 0
            sets = 0
            stage = None
            angle_history.clear()
            plank_elapsed = 0
            plank_running = False

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
