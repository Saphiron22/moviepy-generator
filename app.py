from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate_video():
    data = request.get_json()
    playlist = data.get("playlist", "unknown")

    # TODO: ici tu mets le vrai traitement MoviePy + upload Supabase
    fake_url = f"https://storage.supabase.com/fake/playlist_{playlist}.mp4"

    return jsonify({
        "message": "Vidéo générée !",
        "playlist": playlist,
        "video_url": fake_url
    })