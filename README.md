# AutoVideo Studio 🎬

Esta aplicación automatiza la creación de videos para YouTube Shorts a partir de noticias de última hora.

## Características
- **Extracción de Noticias:** Scrapea automáticamente URLs de noticias.
- **IA Narrativa:** Usa Gemini 1.5 para crear guiones optimizados por nicho.
- **Voz Profesional:** Integración con ElevenLabs para narración multilingüe.
- **Edición Automática:** Montaje de clips de fondo con subtítulos quemados (estilo Shorts).
- **Marketing:** Generación de títulos SEO, descripciones y prompts de miniaturas.
- **YouTube API:** Subida automática y gestión de múltiples canales.

## Configuración

1. **Dependencias:**
   Es crucial instalar las dependencias dentro de tu entorno virtual (venv):
   ```bash
   pip install -r requirements.txt
   ```
   Si recibes un error tipo `ModuleNotFoundError: No module named 'openai'`, asegúrate de haber ejecutado el comando anterior y de que tu IDE/Terminal esté usando el intérprete de Python correcto.

2. **Variables de Entorno:**
   Crea un archivo `.env` basado en `.env.example`:
   - `GEMINI_API_KEY`: Tu llave de Google AI Studio.
   - `ELEVENLABS_API_KEY`: Tu llave de ElevenLabs.
   - `GOOGLE_APPLICATION_CREDENTIALS`: Ruta a tu archivo JSON de credenciales de Google Cloud (opcional para la subida).

3. **YouTube OAuth:**
   Para habilitar la subida, coloca tu archivo `client_secrets.json` (descargado de Google Cloud Console) en la raíz del proyecto.

## Uso

### Aplicación Web (Gestión Manual)
```bash
streamlit run app.py
```
Desde la interfaz puedes:
- Crear canales y definir sus nichos/prompts.
- Subir tu librería de clips a `assets/clips`.
- Añadir URLs de noticias y generar videos bajo demanda.

### Motor de Automatización (24/7)
```bash
python automation_engine.py
```
Este script se ejecutará en segundo plano y procesará los canales configurados diariamente según el horario programado.

## Estructura de Carpetas
- `assets/clips/`: Coloca aquí tus videos de fondo.
- `channels/`: Configuraciones específicas por canal.
- `data/`: Almacenamiento de base de datos JSON y tokens de YouTube.
- `temp/`: Archivos temporales de procesamiento.
