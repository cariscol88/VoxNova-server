# server.py
import os
import io
import wave
import json
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
import aiohttp_cors

# -------------------------
# Configuración API
# -------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# -------------------------
# Carpeta temporal
# -------------------------
TMP_FOLDER = "/tmp/tts_voxnova"
os.makedirs(TMP_FOLDER, exist_ok=True)

# -------------------------
# Funciones auxiliares
# -------------------------
def write_wav_pcm16(audio_data, sample_rate, filename):
    pcm_data = np.int16(np.clip(audio_data, -1, 1) * 32767)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

target_languages = ["ita", "eng", "esp", "fra", "deu", "zh", "gr"]

def process_audio_file(file_bytes, filename="temp.wav"):
    filepath = os.path.join(TMP_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return {
        "transcript": "Texto transcrito simulado",
        "tts_files": {lang: f"/tmp/tts_{lang}.wav" for lang in target_languages}
    }

# -------------------------
# Endpoints
# -------------------------
async def process_audio(request):
    reader = await request.multipart()
    file_part = await reader.next()
    if file_part is None or file_part.name != "file":
        return web.json_response({"error": "No file part"}, status=400)
    file_bytes = await file_part.read()
    result = process_audio_file(file_bytes, file_part.filename)
    return web.json_response(result)

pcs = set()

class AudioRelayTrack(MediaStreamTrack):
    kind = "audio"
    def __init__(self, track):
        super().__init__()
        self.track = track
    async def recv(self):
        return await self.track.recv()

async def offer(request):
    params = await request.json()
    offer_sdp = params["sdp"]
    offer_type = params["type"]

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    async def on_track(track):
        print(f"Nuevo track recibido: {track.kind}")
        if track.kind == "audio":
            relay = AudioRelayTrack(track)
            pc.addTrack(relay)

    offer_desc = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer_desc)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

# -------------------------
# App aiohttp + CORS
# -------------------------
app = web.Application()
app.on_shutdown.append(on_shutdown)

# Configurar CORS antes de registrar rutas
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Registrar rutas con CORS
process_audio_resource = cors.add(app.router.add_resource("/process_audio"))
cors.add(process_audio_resource.add_route("POST", process_audio))

offer_resource = cors.add(app.router.add_resource("/offer"))
cors.add(offer_resource.add_route("POST", offer))

root_resource = cors.add(app.router.add_resource("/"))
cors.add(root_resource.add_route("GET", lambda r: web.Response(text="Server OK", status=200)))

# -------------------------
# Ejecutar servidor
# -------------------------
if __name__ == "__main__":
    web.run_app(app, port=8080)
