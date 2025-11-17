# audio_processor.py
import numpy as np
from aiortc import MediaStreamTrack

class AudioProcessor:
    def __init__(self):
        self.frame_count = 0

    async def handle_frame(self, frame):
        pcm = frame.to_ndarray()

        # Asegurar forma correcta (mono)
        if pcm.ndim > 1:
            pcm = pcm[:, 0]

        self.frame_count += 1

        print("[AudioProcessor] frame recibido:", len(pcm), "bytes")

        # retorno idéntico
        return frame
