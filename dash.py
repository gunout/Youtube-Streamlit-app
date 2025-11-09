import streamlit as st
import os
import tempfile
import subprocess
import time
import math
import json
import re

# --- Configuration ---
st.set_page_config(
    page_title="CYBER-STREAM Terminal",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State ---
if 'title_typed' not in st.session_state:
    st.session_state.title_typed = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'selected_video_url' not in st.session_state:
    st.session_state.selected_video_url = None
if 'selected_video_data' not in st.session_state:
    st.session_state.selected_video_data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 0

# --- CSS (identique à avant) ---
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

# --- Fonctions optimisées ---

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

def clean_youtube_url(url):
    """Nettoie l'URL YouTube pour enlever les paramètres inutiles"""
    video_id = get_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def format_duration(seconds):
    """Formate la durée en secondes"""
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

# --- FONCTION DE RECHERCHE OPTIMISÉE ---
@st.cache_data(ttl=3600, show_spinner="Recherche en cours...")
def search_youtube(query, limit=15):
    """
    Recherche optimisée avec gestion des erreurs améliorée
    """
    try:
        # Nettoyer la requête
        clean_query = query.strip()
        if not clean_query:
            return []
            
        search_command = [
            'yt-dlp',
            f'ytsearch{limit}:"{clean_query}"',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--quiet',
            '--socket-timeout', '30',
            '--source-timeout', '30'
        ]
        
        result = subprocess.run(
            search_command, 
            capture_output=True, 
            text=True, 
            check=True, 
            timeout=45  # Timeout augmenté à 45 secondes
        )
        
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
        
        return videos if videos else get_demo_results(query)
        
    except subprocess.TimeoutExpired:
        st.warning("⏱️ Recherche trop longue, utilisation des résultats de démonstration")
        return get_demo_results(query)
    except subprocess.CalledProcessError as e:
        st.warning(f"⚠️ Recherche échouée, mode démonstration activé: {e.stderr[:100]}...")
        return get_demo_results(query)
    except Exception as e:
        st.warning(f"⚠️ Erreur de recherche: {str(e)}")
        return get_demo_results(query)

def get_demo_results(query):
    """Résultats de démonstration pour tests"""
    return [
        {
            'id': 'dQw4w9WgXcQ',
            'title': f'Demo: {query} - Résultat 1',
            'link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'channel': {'name': 'Chaîne Démo'},
            'duration': {'text': '3:45'},
            'viewCount': {'text': '1,234,567'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'}]
        },
        {
            'id': 'kJQP7kiw5Fk', 
            'title': f'Demo: {query} - Résultat 2',
            'link': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'channel': {'name': 'Chaîne Test'},
            'duration': {'text': '4:20'},
            'viewCount': {'text': '987,654'},
            'thumbnail': [{'url': 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg'}]
        }
    ]

# --- FONCTION INFO VIDÉO OPTIMISÉE ---
def get_video_info(url):
    """
    Récupère les infos vidéo avec timeout étendu et retry
    """
    # Nettoyer l'URL d'abord
    clean_url = clean_youtube_url(url)
    
    for attempt in range(2):  # 2 tentatives
        try:
            command = [
                'yt-dlp',
                '--dump-json',
                '--no-download',
                '--no-warnings',
                '--quiet',
                '--socket-timeout', '45',
                '--source-timeout', '45',
                clean_url
            ]
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=60  # Timeout à 60 secondes
            )
            
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
            
        except subprocess.TimeoutExpired:
            if attempt == 0:  # Première tentative échouée
                st.warning("⌛ Timeout, nouvelle tentative...")
                time.sleep(2)
                continue
            else:
                st.error("⏱️ Délai d'attente dépassé pour cette vidéo")
                return None
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement: {str(e)}")
            return None
    
    return None

# --- FONCTION TÉLÉCHARGEMENT OPTIMISÉE ---
def download_media(url, format_choice):
    """Téléchargement avec gestion d'erreurs améliorée"""
    try:
        # Nettoyer l'URL
        clean_url = clean_youtube_url(url)
        
        temp_dir = tempfile.mkdtemp()
        progress_placeholder = st.empty()
        
        progress_placeholder.info("🔄 Préparation du téléchargement...")
        
        if format_choice == "MP4 (Vidéo)":
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp', 
                '-f', 'best[height<=720]',
                '--merge-output-format', 'mp4',
                '--socket-timeout', '60',
                '--source-timeout', '60',
                '--retries', '3',
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
                '--socket-timeout', '60',
                '--source-timeout', '60',
                '--retries', '3',
                '-o', output_template,
                clean_url
            ]
        
        progress_placeholder.info("📥 Téléchargement en cours...")
        
        # Exécution avec timeout long
        process = subprocess.run(command, capture_output=True, text=True, timeout=300, check=True)
        
        progress_placeholder.success("✅ Téléchargement terminé!")
        
        # Chercher le fichier
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mp3')):
                file_path = os.path.join(temp_dir, file)
                mime_type = "video/mp4" if format_choice == "MP4 (Vidéo)" else "audio/mpeg"
                return file_path, file, mime_type
        
        raise Exception("Fichier non trouvé")
        
    except subprocess.TimeoutExpired:
        st.error("⏱️ Timeout lors du téléchargement")
        return None, None, None
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Erreur de téléchargement: {e.stderr[:200]}...")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None, None, None
    finally:
        progress_placeholder.empty()

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

st.sidebar.title("🎛️ Contrôles")
search_query = st.sidebar.text_input("🔍 Rechercher:", key="search_input")
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
        with st.spinner("Recherche..."):
            results = search_youtube(search_query)
            st.session_state.search_results = results
            st.session_state.total_pages = max(1, math.ceil(len(results) / 3))
            st.session_state.current_page = 1
            st.session_state.selected_video_url = None
            
        st.sidebar.info(f"🔍 {len(results)} résultats trouvés")
    else:
        st.sidebar.warning("⚠️ Entrez un terme de recherche")

# Affichage résultats
if st.session_state.search_results:
    st.subheader("📺 Résultats")
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
        
        if st.button("⬇️ Télécharger"):
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
                    mime=mime_type
                )
                
                # Nettoyage
                try:
                    os.unlink(file_path)
                    os.rmdir(os.path.dirname(file_path))
                except:
                    pass

        if st.button("🗑️ Effacer la sélection"):
            st.session_state.selected_video_url = None
            st.session_state.selected_video_data = None
            st.rerun()

elif not st.session_state.search_results:
    st.info("🔍 Lancez une recherche ou collez une URL YouTube")

# Vérification yt-dlp
st.sidebar.markdown("---")
if st.sidebar.button("🔧 Vérifier yt-dlp"):
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
        st.sidebar.success(f"✅ yt-dlp: {result.stdout.strip()}")
    except:
        st.sidebar.error("❌ yt-dlp non disponible")
