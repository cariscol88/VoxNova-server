# webrtc_server.py
import asyncio
import json
from aiohttp import web
import aiohttp_cors
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack

pcs = set()  # Lista de peer connections activas

class AudioRelayTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        return await self.track.recv()

async def offer(request):
    try:
        params = await request.json()
        offer_sdp = params["sdp"]
        offer_type = params["type"]
    except Exception as e:
        return web.Response(status=400, text=f"Error parsing JSON: {e}")

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    async def on_track(track):
        print(f"Nuevo track recibido: {track.kind}")
        if track.kind == "audio":
            relay = AudioRelayTrack(track)
            # Aquí podrías procesar audio o guardarlo
            pc.addTrack(relay)

    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

# ===============================
# Crear app y habilitar CORS
# ===============================
app = web.Application()
app.router.add_post("/offer", offer)
app.on_shutdown.append(on_shutdown)

# Configurar CORS para permitir cualquier origen
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == "__main__":
    # Railway usa el puerto 8080
    web.run_app(app, port=8080)
