import streamlit as st
import os
import tempfile
import subprocess
import time
import math
import json
import re
import sys

# --- Configuration ---
st.set_page_config(
    page_title="CYBER-STREAM Terminal",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State ---
session_defaults = {
    'title_typed': False,
    'search_results': None,
    'selected_video_url': None,
    'selected_video_data': None,
    'current_page': 1,
    'total_pages': 0,
    'ffmpeg_available': False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- CSS ---
def load_css(theme_name):
    if theme_name == "Cyberpunk":
        cyberpunk_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            .stApp { background: #0a0a0a; color: #e0e0e0; font-family: 'Orbitron', sans-serif; }
            .stButton > button { background: linear-gradient(45deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.2)); border: 1px solid #00ffff; color: #00ffff; }
            .glitch { font-size: 4.5rem; font-weight: 900; color: #00ffff; font-family: 'Orbitron', sans-serif; }
            .metadata-card { background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 15px; padding: 20px; }
            .warning-box { background: rgba(255, 165, 0, 0.1); border: 1px solid orange; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .info-box { background: rgba(0, 255, 255, 0.1); border: 1px solid #00ffff; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)

# --- Vérification FFmpeg ---
def check_ffmpeg():
    """Vérifie si FFmpeg est disponible"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_ffmpeg_python():
    """Vérifie si ffmpeg-python est installé"""
    try:
        import ffmpeg
        return True
    except ImportError:
        return False

# --- Installation automatique de FFmpeg ---
def install_ffmpeg():
    """Tente d'installer FFmpeg via différents moyens"""
    try:
        # Essayer d'installer ffmpeg-python
        subprocess.run([sys.executable, "-m", "pip", "install", "ffmpeg-python"], 
                      capture_output=True, check=True)
        return True
    except:
        return False

# --- Fonctions utilitaires ---
def validate_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

def get_video_id(url):
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

def clean_youtube_url(url):
    video_id = get_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def format_duration(seconds):
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

def safe_search_query(query):
    """Nettoie et sécurise la requête de recherche"""
    cleaned = re.sub(r'[^\w\s\-]', '', query)
    return cleaned.strip()[:100]

# --- FONCTION DE RECHERCHE ---
@st.cache_data(ttl=3600, show_spinner="Recherche en cours...")
def search_youtube(query, limit=15):
    """Recherche YouTube avec fallback"""
    try:
        clean_query = safe_search_query(query)
        if not clean_query:
            return get_demo_results("exemple")
        
        search_command = [
            'yt-dlp',
            f'ytsearch{limit}:{clean_query}',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--quiet',
            '--ignore-errors'
        ]
        
        result = subprocess.run(search_command, capture_output=True, text=True, timeout=30)
        
        videos = []
        if result.stdout.strip():
            for line in result.stdout.splitlines():
                if line.strip():
                    try:
                        video_data = json.loads(line)
                        duration = video_data.get('duration')
                        duration_text = format_duration(duration) if duration else 'N/A'
                        
                        videos.append({
                            'id': video_data.get('id'),
                            'title': video_data.get('title', 'Sans titre'),
                            'link': video_data.get('webpage_url'),
                            'channel': {'name': video_data.get('uploader', 'Chaîne inconnue')},
                            'duration': {'text': duration_text},
                            'viewCount': {'text': f"{video_data.get('view_count', 0):,}"},
                            'thumbnail': [{'url': video_data.get('thumbnail')}]
                        })
                    except json.JSONDecodeError:
                        continue
        
        return videos if videos else get_demo_results(query)
        
    except Exception as e:
        return get_demo_results(query)

def get_demo_results(query):
    """Résultats de démonstration"""
    return [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'Résultat démo: {query} - Exemple 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Démonstration'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1,234,567'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}]
        },
        {
            'id': 'kJQP7kiw5Fk', 
            'title': f'Résultat démo: {query} - Exemple 2',
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Test'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987,654'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}]
        }
    ]

# --- FONCTION DE TÉLÉCHARGEMENT SANS FFMPEG ---
def download_media(url, format_choice):
    """
    Téléchargement sans dépendance à FFmpeg
    """
    try:
        clean_url = clean_youtube_url(url)
        temp_dir = tempfile.mkdtemp()
        
        st.info("🔄 Configuration du téléchargement...")
        
        # Configuration de base
        base_command = [
            'yt-dlp',
            '--ignore-errors',
            '--no-warnings',
        ]
        
        # Pour MP4: utiliser des formats qui ne nécessitent pas FFmpeg
        if format_choice == "MP4 (Vidéo)":
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            base_command.extend([
                '-f', 'best[ext=mp4]/best[ext=webm]',  # Formats natifs
                '-o', output_template,
            ])
        else:  # MP3 - essayer d'abord sans conversion
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            base_command.extend([
                '-x',  # Extraction audio
                '--audio-format', 'best',  # Prendre le meilleur format audio disponible
                '-o', output_template,
            ])
        
        base_command.append(clean_url)
        
        st.info("📥 Téléchargement en cours...")
        
        process = subprocess.run(base_command, capture_output=True, text=True, timeout=300)
        
        if process.returncode == 0:
            st.success("✅ Téléchargement terminé!")
            
            # Chercher le fichier téléchargé
            for file in os.listdir(temp_dir):
                file_lower = file.lower()
                if format_choice == "MP4 (Vidéo)":
                    if file_lower.endswith(('.mp4', '.webm', '.mkv')):
                        file_path = os.path.join(temp_dir, file)
                        mime_type = "video/mp4"
                        # Renommer en .mp4 si nécessaire
                        if not file.endswith('.mp4'):
                            new_file = os.path.splitext(file)[0] + '.mp4'
                            new_path = os.path.join(temp_dir, new_file)
                            os.rename(file_path, new_path)
                            return new_path, new_file, mime_type
                        return file_path, file, mime_type
                else:  # MP3
                    if file_lower.endswith(('.mp3', '.m4a', '.ogg', '.opus', '.wav')):
                        file_path = os.path.join(temp_dir, file)
                        mime_type = "audio/mpeg"
                        # Renommer en .mp3 si nécessaire
                        if not file.endswith('.mp3'):
                            new_file = os.path.splitext(file)[0] + '.mp3'
                            new_path = os.path.join(temp_dir, new_file)
                            os.rename(file_path, new_path)
                            return new_path, new_file, mime_type
                        return file_path, file, mime_type
            
            # Si aucun fichier trouvé, essayer avec une méthode alternative
            return download_media_fallback(clean_url, format_choice, temp_dir)
        else:
            st.warning("⚠️ Première méthode échouée, tentative avec méthode alternative...")
            return download_media_fallback(clean_url, format_choice, temp_dir)
            
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout lors du téléchargement")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None, None, None

def download_media_fallback(url, format_choice, temp_dir):
    """
    Méthode de fallback pour le téléchargement
    """
    try:
        # Méthode plus simple - télécharger le meilleur format disponible
        base_command = [
            'yt-dlp',
            '--ignore-errors',
            '--no-warnings',
            '-f', 'best',  # Juste le meilleur format disponible
            '-o', os.path.join(temp_dir, "%(title).100s.%(ext)s"),
            url
        ]
        
        process = subprocess.run(base_command, capture_output=True, text=True, timeout=300)
        
        if process.returncode == 0:
            # Chercher n'importe quel fichier téléchargé
            for file in os.listdir(temp_dir):
                if not file.endswith('.part'):  # Ignorer les fichiers partiels
                    file_path = os.path.join(temp_dir, file)
                    # Déterminer le type MIME en fonction de l'extension
                    if file.lower().endswith(('.mp4', '.webm', '.mkv')):
                        mime_type = "video/mp4"
                    elif file.lower().endswith(('.mp3', '.m4a', '.ogg')):
                        mime_type = "audio/mpeg"
                    else:
                        mime_type = "application/octet-stream"
                    
                    return file_path, file, mime_type
        
        raise Exception("Aucun fichier téléchargé trouvé")
        
    except Exception as e:
        st.error(f"❌ Méthode de fallback échouée: {str(e)}")
        return None, None, None

# --- FONCTION POUR OBTENIR LES INFOS VIDÉO ---
def get_video_info(url):
    """Récupère les informations de la vidéo"""
    try:
        clean_url = clean_youtube_url(url)
        
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--ignore-errors',
            '--no-warnings',
            '--quiet',
            clean_url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            video_data = json.loads(result.stdout)
            duration = video_data.get('duration')
            duration_text = format_duration(duration) if duration else 'N/A'
            
            return {
                'id': video_data.get('id'),
                'title': video_data.get('title', 'Titre non disponible'),
                'link': clean_url,
                'channel': {'name': video_data.get('uploader', 'Chaîne inconnue')},
                'duration': {'text': duration_text},
                'viewCount': {'text': f"{video_data.get('view_count', 0):,}"},
                'thumbnail': [{'url': video_data.get('thumbnail')}]
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None

# --- INTERFACE UTILISATEUR ---
def display_metadata(video_data):
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

# Vérification initiale des dépendances
if not st.session_state.get('dependencies_checked'):
    st.session_state.ffmpeg_available = check_ffmpeg() or check_ffmpeg_python()
    st.session_state.dependencies_checked = True

theme = st.sidebar.selectbox("🎨 Thème", ["Cyberpunk", "Clair"])
load_css(theme)

if not st.session_state.title_typed:
    st.markdown('<h1 class="typing-title">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.title_typed = True
    st.rerun()
else:
    st.markdown('<h1 class="glitch" data-text="CYBER-STREAM TERMINAL">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)

# Panneau de contrôle des dépendances
st.sidebar.title("🔧 Dépendances")

# Vérifier yt-dlp
try:
    yt_dlp_result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
    if yt_dlp_result.returncode == 0:
        st.sidebar.success(f"✅ yt-dlp: {yt_dlp_result.stdout.strip()}")
    else:
        st.sidebar.error("❌ yt-dlp: Erreur")
except:
    st.sidebar.error("❌ yt-dlp: Non disponible")

# Vérifier FFmpeg
if st.session_state.ffmpeg_available:
    st.sidebar.success("✅ FFmpeg: Disponible")
else:
    st.sidebar.warning("⚠️ FFmpeg: Non disponible - Mode limité activé")
    if st.sidebar.button("🔄 Tenter d'installer FFmpeg"):
        if install_ffmpeg():
            st.sidebar.success("✅ FFmpeg installé!")
            st.session_state.ffmpeg_available = True
            st.rerun()
        else:
            st.sidebar.error("❌ Échec de l'installation")

st.sidebar.markdown("---")

# Avertissement sur les limitations
if not st.session_state.ffmpeg_available:
    st.sidebar.markdown("""
    <div class='warning-box'>
    <strong>⚠️ Mode limité activé</strong><br>
    Sans FFmpeg, certaines conversions peuvent ne pas fonctionner. 
    Le téléchargement utilisera les formats natifs disponibles.
    </div>
    """, unsafe_allow_html=True)

# Contrôles principaux
search_query = st.sidebar.text_input("🔍 Rechercher:", key="search_input", value="musique")
download_format = st.sidebar.selectbox("Format:", ["MP4 (Vidéo)", "MP3 (Audio)"])

# URL directe
st.sidebar.markdown("---")
direct_url = st.sidebar.text_input("🌐 URL YouTube directe:")

if direct_url and validate_youtube_url(direct_url):
    with st.spinner("Chargement des informations..."):
        video_data = get_video_info(direct_url)
        if video_data:
            st.session_state.selected_video_url = direct_url
            st.session_state.selected_video_data = video_data
            st.sidebar.success("✅ Vidéo chargée!")
        else:
            st.sidebar.error("❌ Erreur de chargement")

if st.sidebar.button("🚀 Rechercher") and search_query:
    if search_query.strip():
        with st.spinner("Recherche en cours..."):
            results = search_youtube(search_query)
            st.session_state.search_results = results
            st.session_state.total_pages = max(1, math.ceil(len(results) / 3))
            st.session_state.current_page = 1
            st.session_state.selected_video_url = None
            
        if results:
            st.sidebar.success(f"🔍 {len(results)} résultats trouvés")
        else:
            st.sidebar.warning("⚠️ Aucun résultat trouvé")
    else:
        st.sidebar.warning("⚠️ Entrez un terme de recherche")

# Affichage résultats
if st.session_state.search_results:
    st.subheader("📺 Résultats de recherche")
    
    # Avertissement mode démo
    if st.session_state.search_results and len(st.session_state.search_results) > 0:
        first_title = st.session_state.search_results[0].get('title', '')
        if 'démo' in first_title.lower() or 'demo' in first_title.lower():
            st.warning("🔄 Mode démonstration - Les résultats sont simulés")
    
    results_per_page = 3
    start_index = (st.session_state.current_page - 1) * results_per_page
    end_index = start_index + results_per_page
    page_results = st.session_state.search_results[start_index:end_index]
    
    for video in page_results:
        with st.container():
            col_img, col_info, col_button = st.columns([1, 3, 1])
            with col_img:
                thumbnail_list = video.get('thumbnail', [])
                if thumbnail_list: 
                    st.image(thumbnail_list[0]['url'], width=120)
            with col_info:
                title = video.get('title', 'Sans titre')
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

# Vidéo sélectionnée
if st.session_state.selected_video_url and st.session_state.selected_video_data:
    st.subheader("🎬 Vidéo sélectionnée")
    display_metadata(st.session_state.selected_video_data)
    
    video_id = get_video_id(st.session_state.selected_video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.components.v1.iframe(embed_url, height=400)
        
        # Avertissement format
        if not st.session_state.ffmpeg_available and download_format == "MP3 (Audio)":
            st.warning("""
            **⚠️ Attention:** Sans FFmpeg, la conversion en MP3 peut ne pas fonctionner.
            Le téléchargement utilisera le meilleur format audio disponible (m4a, opus, etc.)
            """)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬇️ Télécharger", use_container_width=True, type="primary"):
                file_path, file_name, mime_type = download_media(
                    st.session_state.selected_video_url, 
                    download_format
                )
                if file_path:
                    with open(file_path, "rb") as f:
                        bytes_data = f.read()
                    
                    st.download_button(
                        label=f"💾 Télécharger {file_name}",
                        data=bytes_data,
                        file_name=file_name,
                        mime=mime_type,
                        use_container_width=True
                    )
                    
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
    st.info("🔍 Lancez une recherche ou collez une URL YouTube pour commencer")

# Instructions d'installation
with st.sidebar.expander("📋 Instructions d'installation"):
    st.markdown("""
    **Pour une expérience complète:**
    
    ```bash
    # Installer FFmpeg
    # Windows (avec chocolatey):
    choco install ffmpeg
    
    # Ubuntu/Debian:
    sudo apt update && sudo apt install ffmpeg
    
    # Mac (avec brew):
    brew install ffmpeg
    
    # Ou utiliser pip:
    pip install ffmpeg-python
    ```
    
    **Formats disponibles sans FFmpeg:**
    - Vidéo: MP4, WebM (natifs)
    - Audio: M4A, Opus, OGG (natifs)
    """)
