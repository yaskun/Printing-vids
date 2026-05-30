import requests
from bs4 import BeautifulSoup
from google import genai
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

def retry_with_backoff(func, max_retries=5, initial_sleep=2):
    """
    Decorador o utilidad para reintentar llamadas a la API con retroceso exponencial.
    Ideal para manejar errores 429 (Too Many Requests).
    """
    def wrapper(*args, **kwargs):
        retries = 0
        sleep_time = initial_sleep
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    retries += 1
                    if retries == max_retries:
                        print(f"Máximo de reintentos alcanzado para la API de Gemini.")
                        raise e

                    # Añadir un pequeño factor aleatorio (jitter) para evitar colisiones
                    actual_sleep = sleep_time + random.uniform(0, 1)
                    print(f"Error 429 detectado. Reintentando en {actual_sleep:.2f}s... (Intento {retries}/{max_retries})")
                    time.sleep(actual_sleep)
                    sleep_time *= 2 # Retroceso exponencial
                else:
                    raise e
    return wrapper

class NewsProcessor:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

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

    def _call_gemini_generate(self, prompt):
        return self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )

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

        # Aplicar reintento con backoff
        safe_call = retry_with_backoff(self._call_gemini_generate)
        response = safe_call(prompt)

        # Pausa de cortesía para evitar ráfagas
        time.sleep(1)
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

        safe_call = retry_with_backoff(self._call_gemini_generate)
        response = safe_call(prompt)

        time.sleep(1)
        return response.text.strip()

    def _call_gemini_image(self, prompt):
        return self.client.models.generate_image(
            model="imagen-3.0-generate-001",
            prompt=prompt
        )

    def generate_thumbnail(self, prompt, output_path="temp/thumbnail.png"):
        try:
            safe_call = retry_with_backoff(self._call_gemini_image)
            response = safe_call(prompt)

            if response.images:
                response.images[0].save(output_path)
                return output_path
        except Exception as e:
            print(f"Error generando miniatura: {e}")
            return None
