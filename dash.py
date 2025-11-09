import streamlit as st
import os
import tempfile
import subprocess
import time
import math
import json
import re
import shlex

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
    'total_pages': 0
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
        </style>
        """
        st.markdown(cyberpunk_css, unsafe_allow_html=True)

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
    # Supprimer les caractères problématiques
    cleaned = re.sub(r'[^\w\s\-]', '', query)
    # Limiter la longueur
    return cleaned.strip()[:100]

# --- FONCTION DE RECHERCHE CORRIGÉE ---
@st.cache_data(ttl=3600, show_spinner="Recherche en cours...")
def search_youtube(query, limit=15):
    """
    Recherche robuste avec gestion des erreurs améliorée
    """
    try:
        clean_query = safe_search_query(query)
        if not clean_query:
            st.warning("❌ Requête de recherche vide après nettoyage")
            return get_demo_results("recherche exemple")
        
        # Méthode 1: Utiliser yt-dlp avec requête sécurisée
        try:
            # Construction sécurisée de la commande
            search_command = [
                'yt-dlp',
                f'ytsearch{limit}:{clean_query}',
                '--dump-json',
                '--no-download',
                '--no-warnings',
                '--quiet',
                '--ignore-errors',
                '--socket-timeout', '20',
                '--source-timeout', '20'
            ]
            
            result = subprocess.run(
                search_command, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            # Si yt-dlp échoue mais retourne du contenu, essayer de le parser quand même
            if result.stdout.strip():
                videos = []
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
                
                if videos:
                    return videos
            
            # Si on arrive ici, yt-dlp a échoué
            st.warning("yt-dlp a rencontré un problème, utilisation de la méthode alternative...")
            
        except Exception as e:
            st.warning(f"Erreur yt-dlp: {str(e)}")
        
        # Méthode 2: Fallback - recherche via API web scraping simple
        return search_youtube_fallback(clean_query, limit)
        
    except Exception as e:
        st.error(f"Erreur générale de recherche: {str(e)}")
        return get_demo_results(query)

def search_youtube_fallback(query, limit):
    """
    Méthode de fallback pour la recherche YouTube
    """
    try:
        import urllib.parse
        import requests
        
        # Encoder la requête pour URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Headers pour éviter le blocage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Extraire les IDs des vidéos depuis le HTML (méthode basique)
            video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)
            unique_ids = list(dict.fromkeys(video_ids))[:limit]
            
            videos = []
            for video_id in unique_ids:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_info = get_video_info_fallback(video_url)
                if video_info:
                    videos.append(video_info)
            
            return videos if videos else get_demo_results(query)
        else:
            st.warning("Fallback HTTP échoué, utilisation des résultats de démonstration")
            return get_demo_results(query)
            
    except Exception as e:
        st.warning(f"Fallback échoué: {str(e)}")
        return get_demo_results(query)

def get_video_info_fallback(url):
    """
    Obtient les infos vidéo via yt-dlp en mode simple
    """
    try:
        clean_url = clean_youtube_url(url)
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--ignore-errors',
            '--no-warnings',
            clean_url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
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
    except:
        pass
    return None

def get_demo_results(query):
    """Résultats de démonstration avec recherche simulée"""
    return [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'Résultat démo pour: {query} - Exemple 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Démonstration'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1,234,567'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}]
        },
        {
            'id': 'kJQP7kiw5Fk', 
            'title': f'Résultat démo pour: {query} - Exemple 2',
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Test'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987,654'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}]
        },
        {
            'id': '9bZkp7q19f0',
            'title': f'Résultat démo pour: {query} - Exemple 3',
            'link': 'https://www.youtube.com/watch?v=9bZkp7q19f0',
            'channel': {'name': 'Chaîne Exemple'},
            'duration': {'text': '4:12'},
            'viewCount': {'text': '2,345,678'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg'}]
        }
    ]

# --- FONCTION POUR OBTENIR LES INFOS VIDÉO ---
def get_video_info(url):
    """
    Récupère les informations de la vidéo
    """
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
            st.error("❌ Impossible de récupérer les informations de la vidéo")
            return None
            
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout lors de la récupération des informations")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None

# --- FONCTION DE TÉLÉCHARGEMENT ---
def download_media(url, format_choice):
    """
    Téléchargement avec gestion d'erreurs
    """
    try:
        clean_url = clean_youtube_url(url)
        temp_dir = tempfile.mkdtemp()
        
        st.info("🔄 Préparation du téléchargement...")
        
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
        else:  # MP3
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp',
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--ignore-errors',
                '--no-warnings',
                '-o', output_template,
                clean_url
            ]
        
        st.info("📥 Téléchargement en cours...")
        
        process = subprocess.run(command, capture_output=True, text=True, timeout=300)
        
        if process.returncode == 0:
            st.success("✅ Téléchargement terminé!")
            
            # Chercher le fichier
            for file in os.listdir(temp_dir):
                if file.endswith(('.mp4', '.mp3', '.webm', '.m4a')):
                    file_path = os.path.join(temp_dir, file)
                    mime_type = "video/mp4" if format_choice == "MP4 (Vidéo)" else "audio/mpeg"
                    return file_path, file, mime_type
            
            raise Exception("Aucun fichier trouvé après téléchargement")
        else:
            raise Exception(f"Échec du téléchargement: {process.stderr}")
            
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout lors du téléchargement")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None, None, None

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
theme = st.sidebar.selectbox("🎨 Thème", ["Cyberpunk", "Clair"])
load_css(theme)

if not st.session_state.title_typed:
    st.markdown('<h1 class="typing-title">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.title_typed = True
    st.rerun()
else:
    st.markdown('<h1 class="glitch" data-text="CYBER-STREAM TERMINAL">CYBER-STREAM TERMINAL</h1>', unsafe_allow_html=True)

# Vérification des dépendances
st.sidebar.title("🔧 Dépendances")

try:
    result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        st.sidebar.success(f"✅ yt-dlp: {result.stdout.strip()}")
    else:
        st.sidebar.error("❌ yt-dlp: Erreur")
except:
    st.sidebar.error("❌ yt-dlp: Non disponible")

st.sidebar.markdown("---")

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
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬇️ Télécharger", use_container_width=True):
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
                        os.unlink(file_path)
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

# Mode démonstration
if st.session_state.search_results and len(st.session_state.search_results) > 0:
    first_result = st.session_state.search_results[0]
    if "démo" in first_result.get('title', '').lower() or "demo" in first_result.get('title', '').lower():
        st.warning("🔄 Mode démonstration activé - Les résultats sont simulés pour tester l'interface")
