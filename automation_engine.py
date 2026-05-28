import json
import os
import time
import schedule
from news_processor import NewsProcessor
from audio_generator import AudioGenerator
from video_editor import VideoEditor
from youtube_uploader import YouTubeUploader
from dotenv import load_dotenv

load_dotenv()

class AutomationEngine:
    def __init__(self):
        self.news_processor = NewsProcessor(os.getenv("GEMINI_API_KEY"))
        self.audio_generator = AudioGenerator(os.getenv("ELEVENLABS_API_KEY"))
        self.video_editor = VideoEditor()
        self.uploader = YouTubeUploader()

    def process_channel(self, channel_name, config):
        print(f"--- Procesando Canal: {channel_name} ---")
        if not config['urls']:
            print(f"No hay URLs para {channel_name}")
            return

        # Tomar la primera URL (o podrías rotarlas)
        url = config['urls'][0]

        try:
            # 1. Extraer
            content = self.news_processor.fetch_news_content(url)

            # 2. Guion
            script = self.news_processor.generate_script(content, config['niche'], config['prompt'])

            # 3. Audio
            audio_path = self.audio_generator.generate_audio(script, voice_id=config.get('voice_id'))

            # 4. Video
            video_output = f"temp/auto_{channel_name.replace(' ', '_')}.mp4"
            self.video_editor.create_video(audio_path, video_output, script)

            # 5. Marketing
            assets_text = self.news_processor.generate_marketing_assets(script, config['niche'])
            # Parsear assets (simplificado)
            title = "Video Automatizado"
            description = "Contenido generado automáticamente."
            for line in assets_text.split('\n'):
                if line.startswith('TITULO:'): title = line.replace('TITULO:', '').strip()
                if line.startswith('DESCRIPCION:'): description = line.replace('DESCRIPCION:', '').strip()

            # 6. Subir (Solo si existe client_secrets.json)
            if os.path.exists('client_secrets.json'):
                print(f"Subiendo a YouTube: {title}")
                # self.uploader.upload_video(channel_name, video_output, title, description)
            else:
                print("Saltando subida: client_secrets.json no encontrado.")

        except Exception as e:
            print(f"Error procesando canal {channel_name}: {e}")

    def run_daily_cycle(self):
        if not os.path.exists("data/channels.json"):
            return

        with open("data/channels.json", "r") as f:
            channels = json.load(f)

        for name, config in channels.items():
            self.process_channel(name, config)

def main():
    engine = AutomationEngine()

    # Programar ejecución diaria (ejemplo a las 08:00)
    schedule.every().day.at("08:00").do(engine.run_daily_cycle)

    print("Motor de automatización iniciado. Esperando tareas programadas...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Para pruebas inmediatas puedes llamar a:
    # AutomationEngine().run_daily_cycle()
    main()
