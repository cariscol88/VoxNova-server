# webrtc_server.py
import asyncio
import json
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack

pcs = set()  # lista de peer connections activas

class AudioRelayTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()  # tipo 'audio'
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
            # aquí podrías hacer forward a otro lugar o guardar audio
            pc.addTrack(relay)

    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app = web.Application()
app.router.add_post("/offer", offer)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=8080)
