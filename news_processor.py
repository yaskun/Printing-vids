import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

def retry_with_backoff(func, max_retries=5, initial_sleep=5):
    """
    Utilidad para reintentar llamadas a la API. OpenRouter suele ser más estable en cuotas
    pero los reintentos ayudan con errores de red o saturación temporal.
    """
    def wrapper(*args, **kwargs):
        retries = 0
        sleep_time = initial_sleep
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg:
                    retries += 1
                    actual_sleep = sleep_time + random.uniform(0, 5)
                    print(f"OpenRouter Rate Limit. Reintentando en {actual_sleep:.2f}s...")
                    time.sleep(actual_sleep)
                    sleep_time *= 2
                else:
                    raise e
    return wrapper

class NewsProcessor:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model_id = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v3") # O el modelo específico que el usuario quiera

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
            text = article.get_text(separator=' ', strip=True) if article else soup.get_text(separator=' ', strip=True)
            return text[:12000]
        except Exception as e:
            return f"Error al extraer contenido: {str(e)}"

    def _call_ai(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def generate_script(self, news_text, channel_niche, custom_prompt):
        prompt = f"""
        Actúa como un experto creador de contenido para YouTube Shorts.
        Nicho: {channel_niche} | Estilo: {custom_prompt}
        Noticia: {news_text}

        Tarea: Crea un guion narrativo dinámico en ESPAÑOL de 30-40 seg.
        Solo devuelve el texto hablado.
        """
        safe_call = retry_with_backoff(self._call_ai)
        return safe_call(prompt).strip()

    def generate_marketing_assets(self, script, channel_context):
        prompt = f"""
        Como experto en YouTube Marketing para el canal {channel_context}:
        Guion: {script}

        Genera:
        1. Título SEO-hook.
        2. Descripción breve + hashtags.
        3. Prompt para miniatura impactante.

        Formato:
        TITULO: ...
        DESCRIPCION: ...
        PROMPT_MINIATURA: ...
        """
        safe_call = retry_with_backoff(self._call_ai)
        return safe_call(prompt).strip()
