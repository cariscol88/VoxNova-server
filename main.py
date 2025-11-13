import os
import io
import wave
import numpy as np
import openai
from flask import Flask, request, jsonify

# =========================
# CONFIGURACIÓN API
# =========================
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

# =========================
# Flask app
# =========================
app = Flask(__name__)

# Idiomas objetivo
target_languages = ["ita", "eng", "esp", "fra", "deu", "zh", "gr"]

# Carpeta temporal
TMP_FOLDER = "/tmp/tts_voxnova"
os.makedirs(TMP_FOLDER, exist_ok=True)

# =========================
# Funciones auxiliares
# =========================
def write_wav_pcm16(audio_data, sample_rate, filename):
    pcm_data = np.int16(np.clip(audio_data, -1, 1) * 32767)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

# Detect language mock
def detect_language(text):
    return "eng"  # por defecto para pruebas

# Procesar audio: guardamos WAV y retornamos mock TTS
def process_audio_file(file_bytes, filename="temp.wav"):
    filepath = os.path.join(TMP_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)

    # Mock de transcripción y TTS
    return {
        "transcript": "Texto transcrito simulado",
        "tts_files": {lang: f"/tmp/tts_{lang}.wav" for lang in target_languages}
    }

# =========================
# Endpoints
# =========================
@app.route("/process_audio", methods=["POST"])
def process_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    result = process_audio_file(file.read(), file.filename)
    return jsonify(result)

# Endpoint raíz para healthcheck
@app.route("/")
def index():
    return "Server OK", 200

# =========================
# Export app para Gunicorn
# =========================
# Railway detecta la variable "app" automáticamente
# y no necesita ejecutar app.run()
