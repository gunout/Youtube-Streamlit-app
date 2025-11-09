import streamlit as st
import os
import tempfile
import subprocess
import time
import math
import json
import re
import sys
import platform
from datetime import datetime

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
    'ffmpeg_available': False,
    'ffmpeg_source': None,
    'ffmpeg_installation_tried': False,
    'download_history': [],
    'dependencies_checked': False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Système et Dépendances ---
def get_system_info():
    """Récupère les informations système"""
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()[0]
    }

def check_ffmpeg():
    """Vérification complète de FFmpeg"""
    # Méthode 1: ffmpeg système
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, "Système"
    except:
        pass
    
    # Méthode 2: ffmpeg-python
    try:
        import ffmpeg
        # Test si ffmpeg est fonctionnel
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            return True, "ffmpeg-python"
        except:
            return True, "ffmpeg-python (limité)"
    except ImportError:
        pass
    
    # Méthode 3: imageio-ffmpeg
    try:
        import imageio_ffmpeg
        return True, "imageio-ffmpeg"
    except ImportError:
        pass
    
    return False, None

def install_ffmpeg_complete():
    """Installation complète de FFmpeg avec multiples méthodes"""
    methods = [
        {"name": "ffmpeg-python", "command": [sys.executable, "-m", "pip", "install", "ffmpeg-python"]},
        {"name": "imageio-ffmpeg", "command": [sys.executable, "-m", "pip", "install", "imageio-ffmpeg"]},
    ]
    
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    for i, method in enumerate(methods):
        try:
            progress = (i + 1) / len(methods)
            progress_bar.progress(progress)
            status_text.text(f"🔧 Installation de {method['name']}...")
            
            result = subprocess.run(
                method['command'] + ["--quiet", "--no-warn-script-location"],
                capture_output=True, 
                text=True, 
                timeout=120,
                check=True
            )
            
            status_text.text(f"✅ {method['name']} installé!")
            time.sleep(1)
            
            # Vérifier si ça marche
            available, source = check_ffmpeg()
            if available:
                st.session_state.ffmpeg_available = True
                st.session_state.ffmpeg_source = source
                st.session_state.ffmpeg_installation_tried = True
                progress_bar.progress(1.0)
                status_text.text("🎉 FFmpeg est maintenant opérationnel!")
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
                return True
                
        except Exception as e:
            status_text.text(f"❌ {method['name']} a échoué")
            time.sleep(1)
            continue
    
    progress_bar.empty()
    status_text.text("😞 Toutes les méthodes ont échoué")
    time.sleep(2)
    status_text.empty()
    st.session_state.ffmpeg_installation_tried = True
    return False

def check_yt_dlp():
    """Vérifie yt-dlp"""
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "Erreur"
    except:
        return False, "Non disponible"

# --- CSS et Style ---
def load_css(theme_name):
    """Charge le CSS selon le thème"""
    if theme_name == "Cyberpunk":
        cyberpunk_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            .stApp { 
                background: linear-gradient(135deg, #0a0a0a 0%, #1a0a1a 100%); 
                color: #e0e0e0; 
                font-family: 'Orbitron', sans-serif; 
            }
            .stButton > button { 
                background: linear-gradient(45deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.2)); 
                border: 1px solid #00ffff; 
                color: #00ffff; 
                transition: all 0.3s ease;
                font-weight: bold;
            }
            .stButton > button:hover {
                background: linear-gradient(45deg, rgba(0, 255, 255, 0.3), rgba(0, 255, 255, 0.4));
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3);
            }
            .glitch { 
                font-size: 4.5rem; 
                font-weight: 900; 
                color: #00ffff; 
                font-family: 'Orbitron', sans-serif;
                text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
                animation: glitch 2s infinite;
            }
            @keyframes glitch {
                0%, 100% { text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff; }
                25% { text-shadow: -2px 0 #ff00ff, 2px 0 #00ffff; }
                50% { text-shadow: 2px 0 #ff00ff, -2px 0 #00ffff; }
                75% { text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff; }
            }
            .metadata-card { 
                background: rgba(255, 255, 255, 0.07); 
                border: 1px solid rgba(0, 255, 255, 0.3); 
                border-radius: 15px; 
                padding: 20px;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            .metadata-card:hover {
                border-color: rgba(0, 255, 255, 0.6);
                box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
            }
            .success-box { 
                background: rgba(0, 255, 0, 0.1); 
                border: 1px solid #00ff00; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                backdrop-filter: blur(5px);
            }
            .warning-box { 
                background: rgba(255, 165, 0, 0.1); 
                border: 1px solid orange; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                backdrop-filter: blur(5px);
            }
            .error-box { 
                background: rgba(255, 0, 0, 0.1); 
                border: 1px solid #ff0000; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                backdrop-filter: blur(5px);
            }
            .typing-title {
                font-size: 3rem;
                color: #00ffff;
                font-family: 'Orbitron', sans-serif;
                overflow: hidden;
                white-space: nowrap;
                animation: typing 3s steps(30, end);
            }
            @keyframes typing {
                from { width: 0 }
                to { width: 100% }
            }
            .video-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                transition: all 0.3s ease;
            }
            .video-card:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: rgba(0, 255, 255, 0.5);
                transform: translateX(5px);
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 10px;
                animation: pulse 2s infinite;
            }
            .status-online { background: #00ff00; }
            .status-warning { background: #ffa500; }
            .status-offline { background: #ff0000; }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)

# --- Fonctions Utilitaires ---
def validate_youtube_url(url):
    """Validation améliorée des URLs YouTube"""
    if not url:
        return False
    
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

def get_video_id(url):
    """Extrait l'ID vidéo d'une URL YouTube"""
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
    """Nettoie et standardise une URL YouTube"""
    video_id = get_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

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

def format_views(view_count):
    """Formate le nombre de vues"""
    try:
        count = int(view_count)
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        else:
            return f"{count:,}"
    except:
        return "N/A"

def safe_search_query(query):
    """Nettoie et sécurise la requête de recherche"""
    if not query:
        return ""
    cleaned = re.sub(r'[^\w\s\-]', '', query)
    return cleaned.strip()[:100]

# --- Fonctions YouTube ---
@st.cache_data(ttl=3600, show_spinner="Recherche en cours...")
def search_youtube(query, limit=15):
    """Recherche YouTube avec gestion d'erreurs améliorée"""
    try:
        clean_query = safe_search_query(query)
        if not clean_query:
            return get_demo_results("exemple")
        
        search_command = [
            'yt-dlp',
            f'ytsearch{limit}:"{clean_query}"',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--quiet',
            '--ignore-errors',
            '--socket-timeout', '30',
            '--source-timeout', '30'
        ]
        
        result = subprocess.run(
            search_command, 
            capture_output=True, 
            text=True, 
            timeout=45
        )
        
        videos = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    video_data = json.loads(line)
                    duration = video_data.get('duration')
                    duration_text = format_duration(duration) if duration else 'N/A'
                    view_count = video_data.get('view_count', 0)
                    
                    videos.append({
                        'id': video_data.get('id'),
                        'title': video_data.get('title', 'Sans titre'),
                        'link': video_data.get('webpage_url'),
                        'channel': {'name': video_data.get('uploader', 'Chaîne inconnue')},
                        'duration': {'text': duration_text},
                        'viewCount': {'text': format_views(view_count)},
                        'viewCount_raw': view_count,
                        'thumbnail': [{'url': video_data.get('thumbnail')}],
                        'upload_date': video_data.get('upload_date', ''),
                        'description': video_data.get('description', '')[:200] + '...' if video_data.get('description') else ''
                    })
                except json.JSONDecodeError:
                    continue
        
        return videos if videos else get_demo_results(query)
        
    except Exception as e:
        st.error(f"Erreur lors de la recherche: {str(e)}")
        return get_demo_results(query)

def get_demo_results(query):
    """Résultats de démonstration"""
    return [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'Demo: {query} - Résultat 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Démo'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1.2M'},
            'viewCount_raw': 1234567,
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}],
            'upload_date': '20220101',
            'description': 'Ceci est une vidéo de démonstration...'
        },
        {
            'id': 'kJQP7kiw5Fk', 
            'title': f'Demo: {query} - Résultat 2',
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Test'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987K'},
            'viewCount_raw': 987654,
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}],
            'upload_date': '20220102',
            'description': 'Une autre vidéo de démonstration...'
        }
    ]

def get_video_info(url):
    """Récupère les informations détaillées d'une vidéo"""
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
            view_count = video_data.get('view_count', 0)
            
            return {
                'id': video_data.get('id'),
                'title': video_data.get('title', 'Titre non disponible'),
                'link': clean_url,
                'channel': {'name': video_data.get('uploader', 'Chaîne inconnue')},
                'duration': {'text': duration_text},
                'viewCount': {'text': format_views(view_count)},
                'viewCount_raw': view_count,
                'thumbnail': [{'url': video_data.get('thumbnail')}],
                'upload_date': video_data.get('upload_date', ''),
                'description': video_data.get('description', '')
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Erreur lors de la récupération des infos: {str(e)}")
        return None

# --- Fonctions de Téléchargement ---
def download_media(url, format_choice):
    """Téléchargement avec support FFmpeg complet et gestion d'erreurs"""
    try:
        clean_url = clean_youtube_url(url)
        temp_dir = tempfile.mkdtemp()
        
        # Vérifier FFmpeg à nouveau
        ffmpeg_available, ffmpeg_source = check_ffmpeg()
        st.session_state.ffmpeg_available = ffmpeg_available
        st.session_state.ffmpeg_source = ffmpeg_source
        
        st.info("🔄 Configuration du téléchargement...")
        
        if format_choice == "MP4 (Vidéo)":
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp', 
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '--ignore-errors',
                '--no-warnings',
                '-o', output_template, 
                clean_url
            ]
        else:  # MP3
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            
            if ffmpeg_available:
                # AVEC FFMPEG - Vraie conversion MP3
                command = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '--audio-quality', '192K',  # Qualité haute
                    '--ignore-errors',
                    '--no-warnings',
                    '-o', output_template,
                    clean_url
                ]
                st.success(f"🎵 Conversion MP3 avec FFmpeg ({ffmpeg_source}) activée!")
            else:
                # SANS FFMPEG - Fallback
                st.warning("⚠️ FFmpeg non disponible - Format audio natif")
                command = [
                    'yt-dlp',
                    '-x',
                    '--ignore-errors',
                    '--no-warnings',
                    '-o', output_template,
                    clean_url
                ]
        
        st.info("📥 Téléchargement en cours...")
        
        # Barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Exécution avec mise à jour de progression
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            universal_newlines=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                # Simple progression basique
                if '[download]' in output:
                    progress = min(0.9, float(st.session_state.get('download_progress', 0)) + 0.1)
                    progress_bar.progress(progress)
                    st.session_state.download_progress = progress
        
        # Récupérer le résultat final
        process.wait()
        
        if process.returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Téléchargement terminé!")
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            # Recherche du fichier
            downloaded_file = None
            for file in os.listdir(temp_dir):
                file_lower = file.lower()
                
                if format_choice == "MP4 (Vidéo)":
                    if file_lower.endswith(('.mp4', '.webm', '.mkv')):
                        downloaded_file = os.path.join(temp_dir, file)
                        if not downloaded_file.endswith('.mp4'):
                            new_file = os.path.splitext(downloaded_file)[0] + '.mp4'
                            os.rename(downloaded_file, new_file)
                            downloaded_file = new_file
                        mime_type = "video/mp4"
                        break
                else:  # MP3
                    if file_lower.endswith('.mp3'):
                        # Vrai MP3 avec FFmpeg
                        downloaded_file = os.path.join(temp_dir, file)
                        mime_type = "audio/mpeg"
                        st.success("🎵 Fichier MP3 converti avec FFmpeg!")
                        break
                    elif file_lower.endswith(('.m4a', '.ogg', '.opus', '.wav')):
                        # Format natif sans FFmpeg
                        downloaded_file = os.path.join(temp_dir, file)
                        new_file = os.path.splitext(downloaded_file)[0] + '.mp3'
                        os.rename(downloaded_file, new_file)
                        downloaded_file = new_file
                        mime_type = "audio/mpeg"
                        st.warning("🔸 Fichier audio natif renommé (pas de conversion FFmpeg)")
                        break
            
            if downloaded_file:
                file_name = os.path.basename(downloaded_file)
                
                # Ajouter à l'historique
                history_entry = {
                    'title': st.session_state.selected_video_data.get('title', 'Inconnu'),
                    'format': format_choice,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'file_name': file_name
                }
                st.session_state.download_history.insert(0, history_entry)
                if len(st.session_state.download_history) > 10:
                    st.session_state.download_history = st.session_state.download_history[:10]
                
                return downloaded_file, file_name, mime_type
            else:
                raise Exception("Aucun fichier trouvé après téléchargement")
        else:
            error_output = process.stderr.read()
            raise Exception(f"Échec du téléchargement: {error_output}")
            
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout lors du téléchargement")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None, None, None
    finally:
        # Nettoyage
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()

# --- Interface Utilisateur ---
def display_metadata(video_data):
    """Affiche les métadonnées d'une vidéo"""
    col1, col2 = st.columns([1, 3])
    with col1:
        thumbnail_list = video_data.get('thumbnail', [])
        if thumbnail_list: 
            st.image(thumbnail_list[0]['url'], width=200, use_column_width=False)
    with col2:
        title = video_data.get('title', 'Titre non disponible')
        channel_name = video_data.get('channel', {}).get('name', 'Chaîne inconnue')
        view_text = video_data.get('viewCount', {}).get('text', 'N/A vues')
        duration_text = video_data.get('duration', {}).get('text', 'N/A')
        upload_date = video_data.get('upload_date', '')
        description = video_data.get('description', '')
        
        st.markdown(f"""
        <div class='metadata-card'>
            <h3>{title}</h3>
            <p>👤 Chaîne : {channel_name}</p>
            <p>👁️ Vues : {view_text} | ⏱️ Durée : {duration_text}</p>
            {f"<p>📅 Date : {upload_date}</p>" if upload_date else ""}
            {f"<p>📝 {description}</p>" if description else ""}
        </div>
        """, unsafe_allow_html=True)

def render_pagination():
    """Affiche les contrôles de pagination"""
    if st.session_state.total_pages <= 1:
        return
        
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Précédent", disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page -= 1
            st.rerun()
    with col_info:
        st.markdown(f"<div style='color: #00ffff; text-align: center; font-weight: bold;'>Page {st.session_state.current_page} / {st.session_state.total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("Suivant ➡️", disabled=(st.session_state.current_page == st.session_state.total_pages)):
            st.session_state.current_page += 1
            st.rerun()

def display_video_card(video, index):
    """Affiche une carte vidéo stylisée"""
    with st.container():
        st.markdown(f"""
        <div class='video-card'>
        """, unsafe_allow_html=True)
        
        col_img, col_info, col_button = st.columns([1, 3, 1])
        with col_img:
            thumbnail_list = video.get('thumbnail', [])
            if thumbnail_list: 
                st.image(thumbnail_list[0]['url'], width=120, use_column_width=False)
        with col_info:
            title = video.get('title', 'Sans titre')
            channel_name = video.get('channel', {}).get('name', 'Chaîne inconnue')
            view_text = video.get('viewCount', {}).get('text', 'N/A vues')
            duration_text = video.get('duration', {}).get('text', 'N/A')
            
            st.markdown(f"**{title}**")
            st.caption(f"👤 {channel_name} | 👁️ {view_text} | ⏱️ {duration_text}")
        with col_button:
            if st.button("▶️ Sélectionner", key=f"select_{video['id']}_{index}"):
                st.session_state.selected_video_url = video['link']
                st.session_state.selected_video_data = video
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")

def display_download_history():
    """Affiche l'historique des téléchargements"""
    if st.session_state.download_history:
        st.subheader("📜 Historique des téléchargements")
        for i, entry in enumerate(st.session_state.download_history):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📹 {entry['title']}")
            with col2:
                st.write(f"🎵 {entry['format']}")
            with col3:
                st.write(f"📅 {entry['date']}")
        st.markdown("---")

# --- APPLICATION PRINCIPALE ---

# Vérification initiale des dépendances
if not st.session_state.dependencies_checked:
    with st.spinner("Vérification des dépendances..."):
        st.session_state.ffmpeg_available, st.session_state.ffmpeg_source = check_ffmpeg()
        st.session_state.dependencies_checked = True

# Configuration du thème
theme = st.sidebar.selectbox("🎨 Thème", ["Cyberpunk", "Clair"])
load_css(theme)

# Animation du titre
if not st.session_state.title_typed:
    st.markdown('<h1 class="typing-title">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.title_typed = True
    st.rerun()
else:
    st.markdown('<h1 class="glitch" data-text="CYBER-STREAM TERMINAL">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)

# Sidebar - Contrôles principaux
st.sidebar.title("🎛️ Panneau de Contrôle")

# État des dépendances
st.sidebar.subheader("📊 État du Système")

# FFmpeg Status
ffmpeg_status = st.session_state.ffmpeg_available
status_class = "status-online" if ffmpeg_status else "status-warning"
status_text = "✅ Opérationnel" if ffmpeg_status else "⚠️ Requis"

st.sidebar.markdown(f"""
<div class='success-box' if ffmpeg_status else 'warning-box'>
<span class='status-indicator {status_class}'></span>
<strong>FFmpeg: {status_text}</strong><br>
{f"Source: {st.session_state.ffmpeg_source}" if st.session_state.ffmpeg_source else "Non installé"}
</div>
""", unsafe_allow_html=True)

if not st.session_state.ffmpeg_available and not st.session_state.ffmpeg_installation_tried:
    if st.sidebar.button("🚀 Installer FFmpeg Automatiquement", use_container_width=True):
        with st.sidebar:
            with st.spinner("Installation en cours..."):
                if install_ffmpeg_complete():
                    st.success("🎉 FFmpeg installé avec succès!")
                    st.rerun()

# yt-dlp Status
yt_dlp_available, yt_dlp_version = check_yt_dlp()
status_class = "status-online" if yt_dlp_available else "status-offline"
status_text = f"✅ {yt_dlp_version}" if yt_dlp_available else "❌ Non disponible"

st.sidebar.markdown(f"""
<div class='success-box' if yt_dlp_available else 'error-box'>
<span class='status-indicator {status_class}'></span>
<strong>yt-dlp: {status_text}</strong>
</div>
""", unsafe_allow_html=True)

# Système Info
system_info = get_system_info()
with st.sidebar.expander("💻 Informations Système"):
    st.write(f"**OS:** {system_info['platform']}")
    st.write(f"**Python:** {system_info['python_version']}")
    st.write(f"**Architecture:** {system_info['architecture']}")

st.sidebar.markdown("---")

# Contrôles de recherche
st.sidebar.subheader("🔍 Recherche")
search_query = st.sidebar.text_input("Terme de recherche:", key="search_input", value="musique")
download_format = st.sidebar.selectbox("Format de sortie:", ["MP4 (Vidéo)", "MP3 (Audio)"])

# Avertissement MP3 sans FFmpeg
if download_format == "MP3 (Audio)" and not st.session_state.ffmpeg_available:
    st.sidebar.markdown("""
    <div class='warning-box'>
    <strong>⚠️ MP3 Limité</strong><br>
    Sans FFmpeg: format natif renommé
    </div>
    """, unsafe_allow_html=True)

# URL directe
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 URL Directe")
direct_url = st.sidebar.text_input("Collez l'URL YouTube:", key="direct_url")

if direct_url and validate_youtube_url(direct_url):
    if st.sidebar.button("📥 Charger la vidéo", use_container_width=True):
        with st.spinner("Chargement des informations..."):
            video_data = get_video_info(direct_url)
            if video_data:
                st.session_state.selected_video_url = direct_url
                st.session_state.selected_video_data = video_data
                st.sidebar.success("✅ Vidéo chargée!")
                st.rerun()
            else:
                st.sidebar.error("❌ Erreur de chargement")

# Bouton de recherche
if st.sidebar.button("🚀 Lancer la recherche", use_container_width=True):
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
        st.rerun()
    else:
        st.sidebar.warning("⚠️ Entrez un terme de recherche")

# Zone principale
# Historique des téléchargements
display_download_history()

# Affichage des résultats de recherche
if st.session_state.search_results:
    st.subheader("📺 Résultats de recherche")
    results_per_page = 3
    start_index = (st.session_state.current_page - 1) * results_per_page
    end_index = start_index + results_per_page
    page_results = st.session_state.search_results[start_index:end_index]
    
    for i, video in enumerate(page_results):
        display_video_card(video, i)
    
    render_pagination()

# Vidéo sélectionnée
if st.session_state.selected_video_url and st.session_state.selected_video_data:
    st.subheader("🎬 Vidéo Sélectionnée")
    display_metadata(st.session_state.selected_video_data)
    
    video_id = get_video_id(st.session_state.selected_video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.components.v1.iframe(embed_url, height=400)
        
        # Avertissement spécifique pour MP3
        if download_format == "MP3 (Audio)" and not st.session_state.ffmpeg_available:
            st.warning("""
            **⚠️ Conversion MP3 limitée:** 
            Sans FFmpeg, le fichier sera un format audio natif (généralement m4a) renommé en .mp3.
            Pour une vraie conversion MP3, installez FFmpeg.
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬇️ Télécharger", use_container_width=True):
                with st.spinner("Téléchargement en cours..."):
                    file_path, file_name, mime_type = download_media(
                        st.session_state.selected_video_url, 
                        download_format
                    )
                    if file_path:
                        st.success(f"✅ {file_name} prêt!")
                        
                        # Afficher le bouton de téléchargement
                        with open(file_path, "rb") as f:
                            bytes_data = f.read()
                        
                        st.download_button(
                            label=f"💾 Télécharger {file_name}",
                            data=bytes_data,
                            file_name=file_name,
                            mime=mime_type,
                            use_container_width=True
                        )
                        
                        # Nettoyage des fichiers temporaires
                        try:
                            if os.path.exists(file_path):
                                os.unlink(file_path)
                            if os.path.exists(os.path.dirname(file_path)):
                                os.rmdir(os.path.dirname(file_path))
                        except:
                            pass
        
        with col2:
            if st.button("🗑️ Effacer", use_container_width=True):
                st.session_state.selected_video_url = None
                st.session_state.selected_video_data = None
                st.rerun()

elif not st.session_state.search_results:
    st.info("🔍 Lancez une recherche ou collez une URL YouTube pour commencer")

# Footer avec instructions
st.sidebar.markdown("---")
with st.sidebar.expander("📚 Guide d'Installation"):
    st.markdown("""
    **Installation FFmpeg Manuelle:**
    
    ```bash
    # Windows (avec Chocolatey):
    choco install ffmpeg
    
    # Ubuntu/Debian:
    sudo apt update && sudo apt install ffmpeg
    
    # Mac (avec Homebrew):
    brew install ffmpeg
    
    # Python (recommandé):
    pip install ffmpeg-python
    ```
    
    **Redémarrez l'application après installation.**
    
    **Actuellement:** 
    - ✅ MP4: Toujours fonctionnel
    - ⚠️ MP3: Limité sans FFmpeg
    """)

# Pied de page
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
<p>🦾 CYBER-STREAM Terminal v2.0 | Powered by yt-dlp & FFmpeg</p>
<p>⚡ Téléchargement haute vitesse | 🎵 Conversion audio | 📺 Vidéo HD</p>
</div>
""", unsafe_allow_html=True)
