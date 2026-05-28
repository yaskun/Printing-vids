import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

class AudioGenerator:
    def __init__(self, api_key):
        self.client = ElevenLabs(api_key=api_key)

    def generate_audio(self, text, voice_id="pNInz6obpg8n9Y4avHCy", output_path="temp/voice.mp3"):
        """
        Genera audio a partir de texto usando ElevenLabs.
        Voice ID por defecto (Bella) o uno configurado por el usuario.
        """
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            audio = self.client.generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )

            # Guardar el audio
            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            return output_path
        except Exception as e:
            print(f"Error generando audio: {e}")
            return None
