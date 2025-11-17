# server.py
import os
import asyncio

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
import aiohttp_cors

from audio_processor import AudioProcessor

# -------------------------
# Configuración API (por ahora no usada)
# -------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# -------------------------
# Estado global
# -------------------------
pcs = set()
processor = AudioProcessor()

# -------------------------
# Handlers
# -------------------------
async def offer(request: web.Request) -> web.Response:
    """
    Endpoint WebRTC: recibe SDP offer del navegador y devuelve SDP answer.
    Cada vez que llega un track de audio, se crea una tarea que bombea frames
    hacia AudioProcessor.handle_frame().
    """
    params = await request.json()
    offer_sdp = params["sdp"]
    offer_type = params["type"]

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    async def on_track(track):
        print("Nuevo track recibido:", track.kind)

        if track.kind == "audio":
            async def pump():
                while True:
                    frame = await track.recv()
                    await processor.handle_frame(frame)

            # tarea en background para leer continuamente el audio
            asyncio.create_task(pump())

    offer_desc = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer_desc)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )


async def index(request: web.Request) -> web.Response:
    return web.Response(text="Server OK", status=200)


async def on_shutdown(app: web.Application):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

# -------------------------
# Montaje de la app aiohttp + CORS
# -------------------------
app = web.Application()
app.on_shutdown.append(on_shutdown)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Ruta /offer
offer_resource = cors.add(app.router.add_resource("/offer"))
cors.add(offer_resource.add_route("POST", offer))

# Ruta raíz /
root_resource = cors.add(app.router.add_resource("/"))
cors.add(root_resource.add_route("GET", index))

# -------------------------
# Ejecutar servidor (Railway corre: `python server.py`)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    web.run_app(app, port=port)
