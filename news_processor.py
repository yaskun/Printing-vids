import requests
from bs4 import BeautifulSoup
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

class NewsProcessor:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash" # Actualizado a la versión más reciente y estable

    def fetch_news_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            for script in soup(["script", "style"]):
                script.decompose()

            article = soup.find('article')
            if article:
                text = article.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)

            return text[:10000]
        except Exception as e:
            return f"Error al extraer contenido de {url}: {str(e)}"

    def generate_script(self, news_text, channel_niche, custom_prompt):
        prompt = f"""
        Actúa como un experto creador de contenido para YouTube Shorts.
        Nicho del canal: {channel_niche}
        Instrucciones de estilo: {custom_prompt}

        Noticia original:
        {news_text}

        Tarea:
        1. Crea un guion narrativo para un video de 30-40 segundos.
        2. El lenguaje debe ser dinámico, enganchador y adaptado a la audiencia del nicho.
        3. El guion DEBE estar en español.
        4. Solo devuelve el texto que será narrado, sin etiquetas tipo [Intro] o [Outro].
        5. Asegúrate de que el resumen cubra los puntos clave de la noticia.
        """

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        return response.text.strip()

    def generate_marketing_assets(self, script, channel_context):
        prompt = f"""
        Actúa como un experto en YouTube Marketing.
        Contexto del canal: {channel_context}
        Guion del video: {script}

        Tarea:
        Genera los siguientes elementos para este video:
        1. Un título optimizado para SEO (con gancho).
        2. Una descripción breve con hashtags.
        3. Un prompt detallado para generar una miniatura visualmente impactante relacionada con el tema.

        Formato de respuesta:
        TITULO: [Título aquí]
        DESCRIPCION: [Descripción aquí]
        PROMPT_MINIATURA: [Prompt aquí]
        """

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        return response.text.strip()

    def generate_thumbnail(self, prompt, output_path="temp/thumbnail.png"):
        """
        Genera una miniatura usando Imagen 3 vía el nuevo SDK.
        """
        try:
            # En el nuevo SDK, Imagen suele estar bajo models.generate_image
            # Nota: Esto depende de la disponibilidad del modelo en la API KEY
            response = self.client.models.generate_image(
                model="imagen-3.0-generate-001",
                prompt=prompt
            )

            if response.images:
                response.images[0].save(output_path)
                return output_path
        except Exception as e:
            print(f"Error generando miniatura: {e}")
            return None
