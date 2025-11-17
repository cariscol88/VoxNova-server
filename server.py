# server.py
import os
import io
import wave
import json
import numpy as np
import asyncio

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
import aiohttp_cors

from audio_processor import AudioProcessor

# -------------------------
# Inicializar procesador global
# -------------------------
processor = AudioProcessor()

# -------------------------
# Carpetas temporales
# -------------------------
TMP_FOLDER = "/tmp/tts_voxnova"
os.makedirs(TMP_FOLDER, exist_ok=True)

# -------------------------
# Procesamiento de uploads (endpoint viejo)
# -------------------------
target_languages = ["ita", "eng", "esp", "fra", "deu", "zh", "gr"]

def process_audio_file(file_bytes, filename="temp.wav"):
    filepath = os.path.join(TMP_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return {
        "transcript": "Texto transcrito simulado",
        "tts_files": {lang: f"/tmp/tts_{lang}.wav" for lang in target_languages}
    }

async def process_audio(request):
    reader = await request.multipart()
    part = await reader.next()
    if part is None or part.name != "file":
        return web.json_response({"error": "No file part"}, status=400)
    file_bytes = await part.read()
    result = process_audio_file(file_bytes, part.filename)
    return web.json_response(result)

# -------------------------
# WebRTC
# -------------------------
pcs = set()

async def offer(request):
    params = await request.json()
    offer_sdp = params["sdp"]
    offer_type = params["type"]

    pc = RTCPeerConnection()
    pcs.add(pc)

    pc.addTransceiver("audio", direction="recvonly")  # ← IMPORTANTE

    processor = AudioProcessor()

    @pc.on("track")
    async def on_track(track):
        print(f"Nuevo track recibido: {track.kind}")

        if track.kind == "audio":
            async def forward_frames():
                while True:
                    frame = await track.recv()
                    await processor.handle_frame(frame)

            asyncio.create_task(forward_frames())

    offer_desc = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer_desc)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )

async def on_shutdown(app):
    await asyncio.gather(*[pc.close() for pc in pcs])
    pcs.clear()

# -------------------------
# Iniciar servidor
# -------------------------
app = web.Application()
app.on_shutdown.append(on_shutdown)

# CORS
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Rutas
r1 = cors.add(app.router.add_resource("/process_audio"))
cors.add(r1.add_route("POST", process_audio))

r2 = cors.add(app.router.add_resource("/offer"))
cors.add(r2.add_route("POST", offer))

r3 = cors.add(app.router.add_resource("/"))
cors.add(r3.add_route("GET", lambda r: web.Response(text="Server OK", status=200)))

if __name__ == "__main__":
    web.run_app(app, port=8080)
