# audio_processor.py
from aiortc import MediaStreamTrack

class AudioProcessor:
    def __init__(self):
        self.frame_count = 0

    async def handle_frame(self, frame):
        """
        Recibe un frame de aiortc, lo convierte a ndarray y loguea tamaño.
        """
        pcm = frame.to_ndarray()

        # Aseguramos mono si viniera estéreo
        if pcm.ndim > 1:
            pcm = pcm[:, 0]

        self.frame_count += 1
        print(f"[AudioProcessor] frame {self.frame_count}, samples: {len(pcm)}")
