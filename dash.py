import streamlit as st
import pytube
from pytube import YouTube
import os
import base64
import tempfile
import subprocess
import time
import random
import math
import json
import re

# --- Configuration de la page ---
st.set_page_config(
    page_title="CYBER-STREAM Terminal",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialisation de l'état de session ---
session_defaults = {
    'title_typed': False,
    'hack_mode': False,
    'search_results': None,
    'selected_video_url': None,
    'selected_video_data': None,
    'current_page': 1,
    'total_pages': 0,
    'download_in_progress': False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Fonction pour charger le CSS ---
def load_css(theme_name):
    if theme_name == "Cyberpunk":
        cyberpunk_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            .stApp { background: #0a0a0a; color: #e0e0e0; font-family: 'Orbitron', sans-serif; overflow-x: hidden; }
            body::before { content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(45deg, #0f0c29, #302b63, #24243e, #0f0c29); background-size: 400% 400%; animation: gradientShift 15s ease infinite; z-index: -2; }
            @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
            body::after { content: ""; position: fixed; top:0; left:0; width:100%; height:100%; background: url('https://www.transparenttextures.com/patterns/noise.png'); opacity: 0.03; z-index: -1; pointer-events: none; }
            .css-1d391kg, .css-17eq0hr { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-right: 1px solid rgba(0, 255, 255, 0.3); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); }
            .stTextInput > div > div > input, .stSelectbox > div > div > select { background: rgba(255, 255, 255, 0.08); color: #00ffff; border: 1px solid rgba(0, 255, 255, 0.5); font-family: 'Orbitron', sans-serif; transition: all 0.3s ease; }
            .stTextInput > div > div > input:focus { border-color: #00ffff; box-shadow: 0 0 15px #00ffff, inset 0 0 5px rgba(0, 255, 255, 0.5); }
            .stButton > button { background: linear-gradient(45deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.2)); border: 1px solid #00ffff; color: #00ffff; font-weight: bold; font-family: 'Orbitron', sans-serif; position: relative; z-index: 1; transition: all 0.3s ease; overflow: hidden; }
            .stButton > button::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.4), transparent); transition: left 0.5s; }
            .stButton > button:hover::before { left: 100%; }
            .stButton > button:hover { background: rgba(0, 255, 255, 0.2); box-shadow: 0 0 20px #00ffff, inset 0 0 10px rgba(0, 255, 255, 0.5); transform: translateY(-2px); }
            .stButton > button:disabled { background: rgba(50, 50, 50, 0.2); border-color: #555; color: #666; cursor: not-allowed; box-shadow: none; transform: none; }
            .glitch { font-size: 4.5rem; font-weight: 900; text-transform: uppercase; position: relative; color: #00ffff; font-family: 'Orbitron', sans-serif; letter-spacing: 5px; text-shadow: 0 0 10px #00ffff; }
            .glitch::before, .glitch::after { content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
            .glitch::before { animation: glitch-1 0.5s infinite; color: #ff00ff; z-index: -1; }
            .glitch::after { animation: glitch-2 0.5s infinite; color: #00ff00; z-index: -2; }
            @keyframes glitch-1 { 0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); } 20% { clip-path: inset(20% 0 30% 0); transform: translate(-2px, 2px); } 40% { clip-path: inset(50% 0 20% 0); transform: translate(2px, -2px); } 60% { clip-path: inset(10% 0 60% 0); transform: translate(-2px, 1px); } 80% { clip-path: inset(80% 0 5% 0); transform: translate(1px, -1px); } }
            @keyframes glitch-2 { 0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); } 20% { clip-path: inset(60% 0 10% 0); transform: translate(2px, -1px); } 40% { clip-path: inset(20% 0 50% 0); transform: translate(-2px, 2px); } 60% { clip-path: inset(30% 0 40% 0); transform: translate(1px, -2px); } 80% { clip-path: inset(5% 0 80% 0); transform: translate(-1px, 1px); } }
            .metadata-card, .search-result-card { background: rgba(255, 255, 255, 0.07); backdrop-filter: blur(8px); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 15px; padding: 20px; transition: all 0.4s cubic-bezier(0.075, 0.82, 0.165, 1); position: relative; overflow: hidden; }
            .search-result-card { padding: 15px; }
            .metadata-card::before, .search-result-card::before { content: ''; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px; background: linear-gradient(45deg, #00ffff, #ff00ff, #00ff00, #00ffff); border-radius: 15px; z-index: -1; opacity: 0; transition: opacity 0.4s ease; background-size: 400% 400%; animation: gradientShift 10s ease infinite; }
            .metadata-card:hover::before, .search-result-card:hover::before { opacity: 0.7; }
            .metadata-card:hover, .search-result-card:hover { transform: translateY(-5px) scale(1.02); box-shadow: 0 10px 40px rgba(0, 255, 255, 0.3); background: rgba(255, 255, 255, 0.1); }
            .metadata-card img, .search-result-card img { border-radius: 10px; border: 1px solid rgba(0, 255, 255, 0.5); }
            .metadata-card-text h3, .search-result-card-text h4 { color: #ffffff; text-shadow: 0 0 5px #00ffff; }
            .metadata-card-text p, .search-result-card-text p { color: #b0b0b0; }
            .pagination-container { display: flex; justify-content: center; align-items: center; gap: 20px; padding: 20px; }
            .pagination-info { color: #00ffff; font-family: 'Orbitron', sans-serif; font-size: 1.1em; }
            .custom-spinner { display: flex; justify-content: center; align-items: center; padding: 20px; }
            .custom-spinner div { width: 15px; height: 15px; margin: 0 5px; background: #00ffff; border-radius: 50%; animation: pulse 1.4s infinite ease-in-out both; }
            .custom-spinner div:nth-child(1) { animation-delay: -0.32s; }
            .custom-spinner div:nth-child(2) { animation-delay: -0.16s; }
            @keyframes pulse { 0%, 80%, 100% { transform: scale(0); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }
            iframe { border: 1px solid rgba(0, 255, 255, 0.5); box-shadow: 0 0 30px rgba(0, 255, 255, 0.4); border-radius: 10px; }
            .status-info { background: rgba(0, 255, 255, 0.1); border: 1px solid #00ffff; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .status-success { background: rgba(0, 255, 0, 0.1); border: 1px solid #00ff00; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .status-error { background: rgba(255, 0, 0, 0.1); border: 1px solid #ff0000; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .download-progress { width: 100%; background: rgba(255, 255, 255, 0.1); border-radius: 10px; margin: 10px 0; }
            .download-progress-bar { height: 10px; background: linear-gradient(90deg, #00ffff, #ff00ff); border-radius: 10px; transition: width 0.3s ease; }
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)
    elif theme_name == "Clair":
        light_css = """ <style> .stApp { background-color: #ffffff; color: #000000; } .typing-title, .glitch { font-size: 3rem; font-weight: bold; color: #1f77b4; } </style> """
        st.markdown(light_css, unsafe_allow_html=True)

# --- Fonctions Utilitaires ---

def validate_youtube_url(url):
    """Valide l'URL YouTube"""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

def get_video_id(url):
    """Extrait l'ID de la vidéo YouTube"""
    if not url:
        return None
    if "youtu.be/" in url: 
        return url.split("youtu.be/")[1].split("?")[0]
    if "watch?v=" in url: 
        return url.split("watch?v=")[1].split("&")[0]
    if "embed/" in url:
        return url.split("embed/")[1].split("?")[0]
    return None

def display_custom_status(message, status_type="info"):
    """Affiche un message de statut stylisé"""
    st.markdown(f'<div class="status-{status_type}">{message}</div>', unsafe_allow_html=True)

def get_nested_data(data, primary_key, secondary_key, default):
    """Récupère les données imbriquées de manière sécurisée"""
    if not data:
        return default
    primary_data = data.get(primary_key)
    if isinstance(primary_data, dict): 
        return primary_data.get(secondary_key, default)
    elif primary_data: 
        return primary_data
    else: 
        return default

def format_duration(seconds):
    """Formate la durée en secondes vers un format lisible"""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except:
        return "N/A"

def display_metadata(video_data):
    """Affiche les métadonnées de la vidéo"""
    col1, col2 = st.columns([1, 3])
    with col1:
        thumbnail_list = video_data.get('thumbnail', [])
        if thumbnail_list: 
            st.image(thumbnail_list[0]['url'], width=200)
    with col2:
        title = video_data.get('title', 'Titre non disponible')
        channel_name = get_nested_data(video_data, 'channel', 'name', 'Chaîne inconnue')
        view_text = get_nested_data(video_data, 'viewCount', 'text', 'N/A vues')
        duration_text = get_nested_data(video_data, 'duration', 'text', 'N/A')
        st.markdown(f"<div class='metadata-card-text'><h3>{title}</h3><p>Chaîne : {channel_name}</p><p>Vues : {view_text} | Durée : {duration_text}</p></div>", unsafe_allow_html=True)

# --- FONCTION DE RECHERCHE AVEC YT-DLP ET CACHE ---
@st.cache_data(ttl=3600, show_spinner="Recherche sur YouTube... Veuillez patienter.")
def search_youtube(query, limit=30):
    """
    Recherche des vidéos sur YouTube en utilisant yt-dlp.
    Les résultats sont mis en cache pendant une heure pour accélérer les recherches répétées.
    """
    try:
        search_command = [
            'yt-dlp',
            f'ytsearch{limit}:{query}',
            '--dump-json',
            '--no-download',
            '--no-warnings'
        ]
        
        result = subprocess.run(search_command, capture_output=True, text=True, check=True, timeout=30)
        
        videos = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    video_data = json.loads(line)
                    # Formater la durée si elle est en secondes
                    duration = video_data.get('duration')
                    duration_text = format_duration(duration) if duration else 'N/A'
                    
                    videos.append({
                        'id': video_data.get('id'),
                        'title': video_data.get('title'),
                        'link': video_data.get('webpage_url'),
                        'channel': {'name': video_data.get('uploader')},
                        'duration': {'text': duration_text},
                        'viewCount': {'text': f"{video_data.get('view_count', 0):,}"},
                        'thumbnail': [{'url': video_data.get('thumbnail')}]
                    })
                except json.JSONDecodeError:
                    continue
        return videos
    except subprocess.TimeoutExpired:
        st.error("La recherche a pris trop de temps. Veuillez réessayer.")
        return []
    except subprocess.CalledProcessError as e:
        st.error(f"Erreur lors de la recherche avec yt-dlp : {e.stderr}")
        return []
    except Exception as e:
        st.error(f"Une erreur inattendue est survenue lors de la recherche : {e}")
        return []

# --- FONCTION DE TÉLÉCHARGEMENT AVEC YT-DLP ---
def download_media(url, format_choice):
    """Télécharge le média avec yt-dlp avec gestion de progression"""
    if st.session_state.download_in_progress:
        display_custom_status("Un téléchargement est déjà en cours.", "error")
        return None, None, None
        
    st.session_state.download_in_progress = True
    
    try:
        spinner_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        spinner_placeholder.markdown('<div class="custom-spinner"><div></div><div></div><div></div></div>', unsafe_allow_html=True)
        status_placeholder.markdown('<div class="status-info">CONNEXION AU SERVEUR YOUTUBE...</div>', unsafe_allow_html=True)
        
        temp_dir = tempfile.mkdtemp()
        
        if format_choice == "MP4 (Vidéo)":
            output_path = os.path.join(temp_dir, "video.%(ext)s")
            command = [
                'yt-dlp', 
                '-f', 'best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '-o', output_path, 
                url
            ]
        elif format_choice == "MP3 (Audio)":
            output_path = os.path.join(temp_dir, "audio.%(ext)s")
            command = [
                'yt-dlp',
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', output_path,
                url
            ]
        
        status_placeholder.markdown('<div class="status-info">TÉLÉCHARGEMENT EN COURS...</div>', unsafe_allow_html=True)
        
        # Exécution du téléchargement
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        
        progress_bar.progress(100)
        status_placeholder.markdown('<div class="status-success">TÉLÉCHARGEMENT TERMINÉ!</div>', unsafe_allow_html=True)
        spinner_placeholder.empty()
        
        # Recherche du fichier téléchargé
        downloaded_file = None
        for file in os.listdir(temp_dir):
            if file.startswith("video.") or file.startswith("audio."):
                downloaded_file = os.path.join(temp_dir, file)
                break
        
        if downloaded_file:
            mime_type = "video/mp4" if format_choice == "MP4 (Vidéo)" else "audio/mpeg"
            return downloaded_file, os.path.basename(downloaded_file), mime_type
        else:
            raise Exception("Fichier téléchargé non trouvé.")
            
    except subprocess.CalledProcessError as e:
        display_custom_status(f"ERREUR YT-DLP : {e.stderr}", "error")
        return None, None, None
    except Exception as e:
        display_custom_status(f"ERREUR DE TÉLÉCHARGEMENT : {e}", "error")
        return None, None, None
    finally:
        st.session_state.download_in_progress = False
        progress_bar.empty()
        status_placeholder.empty()

def render_pagination():
    """Affiche la pagination"""
    if st.session_state.total_pages <= 1:
        return
        
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Précédent", disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page -= 1
            st.rerun()
    with col_info:
        st.markdown(f"<div class='pagination-info'>Page {st.session_state.current_page} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("Suivant ➡️", disabled=(st.session_state.current_page == st.session_state.total_pages)):
            st.session_state.current_page += 1
            st.rerun()

# --- Interface Utilisateur ---

theme = st.sidebar.selectbox("🎨 Choisir un Thème", ["Cyberpunk", "Clair"])
load_css(theme)

if not st.session_state.title_typed:
    st.markdown('<h1 class="typing-title">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.title_typed = True
    st.rerun()
else:
    st.markdown('<h1 class="glitch" data-text="CYBER-STREAM TERMINAL">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)

st.sidebar.title("🎛️ Panneau de Contrôle")
search_query = st.sidebar.text_input("🔍 Rechercher des vidéos :", key="search_input")
download_format = st.sidebar.selectbox("Format de Téléchargement", ["MP4 (Vidéo)", "MP3 (Audio)"])

# Section pour URL directe
st.sidebar.markdown("---")
direct_url = st.sidebar.text_input("🌐 Ou coller une URL YouTube directe:")

if direct_url and validate_youtube_url(direct_url):
    try:
        yt = YouTube(direct_url)
        video_data = {
            'id': get_video_id(direct_url),
            'title': yt.title,
            'link': direct_url,
            'channel': {'name': yt.author},
            'duration': {'text': format_duration(yt.length)},
            'viewCount': {'text': f"{yt.views:,}"},
            'thumbnail': [{'url': yt.thumbnail_url}]
        }
        st.session_state.selected_video_url = direct_url
        st.session_state.selected_video_data = video_data
        st.sidebar.success("Vidéo chargée avec succès!")
    except Exception as e:
        st.sidebar.error(f"Erreur lors du chargement de la vidéo: {e}")

if st.sidebar.button("Lancer la recherche") and search_query:
    if search_query.strip():
        with st.spinner("Recherche en cours..."):
            results = search_youtube(search_query, limit=30)
            st.session_state.search_results = results
            st.session_state.total_pages = max(1, math.ceil(len(results) / 3))
            st.session_state.current_page = 1
            st.session_state.selected_video_url = None
            st.session_state.selected_video_data = None
            
        if not results:
            st.sidebar.warning("Aucun résultat trouvé. Essayez avec d'autres termes.")
    else:
        st.sidebar.warning("Veuillez entrer un terme de recherche.")

if st.sidebar.button("🚨 ACTIVER HACK MODE 🚨"):
    st.session_state.hack_mode = not st.session_state.hack_mode

if st.session_state.hack_mode:
    st.markdown("""<div style='position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9999; overflow:hidden;'><style>.matrix-rain { color: #0F0; font-size: 1.2em; position: absolute; animation: rain 1s linear infinite; }@keyframes rain { to { transform: translateY(100vh); } }</style><script>const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}';const matrixContainer = document.currentScript.parentElement;for(let i = 0; i < 50; i++) {const span = document.createElement('span');span.classList.add('matrix-rain');span.style.left = Math.random() * 100 + '%';span.style.animationDuration = Math.random() * 2 + 1 + 's';span.style.animationDelay = Math.random() * 2 + 's';span.innerText = chars.charAt(Math.floor(Math.random() * chars.length));matrixContainer.appendChild(span);}setTimeout(() => matrixContainer.remove(), 3000);</script></div>""", unsafe_allow_html=True)
    st.session_state.hack_mode = False

# Affichage des résultats de recherche
if st.session_state.search_results:
    st.subheader("📺 Résultats de la recherche")
    results_per_page = 3
    start_index = (st.session_state.current_page - 1) * results_per_page
    end_index = start_index + results_per_page
    page_results = st.session_state.search_results[start_index:end_index]
    
    if not page_results:
        st.info("Aucun résultat à afficher pour cette page.")
    else:
        for video in page_results:
            if video.get('link') and video.get('title'):
                with st.container():
                    col_img, col_info, col_button = st.columns([1, 3, 1])
                    with col_img:
                        thumbnail_list = video.get('thumbnail', [])
                        if thumbnail_list: 
                            st.image(thumbnail_list[0]['url'], width=120, use_column_width=True)
                    with col_info:
                        title = video.get('title', 'Titre non disponible')
                        channel_name = get_nested_data(video, 'channel', 'name', 'Chaîne inconnue')
                        view_text = get_nested_data(video, 'viewCount', 'text', 'N/A vues')
                        duration_text = get_nested_data(video, 'duration', 'text', 'N/A')
                        st.markdown(f"**{title}**")
                        st.caption(f"👤 {channel_name} | 👁️ {view_text} | ⏱️ {duration_text}")
                    with col_button:
                        if st.button("Sélectionner", key=f"select_{video['id']}"):
                            st.session_state.selected_video_url = video['link']
                            st.session_state.selected_video_data = video
                            st.rerun()
                st.markdown("---")
        render_pagination()

# Affichage de la vidéo sélectionnée
if st.session_state.selected_video_url and st.session_state.selected_video_data:
    st.subheader("🎬 Lecteur Vidéo")
    display_metadata(st.session_state.selected_video_data)
    
    video_id = get_video_id(st.session_state.selected_video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.components.v1.iframe(embed_url, height=400)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬇️ Télécharger la vidéo", use_container_width=True):
                if not st.session_state.download_in_progress:
                    file_path, file_name, mime_type = download_media(
                        st.session_state.selected_video_url, 
                        download_format
                    )
                    if file_path:
                        try:
                            with open(file_path, "rb") as f:
                                bytes_data = f.read()
                            
                            st.download_button(
                                label=f"💾 Télécharger {file_name}",
                                data=bytes_data,
                                file_name=file_name,
                                mime=mime_type,
                                use_container_width=True
                            )
                        finally:
                            # Nettoyage du fichier temporaire
                            try:
                                os.unlink(file_path)
                                os.rmdir(os.path.dirname(file_path))
                            except:
                                pass
        with col2:
            if st.button("🗑️ Effacer la sélection", use_container_width=True):
                st.session_state.selected_video_url = None
                st.session_state.selected_video_data = None
                st.rerun()
    else:
        display_custom_status("ERREUR : Impossible de lire l'URL de la vidéo sélectionnée.", "error")

elif not st.session_state.search_results and not st.session_state.selected_video_url:
    st.info("🔍 Veuillez lancer une recherche ou coller une URL YouTube pour commencer.")

# Pied de page
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    <p>CYBER-STREAM TERMINAL v2.0</p>
    <p>Utilise yt-dlp pour le téléchargement</p>
</div>
""", unsafe_allow_html=True)
