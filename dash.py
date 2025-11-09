import streamlit as st
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

# --- Fonctions utilitaires avec yt-dlp uniquement ---

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
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&=%\?]{11})',
        r'^([^&=%\?]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(url):
    """
    Récupère les informations d'une vidéo YouTube avec yt-dlp
    """
    try:
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
        video_data = json.loads(result.stdout)
        
        # Formater les données pour notre application
        duration = video_data.get('duration')
        duration_text = format_duration(duration) if duration else 'N/A'
        
        return {
            'id': video_data.get('id'),
            'title': video_data.get('title', 'Titre non disponible'),
            'link': url,
            'channel': {'name': video_data.get('uploader', 'Chaîne inconnue')},
            'duration': {'text': duration_text},
            'viewCount': {'text': f"{video_data.get('view_count', 0):,}"},
            'thumbnail': [{'url': video_data.get('thumbnail')}]
        }
    except subprocess.CalledProcessError as e:
        st.error(f"Erreur yt-dlp : {e.stderr}")
        return None
    except json.JSONDecodeError:
        st.error("Erreur lors du décodage des données de la vidéo.")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
        return None

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

# --- FONCTION DE RECHERCHE AVEC YT-DLP ---
@st.cache_data(ttl=3600, show_spinner="Recherche sur YouTube... Veuillez patienter.")
def search_youtube(query, limit=20):
    """
    Recherche des vidéos sur YouTube en utilisant yt-dlp
    """
    try:
        search_command = [
            'yt-dlp',
            f'ytsearch{limit}:{query}',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--quiet'
        ]
        
        result = subprocess.run(search_command, capture_output=True, text=True, check=True, timeout=60)
        videos = []
        
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    video_data = json.loads(line)
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
        
    except subprocess.CalledProcessError as e:
        st.error(f"Erreur lors de la recherche avec yt-dlp : {e.stderr}")
        # Fallback: résultats de démonstration
        return get_demo_results(query)
    except subprocess.TimeoutExpired:
        st.error("La recherche a pris trop de temps. Veuillez réessayer.")
        return get_demo_results(query)
    except Exception as e:
        st.error(f"Une erreur inattendue est survenue lors de la recherche : {e}")
        return get_demo_results(query)

def get_demo_results(query):
    """Retourne des résultats de démonstration pour tester l'interface"""
    demo_videos = [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'Résultat de démonstration pour "{query}" - Exemple 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Démo'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1,234,567'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}]
        },
        {
            'id': 'kJQP7kiw5Fk',
            'title': f'Résultat de démonstration pour "{query}" - Exemple 2', 
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Test'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987,654'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}]
        },
        {
            'id': '9bZkp7q19f0',
            'title': f'Résultat de démonstration pour "{query}" - Exemple 3',
            'link': 'https://www.youtube.com/watch?v=9bZkp7q19f0', 
            'channel': {'name': 'Chaîne Exemple'},
            'duration': {'text': '4:12'},
            'viewCount': {'text': '2,345,678'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg'}]
        }
    ]
    return demo_videos

# --- FONCTION DE TÉLÉCHARGEMENT AVEC YT-DLP ---
def download_media(url, format_choice):
    """Télécharge le média avec yt-dlp"""
    if st.session_state.download_in_progress:
        st.error("Un téléchargement est déjà en cours.")
        return None, None, None
        
    st.session_state.download_in_progress = True
    
    try:
        temp_dir = tempfile.mkdtemp()
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        status_placeholder.info("🔄 Connexion au serveur YouTube...")
        
        if format_choice == "MP4 (Vidéo)":
            output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")
            command = [
                'yt-dlp', 
                '-f', 'best[height<=720][ext=mp4]/best[height<=720]',
                '--merge-output-format', 'mp4',
                '-o', output_path, 
                url
            ]
        elif format_choice == "MP3 (Audio)":
            output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")
            command = [
                'yt-dlp',
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', output_path,
                url
            ]
        
        status_placeholder.info("📥 Téléchargement en cours...")
        
        # Exécution du téléchargement
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        
        status_placeholder.success("✅ Téléchargement terminé!")
        
        # Recherche du fichier téléchargé
        downloaded_file = None
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mp3')):
                downloaded_file = os.path.join(temp_dir, file)
                break
        
        if downloaded_file:
            mime_type = "video/mp4" if format_choice == "MP4 (Vidéo)" else "audio/mpeg"
            return downloaded_file, os.path.basename(downloaded_file), mime_type
        else:
            raise Exception("Fichier téléchargé non trouvé.")
            
    except subprocess.CalledProcessError as e:
        st.error(f"Erreur lors du téléchargement : {e.stderr}")
        return None, None, None
    except Exception as e:
        st.error(f"Erreur de téléchargement : {e}")
        return None, None, None
    finally:
        st.session_state.download_in_progress = False
        progress_placeholder.empty()
        status_placeholder.empty()

# --- Interface Utilisateur (identique à avant mais sans pytube) ---

def load_css(theme_name):
    # Garder le même CSS que précédemment
    if theme_name == "Cyberpunk":
        cyberpunk_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            .stApp { background: #0a0a0a; color: #e0e0e0; font-family: 'Orbitron', sans-serif; overflow-x: hidden; }
            body::before { content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(45deg, #0f0c29, #302b63, #24243e, #0f0c29); background-size: 400% 400%; animation: gradientShift 15s ease infinite; z-index: -2; }
            @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
            .stButton > button { background: linear-gradient(45deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.2)); border: 1px solid #00ffff; color: #00ffff; font-weight: bold; font-family: 'Orbitron', sans-serif; }
            .stButton > button:hover { background: rgba(0, 255, 255, 0.2); box-shadow: 0 0 20px #00ffff; }
            .glitch { font-size: 4.5rem; font-weight: 900; text-transform: uppercase; position: relative; color: #00ffff; font-family: 'Orbitron', sans-serif; letter-spacing: 5px; text-shadow: 0 0 10px #00ffff; }
            .metadata-card { background: rgba(255, 255, 255, 0.07); backdrop-filter: blur(8px); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 15px; padding: 20px; }
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)

def display_metadata(video_data):
    """Affiche les métadonnées de la vidéo"""
    col1, col2 = st.columns([1, 3])
    with col1:
        thumbnail_list = video_data.get('thumbnail', [])
        if thumbnail_list: 
            st.image(thumbnail_list[0]['url'], width=200)
    with col2:
        title = video_data.get('title', 'Titre non disponible')
        channel_name = video_data.get('channel', {}).get('name', 'Chaîne inconnue')
        view_text = video_data.get('viewCount', {}).get('text', 'N/A vues')
        duration_text = video_data.get('duration', {}).get('text', 'N/A')
        st.markdown(f"<div class='metadata-card'><h3>{title}</h3><p>Chaîne : {channel_name}</p><p>Vues : {view_text} | Durée : {duration_text}</p></div>", unsafe_allow_html=True)

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
        st.markdown(f"<div style='color: #00ffff; text-align: center;'>Page {st.session_state.current_page} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("Suivant ➡️", disabled=(st.session_state.current_page == st.session_state.total_pages)):
            st.session_state.current_page += 1
            st.rerun()

# --- APPLICATION PRINCIPALE ---

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
    with st.spinner("Chargement des informations de la vidéo..."):
        video_data = get_video_info(direct_url)
        if video_data:
            st.session_state.selected_video_url = direct_url
            st.session_state.selected_video_data = video_data
            st.sidebar.success("✅ Vidéo chargée avec succès!")
        else:
            st.sidebar.error("❌ Erreur lors du chargement de la vidéo")

if st.sidebar.button("🚀 Lancer la recherche") and search_query:
    if search_query.strip():
        with st.spinner("🔍 Recherche en cours..."):
            results = search_youtube(search_query, limit=20)
            st.session_state.search_results = results
            st.session_state.total_pages = max(1, math.ceil(len(results) / 3))
            st.session_state.current_page = 1
            st.session_state.selected_video_url = None
            st.session_state.selected_video_data = None
            
        if not results:
            st.sidebar.warning("⚠️ Aucun résultat trouvé. Essayez avec d'autres termes.")
    else:
        st.sidebar.warning("⚠️ Veuillez entrer un terme de recherche.")

# Affichage des résultats
if st.session_state.search_results:
    st.subheader("📺 Résultats de la recherche")
    results_per_page = 3
    start_index = (st.session_state.current_page - 1) * results_per_page
    end_index = start_index + results_per_page
    page_results = st.session_state.search_results[start_index:end_index]
    
    for video in page_results:
        if video.get('link') and video.get('title'):
            with st.container():
                col_img, col_info, col_button = st.columns([1, 3, 1])
                with col_img:
                    thumbnail_list = video.get('thumbnail', [])
                    if thumbnail_list: 
                        st.image(thumbnail_list[0]['url'], width=120)
                with col_info:
                    title = video.get('title', 'Titre non disponible')
                    channel_name = video.get('channel', {}).get('name', 'Chaîne inconnue')
                    view_text = video.get('viewCount', {}).get('text', 'N/A vues')
                    duration_text = video.get('duration', {}).get('text', 'N/A')
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
                            # Nettoyage
                            try:
                                if os.path.exists(file_path):
                                    os.unlink(file_path)
                                if os.path.exists(os.path.dirname(file_path)):
                                    os.rmdir(os.path.dirname(file_path))
                            except:
                                pass
        with col2:
            if st.button("🗑️ Effacer la sélection", use_container_width=True):
                st.session_state.selected_video_url = None
                st.session_state.selected_video_data = None
                st.rerun()

elif not st.session_state.search_results and not st.session_state.selected_video_url:
    st.info("🔍 Veuillez lancer une recherche ou coller une URL YouTube pour commencer.")

# Vérification des dépendances
st.sidebar.markdown("---")
if st.sidebar.button("🔧 Vérifier les dépendances"):
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            st.sidebar.success(f"✅ yt-dlp installé (version: {result.stdout.strip()})")
        else:
            st.sidebar.error("❌ yt-dlp non trouvé")
    except:
        st.sidebar.error("❌ yt-dlp non installé")
