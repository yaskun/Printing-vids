import streamlit as st
import os
import json
from news_processor import NewsProcessor
from audio_generator import AudioGenerator
from video_editor import VideoEditor
from youtube_uploader import YouTubeUploader
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de página
st.set_page_config(page_title="AutoVideo Studio", layout="wide", page_icon="🎬")

# Inicializar componentes de forma segura
gemini_key = os.getenv("GEMINI_API_KEY")
eleven_key = os.getenv("ELEVENLABS_API_KEY")

if 'news_processor' not in st.session_state:
    st.session_state.news_processor = NewsProcessor(gemini_key) if gemini_key else None
if 'audio_generator' not in st.session_state:
    st.session_state.audio_generator = AudioGenerator(eleven_key) if eleven_key else None
if 'video_editor' not in st.session_state:
    st.session_state.video_editor = VideoEditor()
if 'uploader' not in st.session_state:
    st.session_state.uploader = YouTubeUploader()

# Función para cargar configuración de canales
def load_channels():
    if os.path.exists("data/channels.json"):
        with open("data/channels.json", "r") as f:
            return json.load(f)
    return {}

def save_channels(channels):
    with open("data/channels.json", "w") as f:
        json.dump(channels, f, indent=4)

channels = load_channels()

# Sidebar para gestión de canales
st.sidebar.title("📺 Gestión de Canales")
channel_names = list(channels.keys())
selected_channel = st.sidebar.selectbox("Seleccionar Canal", ["+ Nuevo Canal"] + channel_names)

if selected_channel == "+ Nuevo Canal":
    with st.sidebar.form("new_channel_form"):
        new_name = st.text_input("Nombre del Canal")
        new_niche = st.text_area("Nicho/Contexto")
        new_prompt = st.text_area("Prompt de Estilo (Narrativa/Visual)")
        new_voice = st.text_input("ElevenLabs Voice ID", value="pNInz6obpg8n9Y4avHCy")
        submit_new = st.form_submit_button("Crear Canal")

        if submit_new and new_name:
            channels[new_name] = {
                "niche": new_niche,
                "prompt": new_prompt,
                "voice_id": new_voice,
                "urls": []
            }
            save_channels(channels)
            st.rerun()
else:
    # Editar canal seleccionado
    st.sidebar.subheader(f"Configuración: {selected_channel}")
    channels[selected_channel]["niche"] = st.sidebar.text_area("Nicho", value=channels[selected_channel]["niche"])
    channels[selected_channel]["prompt"] = st.sidebar.text_area("Prompt", value=channels[selected_channel]["prompt"])
    channels[selected_channel]["voice_id"] = st.sidebar.text_input("Voice ID", value=channels[selected_channel].get("voice_id", "pNInz6obpg8n9Y4avHCy"))

    if st.sidebar.button("Guardar Cambios"):
        save_channels(channels)
        st.success("Cambios guardados")

# Cuerpo principal
st.title("🎬 AutoVideo Studio")

if selected_channel != "+ Nuevo Canal":
    if not gemini_key or not eleven_key:
        st.error("⚠️ Faltan llaves de API (Gemini o ElevenLabs) en el archivo .env")
        st.info("Asegúrate de configurar GEMINI_API_KEY y ELEVENLABS_API_KEY para habilitar la generación.")

    st.info("🐢 **Modo de Alta Compatibilidad Activado**: La generación será pausada para evitar bloqueos de Google.")

    tab1, tab2, tab3 = st.tabs(["🚀 Generar Video", "📰 Fuentes de Noticias", "📁 Librería de Clips"])

    with tab1:
        st.header(f"Generar contenido para {selected_channel}")

        if not channels[selected_channel]["urls"]:
            st.warning("Añade algunas URLs de noticias en la pestaña 'Fuentes de Noticias' primero.")
        elif not st.session_state.news_processor:
            st.error("NewsProcessor no inicializado (revisa tu GEMINI_API_KEY)")
        else:
            url_to_process = st.selectbox("Seleccionar noticia para procesar", channels[selected_channel]["urls"])

            if st.button("Comenzar Producción 🎬"):
                with st.status("Procesando video...", expanded=True) as status:
                    # 1. Extraer noticia
                    status.write("Extrayendo contenido de la noticia...")
                    content = st.session_state.news_processor.fetch_news_content(url_to_process)

                    # 2. Generar Guion
                    status.write("Generando guion con Gemini...")
                    script = st.session_state.news_processor.generate_script(
                        content,
                        channels[selected_channel]["niche"],
                        channels[selected_channel]["prompt"]
                    )
                    st.text_area("Guion Generado", script, height=100)

                    # 3. Generar Audio
                    status.write("Generando voz con ElevenLabs...")
                    audio_path = st.session_state.audio_generator.generate_audio(
                        script,
                        voice_id=channels[selected_channel]["voice_id"]
                    )

                    # 4. Generar Video
                    status.write("Montando video y subtítulos...")
                    video_output = f"temp/{selected_channel.replace(' ', '_')}_video.mp4"
                    st.session_state.video_editor.create_video(audio_path, video_output, script)

                    # 5. Marketing Assets
                    status.write("Generando títulos y descripción...")
                    assets = st.session_state.news_processor.generate_marketing_assets(script, channels[selected_channel]["niche"])
                    st.markdown(f"### Activos Generados\n{assets}")

                    status.update(label="Producción completada!", state="complete")

                st.video(video_output)

                if st.button("Subir a YouTube 🚀"):
                    # Aquí iría la lógica de uploader.upload_video
                    st.info("Función de subida activada (requiere client_secrets.json)")

    with tab2:
        st.header("Gestionar Fuentes (URLs)")
        new_url = st.text_input("Nueva URL de Noticia")
        if st.button("Añadir URL"):
            if new_url and new_url not in channels[selected_channel]["urls"]:
                channels[selected_channel]["urls"].append(new_url)
                save_channels(channels)
                st.rerun()

        st.subheader("URLs actuales")
        for i, url in enumerate(channels[selected_channel]["urls"]):
            cols = st.columns([0.8, 0.2])
            cols[0].write(url)
            if cols[1].button("Eliminar", key=f"del_{i}"):
                channels[selected_channel]["urls"].pop(i)
                save_channels(channels)
                st.rerun()

    with tab3:
        st.header("Librería de Clips")
        uploaded_files = st.file_uploader("Subir clips de video (MP4)", accept_multiple_files=True, type=['mp4'])
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with open(os.path.join("assets/clips", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"{len(uploaded_files)} archivos subidos con éxito.")

        st.subheader("Clips en la nube (assets/clips)")
        clips = [f for f in os.listdir("assets/clips") if f.endswith('.mp4')]
        for clip in clips:
            st.write(f"✅ {clip}")

else:
    st.info("Crea o selecciona un canal en la barra lateral para empezar.")
