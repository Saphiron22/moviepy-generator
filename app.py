from flask import Flask, request, jsonify
import os
import random
import tempfile
from moviepy.editor import *
from dotenv import load_dotenv
from supabase import create_client
import requests

# Charger .env
load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/generate", methods=["POST"])
def generate_video():
    data = request.get_json()
    playlist = data.get("playlist", "Rap Triste")

    # Étapes de sélection
    mp3_files = list_files(f"extraits-musicaux/{playlist}/", ".mp3")
    screenshot_files = list_files(f"extraits-musicaux/{playlist}/Screenshot/", ".mp4")
    cover_images = list_files(f"extraits-musicaux/{playlist}/Screenshot/", [".jpg", ".png"])
    hooks = list_files("hooks/", ".mp4")

    if not (mp3_files and screenshot_files and cover_images and hooks):
        return jsonify({"error": "Fichiers manquants dans Supabase"}), 400

    music_file = random.choice(mp3_files)
    scroll_video = random.choice(screenshot_files)
    cover_image = random.choice(cover_images)
    hook_video = random.choice(hooks)

    # Télécharger les fichiers temporairement
    music_path = download_file(music_file)
    scroll_path = download_file(scroll_video)
    cover_path = download_file(cover_image)
    hook_path = download_file(hook_video)

    # Générer vidéo
    output_path = generate_final_video(hook_path, music_path, cover_path, scroll_path)

    # Upload vers Supabase
    video_name = f"video_{random.randint(1000,9999)}.mp4"
    with open(output_path, "rb") as f:
        supabase.storage.from_(BUCKET_NAME).upload(video_name, f, {"content-type": "video/mp4"})

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{video_name}"

    return jsonify({
        "message": "Vidéo générée avec succès",
        "playlist": playlist,
        "video_url": public_url
    })

def list_files(prefix, extensions):
    res = supabase.storage.from_("extraits-musicaux").list(prefix)
    return [f"{prefix}{f['name']}" for f in res if any(f["name"].endswith(ext) for ext in (extensions if isinstance(extensions, list) else [extensions]))]

def download_file(path):
    url = f"{SUPABASE_URL}/storage/v1/object/public/{path}"
    local = tempfile.NamedTemporaryFile(delete=False)
    local.write(requests.get(url).content)
    local.close()
    return local.name

def generate_final_video(hook, audio, cover_img, scroll):
    # MoviePy processing simple (à affiner ensuite)
    hook_clip = VideoFileClip(hook).without_audio()
    scroll_clip = VideoFileClip(scroll).resize(hook_clip.size)
    cover = ImageClip(cover_img).set_duration(3).resize(width=hook_clip.w).set_position("center")

    final_clip = concatenate_videoclips([hook_clip, scroll_clip])
    final_clip = CompositeVideoClip([final_clip, cover.set_start(0)])

    final_clip = final_clip.set_audio(AudioFileClip(audio)).set_duration(15)
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    final_clip.write_videofile(output.name, codec="libx264", audio_codec="aac")
    return output.name