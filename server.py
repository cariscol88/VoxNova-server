import asyncio
from flask import Flask, request, jsonify
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack

app = Flask(__name__)
pcs = set()  # lista de conexiones activas

# Clase base (aún sin procesar audio)
class AudioSink(MediaStreamTrack):
    kind = "audio"
    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        # Aquí más adelante procesaremos el audio
        return frame

@app.route("/offer", methods=["POST"])
async def offer():
    params = await request.get_json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            pc.addTrack(AudioSink(track))

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return jsonify({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
