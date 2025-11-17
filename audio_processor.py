# audio_processor.py

import asyncio

class AudioProcessor:
    def __init__(self):
        # Si querés acumular audio temporalmente:
        self.buffer = bytearray()
        self.frame_count = 0

    async def handle_frame(self, frame):
        """
        frame: objeto AudioFrame de aiortc
        Convertimos a WAV/PCM y lo guardamos o pasamos al pipeline.
        """
        pcm = frame.to_ndarray().tobytes()
        self.buffer.extend(pcm)
        self.frame_count += 1

        # Debug mínimo controlado
        if self.frame_count % 50 == 0:
            print(f"[AudioProcessor] {self.frame_count} frames recibidos")
