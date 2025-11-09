import streamlit as st
import os
import tempfile
import subprocess
import time
import math
import json
import re
import requests
from urllib.parse import quote

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
    'using_fallback': False
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- CSS Amélioré ---
def load_css(theme_name):
    if theme_name == "Cyberpunk":
        cyberpunk_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
            .stApp { 
                background: #0a0a0a; 
                color: #e0e0e0; 
                font-family: 'Orbitron', sans-serif; 
                background-image: 
                    radial-gradient(circle at 25% 25%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, rgba(255, 0, 255, 0.1) 0%, transparent 50%);
            }
            .stButton > button { 
                background: linear-gradient(45deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.2)); 
                border: 1px solid #00ffff; 
                color: #00ffff; 
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            .stButton > button:hover { 
                background: rgba(0, 255, 255, 0.3);
                box-shadow: 0 0 15px #00ffff;
                transform: translateY(-2px);
            }
            .glitch { 
                font-size: 4.5rem; 
                font-weight: 900; 
                color: #00ffff; 
                font-family: 'Orbitron', sans-serif; 
                text-align: center;
                text-shadow: 0 0 10px #00ffff;
                margin-bottom: 2rem;
            }
            .metadata-card { 
                background: rgba(255, 255, 255, 0.07); 
                border: 1px solid rgba(0, 255, 255, 0.3); 
                border-radius: 15px; 
                padding: 20px; 
                backdrop-filter: blur(10px);
            }
            .warning-box { 
                background: rgba(255, 165, 0, 0.1); 
                border: 1px solid orange; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0; 
            }
            .success-box { 
                background: rgba(0, 255, 0, 0.1); 
                border: 1px solid #00ff00; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0; 
            }
            .info-box { 
                background: rgba(0, 255, 255, 0.1); 
                border: 1px solid #00ffff; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0; 
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
                background: rgba(255, 255, 255, 0.08);
                border-color: #00ffff;
                transform: translateY(-3px);
            }
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)

# --- Installation des Dépendances ---
def install_dependencies():
    """Tente d'installer les dépendances manquantes"""
    dependencies = [
        "pytubefix",
        "yt-dlp",
        "requests"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([
                "pip", "install", dep, "--quiet", "--no-warn-script-location"
            ], check=True, timeout=60)
            st.sidebar.success(f"✅ {dep} installé")
        except:
            st.sidebar.warning(f"⚠️ {dep} installation échouée")

# --- Vérification des Dépendances ---
def check_dependencies():
    """Vérifie toutes les dépendances"""
    deps_status = {}
    
    # Vérifier yt-dlp
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
        deps_status["yt-dlp"] = result.returncode == 0
    except:
        deps_status["yt-dlp"] = False
    
    # Vérifier pytubefix
    try:
        import pytubefix
        deps_status["pytubefix"] = True
    except ImportError:
        deps_status["pytubefix"] = False
    
    # Vérifier requests
    try:
        import requests
        deps_status["requests"] = True
    except ImportError:
        deps_status["requests"] = False
    
    return deps_status

# --- Fonctions Utilitaires ---
def validate_youtube_url(url):
    """Valide l'URL YouTube"""
    youtube_patterns = [
        r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^(https?://)?(www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url or ""):
            return True
    return False

def get_video_id(url):
    """Extrait l'ID de la vidéo"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url or "")
        if match:
            return match.group(1)
    return None

def clean_youtube_url(url):
    """Nettoie l'URL YouTube"""
    video_id = get_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def format_duration(seconds):
    """Formate la durée"""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    except:
        return "N/A"

# --- RECHERCHE YOUTUBE AMÉLIORÉE ---
@st.cache_data(ttl=1800, show_spinner="🔍 Recherche en cours...")
def search_youtube_improved(query, limit=10):
    """
    Recherche YouTube avec multiples méthodes de fallback
    """
    clean_query = re.sub(r'[^\w\s]', '', query.strip())[:100]
    
    if not clean_query:
        return get_demo_results("musique")
    
    # Méthode 1: yt-dlp (si disponible)
    if st.session_state.get('deps_status', {}).get('yt-dlp', False):
        try:
            result = subprocess.run([
                'yt-dlp', 
                f'ytsearch{limit}:{clean_query}',
                '--dump-json',
                '--no-download',
                '--no-warnings',
                '--ignore-errors',
                '--quiet'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                videos = []
                for line in result.stdout.splitlines():
                    try:
                        data = json.loads(line)
                        videos.append({
                            'id': data.get('id'),
                            'title': data.get('title', 'Sans titre'),
                            'link': data.get('webpage_url'),
                            'channel': {'name': data.get('uploader', 'Chaîne inconnue')},
                            'duration': {'text': format_duration(data.get('duration'))},
                            'viewCount': {'text': f"{data.get('view_count', 0):,}"},
                            'thumbnail': [{'url': data.get('thumbnail')}]
                        })
                    except:
                        continue
                
                if videos:
                    st.session_state.using_fallback = False
                    return videos
        except:
            pass
    
    # Méthode 2: pytubefix (méthode principale)
    try:
        from pytubefix import Search
        
        search = Search(clean_query)
        videos = []
        
        for video in search.results[:limit]:
            try:
                videos.append({
                    'id': video.video_id,
                    'title': video.title or 'Sans titre',
                    'link': f"https://www.youtube.com/watch?v={video.video_id}",
                    'channel': {'name': video.author or 'Chaîne inconnue'},
                    'duration': {'text': format_duration(video.length)},
                    'viewCount': {'text': f"{video.views:,}"},
                    'thumbnail': [{'url': video.thumbnail_url}]
                })
            except:
                continue
        
        if videos:
            st.session_state.using_fallback = False
            return videos
    except Exception as e:
        st.warning(f"⚠️ pytubefix échoué: {str(e)}")
    
    # Méthode 3: API de recherche YouTube (fallback)
    try:
        return youtube_api_search(clean_query, limit)
    except:
        pass
    
    # Méthode 4: Résultats de démonstration
    st.session_state.using_fallback = True
    return get_demo_results(clean_query)

def youtube_api_search(query, limit):
    """Recherche via l'API YouTube non officielle"""
    try:
        encoded_query = quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Extraction basique des IDs vidéo
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
            unique_ids = list(dict.fromkeys(video_ids))[:limit]
            
            videos = []
            for vid in unique_ids:
                video_url = f"https://www.youtube.com/watch?v={vid}"
                video_data = get_video_info_improved(video_url)
                if video_data:
                    videos.append(video_data)
            
            return videos if videos else get_demo_results(query)
    except:
        pass
    
    return get_demo_results(query)

def get_demo_results(query):
    """Résultats de démonstration"""
    demos = [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'🎵 Musique: {query} - Exemple 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Musique'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1,234,567'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}]
        },
        {
            'id': 'kJQP7kiw5Fk',
            'title': f'🎵 Musique: {query} - Exemple 2', 
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Internationale'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987,654'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}]
        },
        {
            'id': '9bZkp7q19f0',
            'title': f'🎵 Musique: {query} - Exemple 3',
            'link': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
            'channel': {'name': 'Chaîne Viral'},
            'duration': {'text': '4:12'},
            'viewCount': {'text': '2,345,678'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg'}]
        }
    ]
    return demos

# --- OBTENTION DES INFORMATIONS VIDÉO ---
def get_video_info_improved(url):
    """Obtient les infos vidéo avec multiples méthodes"""
    clean_url = clean_youtube_url(url)
    
    # Méthode 1: pytubefix
    try:
        from pytubefix import YouTube
        yt = YouTube(clean_url)
        
        return {
            'id': yt.video_id,
            'title': yt.title or 'Titre non disponible',
            'link': clean_url,
            'channel': {'name': yt.author or 'Chaîne inconnue'},
            'duration': {'text': format_duration(yt.length)},
            'viewCount': {'text': f"{yt.views:,}"},
            'thumbnail': [{'url': yt.thumbnail_url}]
        }
    except Exception as e:
        st.warning(f"⚠️ Erreur pytubefix: {str(e)}")
    
    # Méthode 2: yt-dlp
    try:
        result = subprocess.run([
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--ignore-errors',
            clean_url
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'id': data.get('id'),
                'title': data.get('title', 'Titre non disponible'),
                'link': clean_url,
                'channel': {'name': data.get('uploader', 'Chaîne inconnue')},
                'duration': {'text': format_duration(data.get('duration'))},
                'viewCount': {'text': f"{data.get('view_count', 0):,}"},
                'thumbnail': [{'url': data.get('thumbnail')}]
            }
    except:
        pass
    
    return None

# --- TÉLÉCHARGEMENT AMÉLIORÉ ---
def download_media_improved(url, format_choice):
    """Téléchargement avec gestion d'erreurs avancée"""
    try:
        clean_url = clean_youtube_url(url)
        temp_dir = tempfile.mkdtemp()
        
        progress = st.progress(0)
        status = st.empty()
        
        status.info("🔄 Initialisation du téléchargement...")
        progress.progress(10)
        
        # Méthode 1: pytubefix (recommandée)
        try:
            from pytubefix import YouTube
            
            status.info("📥 Téléchargement avec pytubefix...")
            yt = YouTube(clean_url)
            
            if format_choice == "MP4 (Vidéo)":
                # Obtenir le stream vidéo le plus adapté
                stream = yt.streams.filter(
                    progressive=True, 
                    file_extension='mp4'
                ).order_by('resolution').desc().first()
                
                if not stream:
                    stream = yt.streams.filter(file_extension='mp4').first()
                
                if stream:
                    file_path = stream.download(output_path=temp_dir)
                    progress.progress(100)
                    status.success("✅ Téléchargement MP4 réussi!")
                    return file_path, os.path.basename(file_path), "video/mp4"
            
            else:  # MP3
                # Télécharger l'audio
                audio_stream = yt.streams.filter(only_audio=True).first()
                if audio_stream:
                    file_path = audio_stream.download(output_path=temp_dir)
                    
                    # Renommer en .mp3 si nécessaire
                    if not file_path.endswith('.mp3'):
                        new_path = os.path.splitext(file_path)[0] + '.mp3'
                        os.rename(file_path, new_path)
                        file_path = new_path
                    
                    progress.progress(100)
                    status.success("✅ Téléchargement MP3 réussi!")
                    return file_path, os.path.basename(file_path), "audio/mpeg"
                    
        except Exception as e:
            st.warning(f"⚠️ pytubefix échoué: {str(e)}")
        
        # Méthode 2: yt-dlp (fallback)
        status.info("🔄 Méthode alternative...")
        progress.progress(50)
        
        if format_choice == "MP4 (Vidéo)":
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp',
                '-f', 'best[height<=720]',
                '--merge-output-format', 'mp4', 
                '--ignore-errors',
                '--no-warnings',
                '-o', output_template,
                clean_url
            ]
        else:
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp',
                '-x', '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--ignore-errors', 
                '--no-warnings',
                '-o', output_template,
                clean_url
            ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        progress.progress(80)
        
        if result.returncode == 0:
            # Trouver le fichier téléchargé
            for file in os.listdir(temp_dir):
                if file.endswith(('.mp4', '.mp3', '.webm')):
                    file_path = os.path.join(temp_dir, file)
                    mime_type = "video/mp4" if format_choice == "MP4 (Vidéo)" else "audio/mpeg"
                    
                    # Renommer si nécessaire
                    if format_choice == "MP3 (Audio)" and not file.endswith('.mp3'):
                        new_path = os.path.splitext(file_path)[0] + '.mp3'
                        os.rename(file_path, new_path)
                        file_path = new_path
                    
                    progress.progress(100)
                    status.success("✅ Téléchargement réussi!")
                    return file_path, os.path.basename(file_path), mime_type
        
        raise Exception("Aucune méthode de téléchargement n'a fonctionné")
        
    except subprocess.TimeoutExpired:
        status.error("⏱️ Timeout lors du téléchargement")
        return None, None, None
    except Exception as e:
        status.error(f"❌ Erreur: {str(e)}")
        return None, None, None
    finally:
        time.sleep(2)
        progress.empty()
        status.empty()

# --- INTERFACE UTILISATEUR ---
def display_video_metadata(video_data):
    """Affiche les métadonnées de la vidéo"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        thumbnails = video_data.get('thumbnail', [])
        if thumbnails:
            st.image(thumbnails[0]['url'], width=200, use_column_width=True)
    
    with col2:
        title = video_data.get('title', 'Titre non disponible')
        channel = video_data.get('channel', {}).get('name', 'Chaîne inconnue')
        views = video_data.get('viewCount', {}).get('text', 'N/A vues')
        duration = video_data.get('duration', {}).get('text', 'N/A')
        
        st.markdown(f"""
        <div class='metadata-card'>
            <h3 style='color: #00ffff; margin-bottom: 10px;'>{title}</h3>
            <p><strong>Chaîne:</strong> {channel}</p>
            <p><strong>Vues:</strong> {views} | <strong>Durée:</strong> {duration}</p>
        </div>
        """, unsafe_allow_html=True)

def render_search_results(results):
    """Affiche les résultats de recherche"""
    results_per_page = 3
    start_idx = (st.session_state.current_page - 1) * results_per_page
    end_idx = start_idx + results_per_page
    page_results = results[start_idx:end_idx]
    
    for video in page_results:
        with st.container():
            st.markdown("<div class='video-card'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                thumbnails = video.get('thumbnail', [])
                if thumbnails:
                    st.image(thumbnails[0]['url'], use_column_width=True)
            
            with col2:
                title = video.get('title', 'Sans titre')
                channel = video.get('channel', {}).get('name', 'Chaîne inconnue')
                views = video.get('viewCount', {}).get('text', 'N/A vues')
                duration = video.get('duration', {}).get('text', 'N/A')
                
                st.markdown(f"**{title}**")
                st.caption(f"👤 {channel} | 👁️ {views} | ⏱️ {duration}")
            
            with col3:
                if st.button("📥 Sélectionner", key=f"sel_{video['id']}", use_container_width=True):
                    st.session_state.selected_video_url = video['link']
                    st.session_state.selected_video_data = video
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

def render_pagination():
    """Affiche la pagination"""
    if st.session_state.total_pages <= 1:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Précédent", disabled=st.session_state.current_page == 1):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col2:
        st.markdown(
            f"<div style='text-align: center; color: #00ffff;'>"
            f"Page {st.session_state.current_page} / {st.session_state.total_pages}"
            f"</div>", 
            unsafe_allow_html=True
        )
    
    with col3:
        if st.button("Suivant ➡️", disabled=st.session_state.current_page == st.session_state.total_pages):
            st.session_state.current_page += 1
            st.rerun()

# --- APPLICATION PRINCIPALE ---

# Initialisation des dépendances
if 'deps_status' not in st.session_state:
    st.session_state.deps_status = check_dependencies()

theme = st.sidebar.selectbox("🎨 Thème", ["Cyberpunk", "Clair"])
load_css(theme)

# Header
if not st.session_state.title_typed:
    st.markdown('<h1 class="typing-title">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)
    time.sleep(1.5)
    st.session_state.title_typed = True
    st.rerun()
else:
    st.markdown('<h1 class="glitch" data-text="CYBER-STREAM TERMINAL">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)

# Sidebar - Contrôles
st.sidebar.title("🎛️ Panneau de Contrôle")

# Vérification des dépendances
with st.sidebar.expander("🔧 État du Système", expanded=True):
    deps = st.session_state.deps_status
    
    if deps.get('pytubefix'):
        st.success("✅ pytubefix: Prêt")
    else:
        st.error("❌ pytubefix: Manquant")
    
    if deps.get('yt-dlp'):
        st.success("✅ yt-dlp: Prêt") 
    else:
        st.warning("⚠️ yt-dlp: Limité")
    
    if deps.get('requests'):
        st.success("✅ requests: Prêt")
    else:
        st.error("❌ requests: Manquant")
    
    if not any(deps.values()):
        st.error("❌ Aucune dépendance disponible!")
        if st.button("🔄 Installer les Dépendances"):
            install_dependencies()
            st.session_state.deps_status = check_dependencies()
            st.rerun()

# Recherche
st.sidebar.markdown("---")
search_query = st.sidebar.text_input("🔍 Rechercher des vidéos:", value="musique")
download_format = st.sidebar.selectbox("📦 Format:", ["MP4 (Vidéo)", "MP3 (Audio)"])

if st.sidebar.button("🚀 Lancer la Recherche", use_container_width=True) and search_query:
    with st.spinner("Recherche en cours..."):
        results = search_youtube_improved(search_query)
        st.session_state.search_results = results
        st.session_state.total_pages = max(1, math.ceil(len(results) / 3))
        st.session_state.current_page = 1
        st.session_state.selected_video_url = None
        
        if results:
            st.sidebar.success(f"✅ {len(results)} résultats trouvés")
        else:
            st.sidebar.error("❌ Aucun résultat trouvé")

# URL directe
st.sidebar.markdown("---")
direct_url = st.sidebar.text_input("🌐 URL YouTube directe:")

if direct_url and validate_youtube_url(direct_url):
    with st.spinner("Chargement de la vidéo..."):
        video_data = get_video_info_improved(direct_url)
        if video_data:
            st.session_state.selected_video_url = direct_url
            st.session_state.selected_video_data = video_data
            st.sidebar.success("✅ Vidéo chargée!")
        else:
            st.sidebar.error("❌ Erreur de chargement")

# Affichage des résultats
if st.session_state.search_results:
    st.subheader("📺 Résultats de Recherche")
    
    # Avertissement mode fallback
    if st.session_state.using_fallback:
        st.warning("""
        🔄 **Mode démonstration activé**  
        Les résultats sont simulés pour tester l'interface.  
        Pour une recherche réelle, vérifiez l'installation des dépendances.
        """)
    
    render_search_results(st.session_state.search_results)
    render_pagination()

# Vidéo sélectionnée
if st.session_state.selected_video_url and st.session_state.selected_video_data:
    st.subheader("🎬 Vidéo Sélectionnée")
    display_video_metadata(st.session_state.selected_video_data)
    
    # Lecteur vidéo
    video_id = get_video_id(st.session_state.selected_video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.components.v1.iframe(embed_url, height=400)
    
    # Contrôles de téléchargement
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⬇️ Télécharger la Vidéo", use_container_width=True, type="primary"):
            file_path, file_name, mime_type = download_media_improved(
                st.session_state.selected_video_url,
                download_format
            )
            
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_data = f.read()
                
                st.download_button(
                    label=f"💾 Télécharger {file_name}",
                    data=file_data,
                    file_name=file_name,
                    mime=mime_type,
                    use_container_width=True
                )
                
                # Nettoyage
                try:
                    os.remove(file_path)
                    os.rmdir(os.path.dirname(file_path))
                except:
                    pass
    
    with col2:
        if st.button("🗑️ Effacer la Sélection", use_container_width=True):
            st.session_state.selected_video_url = None
            st.session_state.selected_video_data = None
            st.rerun()

# État initial
elif not st.session_state.search_results:
    st.info("""
    🎯 **Bienvenue dans CYBER-STREAM TERMINAL**
    
    Pour commencer :
    1. 🔍 **Recherchez** des vidéos en utilisant la barre de recherche
    2. 🌐 **Ou collez** une URL YouTube directe
    3. 📥 **Sélectionnez** une vidéo et téléchargez-la
    
    *Assurez-vous que les dépendances sont installées pour une expérience optimale.*
    """)

# Instructions d'installation
with st.sidebar.expander("📋 Guide d'Installation"):
    st.markdown("""
    **Pour une installation complète:**
    
    ```bash
    # Méthode recommandée (dans votre terminal)
    pip install pytubefix yt-dlp requests
    ```
    
    **Dépendances:**
    - `pytubefix`: Bibliothèque principale (fixe les problèmes de pytube)
    - `yt-dlp`: Alternative avancée pour le téléchargement  
    - `requests`: Pour les requêtes HTTP
    
    **Fonctionnalités:**
    - ✅ Recherche YouTube
    - ✅ Téléchargement MP4/MP3
    - ✅ Interface cyberpunk
    - ✅ Gestion d'erreurs avancée
    """)
