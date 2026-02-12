from flask import Flask, jsonify, send_from_directory, request
import os, json, secrets

app = Flask(__name__)

USERS_FILE = "users.json"
SESSIONS_FILE = "sessions.json"
VIEWS_FILE = "views.json"


# =========================
# HELPERS
# =========================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def get_user_from_token():
    token = request.headers.get("Authorization")
    sessions = load_json(SESSIONS_FILE)
    return sessions.get(token)


# =========================
# LOGIN SYSTEM
# =========================

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    users = load_json(USERS_FILE)

    if data["user"] in users:
        return jsonify({"ok": False, "error": "exists"})

    users[data["user"]] = data["pass"]
    save_json(USERS_FILE, users)

    return jsonify({"ok": True})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    users = load_json(USERS_FILE)

    if users.get(data["user"]) != data["pass"]:
        return jsonify({"ok": False})

    token = secrets.token_hex(16)

    sessions = load_json(SESSIONS_FILE)
    sessions[token] = data["user"]
    save_json(SESSIONS_FILE, sessions)

    return jsonify({"ok": True, "token": token})


@app.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")
    sessions = load_json(SESSIONS_FILE)

    if token in sessions:
        del sessions[token]
        save_json(SESSIONS_FILE, sessions)

    return jsonify({"ok": True})


@app.route("/me")
def me():
    user = get_user_from_token()

    if not user:
        return jsonify({"logged": False})

    return jsonify({"logged": True, "user": user})


# =========================
# VIEWS
# =========================

@app.route("/view/<path:file>", methods=["POST"])
def add_view(file):
    views = load_json(VIEWS_FILE)
    views[file] = views.get(file, 0) + 1
    save_json(VIEWS_FILE, views)
    return jsonify({"ok": True})


# =========================
# VIDEOS
# =========================

def scan_videos():
    views = load_json(VIEWS_FILE)
    items = []

    for file in os.listdir("videos"):
        if file.endswith(".mp4"):
            name = os.path.splitext(file)[0]
            items.append({
                "title": name,
                "file": file,
                "thumb": name + ".jpg",
                "views": views.get(file, 0)
            })

    return items


@app.route("/videos")
def videos():
    return jsonify({"videos": scan_videos()})


@app.route("/trending")
def trending():
    vids = sorted(scan_videos(), key=lambda x: x["views"], reverse=True)
    return jsonify({"videos": vids})


# =========================
# FILES
# =========================

@app.route("/videos/<path:file>")
def vid(file):
    return send_from_directory("videos", file)

@app.route("/thumbs/<path:file>")
def th(file):
    return send_from_directory("thumbs", file)


# =========================
# SPA
# =========================
@app.route("/")
@app.route("/trending-page")
@app.route("/me-page")
def index():
    return send_from_directory("web", "index.html")


app.run(host="0.0.0.0", port=8000)
