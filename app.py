import streamlit as st
import os
import json
from news_processor import NewsProcessor
from audio_generator import AudioGenerator
from video_editor import VideoEditor
from youtube_uploader import YouTubeUploader
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AutoVideo Studio v2", layout="wide", page_icon="🚀")

# Inicializar componentes de forma segura
openrouter_key = os.getenv("OPENROUTER_API_KEY")
eleven_key = os.getenv("ELEVENLABS_API_KEY")

if 'news_processor' not in st.session_state:
    st.session_state.news_processor = NewsProcessor(openrouter_key) if openrouter_key else None
if 'audio_generator' not in st.session_state:
    st.session_state.audio_generator = AudioGenerator(eleven_key) if eleven_key else None
if 'video_editor' not in st.session_state:
    st.session_state.video_editor = VideoEditor()
if 'uploader' not in st.session_state:
    st.session_state.uploader = YouTubeUploader()

def load_channels():
    if os.path.exists("data/channels.json"):
        with open("data/channels.json", "r") as f:
            return json.load(f)
    return {}

def save_channels(channels):
    with open("data/channels.json", "w") as f:
        json.dump(channels, f, indent=4)

channels = load_channels()

# Sidebar
st.sidebar.title("🎮 Panel de Control")
menu = st.sidebar.radio("Ir a", ["📊 Dashboard", "🎬 Productor de Video", "⚙️ Configuración de Canales"])

if menu == "📊 Dashboard":
    st.title("📊 Estadísticas de Canales")

    if not channels:
        st.info("No tienes canales configurados. Ve a la pestaña de Configuración.")
    else:
        cols = st.columns(len(channels) if len(channels) < 4 else 3)
        for i, (name, config) in enumerate(channels.items()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.subheader(name)
                    st.caption(f"Nicho: {config['niche']}")

                    # Intentar obtener stats reales de YT
                    stats = st.session_state.uploader.get_channel_stats(name)
                    if stats:
                        col_a, col_b = st.columns(2)
                        col_a.metric("Subscriptores", stats['subscribers'])
                        col_b.metric("Videos", stats['videos'])
                        st.write(f"Vistas totales: {stats['views']}")
                    else:
                        st.warning("Stats de YouTube no disponibles (Vincula tu cuenta)")

                    st.write(f"Fuentes: {len(config['urls'])}")

elif menu == "🎬 Productor de Video":
    st.title("🎬 Productor de Contenido")
    selected_channel = st.selectbox("Seleccionar Canal", list(channels.keys()))

    if selected_channel:
        tab1, tab2 = st.tabs(["🚀 Generación", "📰 Fuentes"])

        with tab1:
            st.header(f"Producción para {selected_channel}")
            if not channels[selected_channel]["urls"]:
                st.warning("Añade URLs primero.")
            else:
                url = st.selectbox("Noticia", channels[selected_channel]["urls"])
                if st.button("🚀 Iniciar Proceso Automático"):
                    with st.status("Generando video...", expanded=True) as status:
                        content = st.session_state.news_processor.fetch_news_content(url)
                        status.write("Guionando...")
                        script = st.session_state.news_processor.generate_script(content, channels[selected_channel]["niche"], channels[selected_channel]["prompt"])
                        status.write("Audio...")
                        audio_path = st.session_state.audio_generator.generate_audio(script, voice_id=channels[selected_channel].get("voice_id"))
                        status.write("Video...")
                        video_path = f"temp/{selected_channel}_video.mp4"
                        st.session_state.video_editor.create_video(audio_path, video_path, script)
                        status.update(label="¡Listo!", state="complete")
                    st.video(video_path)

        with tab2:
            new_url = st.text_input("Nueva URL")
            if st.button("Agregar"):
                channels[selected_channel]["urls"].append(new_url)
                save_channels(channels)
                st.rerun()
            for i, url in enumerate(channels[selected_channel]["urls"]):
                st.write(f"{i+1}. {url}")

elif menu == "⚙️ Configuración de Canales":
    st.title("⚙️ Gestión de Canales")

    with st.expander("➕ Crear Nuevo Canal", expanded=not channels):
        with st.form("new_channel"):
            name = st.text_input("Nombre único del canal")
            niche = st.text_input("Nicho")
            prompt = st.text_area("Prompt de estilo")
            voice = st.text_input("Voice ID", value="pNInz6obpg8n9Y4avHCy")
            if st.form_submit_button("Crear"):
                channels[name] = {"niche": niche, "prompt": prompt, "voice_id": voice, "urls": []}
                save_channels(channels)
                st.rerun()

    st.subheader("Canales existentes")
    for name in list(channels.keys()):
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"**{name}** - {channels[name]['niche']}")
            if col2.button("🗑️ Borrar", key=f"del_{name}"):
                del channels[name]
                save_channels(channels)
                st.rerun()
