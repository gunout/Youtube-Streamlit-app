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

# --- FONCTION DE TÉLÉCHARGEMENT CORRIGÉE POUR MP3 ---
def download_media(url, format_choice):
    """
    Téléchargement avec correction spécifique pour MP3
    """
    try:
        clean_url = clean_youtube_url(url)
        temp_dir = tempfile.mkdtemp()
        
        st.info("🔄 Configuration du téléchargement...")
        
        if format_choice == "MP4 (Vidéo)":
            # Pour MP4: formats natifs qui ne nécessitent pas FFmpeg
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
        else:  # MP3 - CORRECTION ICI
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            if st.session_state.ffmpeg_available:
                # Avec FFmpeg: conversion en MP3
                command = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '--ignore-errors',
                    '--no-warnings',
                    '-o', output_template,
                    clean_url
                ]
            else:
                # Sans FFmpeg: utiliser le meilleur format audio disponible
                st.warning("⚠️ FFmpeg non disponible - Téléchargement du meilleur format audio natif")
                command = [
                    'yt-dlp',
                    '-x',
                    '--ignore-errors',
                    '--no-warnings',
                    '-o', output_template,
                    clean_url
                ]
        
        st.info("📥 Téléchargement en cours...")
        
        # Exécution avec timeout long
        process = subprocess.run(command, capture_output=True, text=True, timeout=300)
        
        if process.returncode == 0:
            st.success("✅ Téléchargement terminé!")
            
            # Chercher le fichier téléchargé
            downloaded_file = None
            for file in os.listdir(temp_dir):
                file_lower = file.lower()
                if format_choice == "MP4 (Vidéo)":
                    if file_lower.endswith(('.mp4', '.webm', '.mkv')):
                        downloaded_file = os.path.join(temp_dir, file)
                        # Renommer en .mp4 si nécessaire
                        if not downloaded_file.endswith('.mp4'):
                            new_file = os.path.splitext(downloaded_file)[0] + '.mp4'
                            os.rename(downloaded_file, new_file)
                            downloaded_file = new_file
                        mime_type = "video/mp4"
                        break
                else:  # MP3
                    # Accepter différents formats audio
                    if file_lower.endswith(('.mp3', '.m4a', '.ogg', '.opus', '.wav')):
                        downloaded_file = os.path.join(temp_dir, file)
                        # FORCER le renommage en .mp3 pour MP3
                        if not downloaded_file.endswith('.mp3'):
                            new_file = os.path.splitext(downloaded_file)[0] + '.mp3'
                            os.rename(downloaded_file, new_file)
                            downloaded_file = new_file
                        mime_type = "audio/mpeg"
                        break
            
            if downloaded_file:
                file_name = os.path.basename(downloaded_file)
                return downloaded_file, file_name, mime_type
            else:
                # Si aucun fichier trouvé, essayer une méthode alternative
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
    Méthode de fallback pour le téléchargement - SPÉCIALEMENT POUR MP3
    """
    try:
        st.info("🔄 Utilisation de la méthode de secours...")
        
        if format_choice == "MP3 (Audio)":
            # Méthode spécifique pour MP3 avec extraction audio
            output_template = os.path.join(temp_dir, "%(title).100s.%(ext)s")
            command = [
                'yt-dlp',
                '-f', 'bestaudio',  # Spécifiquement le meilleur audio
                '--ignore-errors',
                '--no-warnings',
                '-o', output_template,
                url
            ]
            
            process = subprocess.run(command, capture_output=True, text=True, timeout=300)
            
            if process.returncode == 0:
                # Chercher n'importe quel fichier audio
                for file in os.listdir(temp_dir):
                    if not file.endswith('.part'):
                        file_path = os.path.join(temp_dir, file)
                        # RENOMMER FORCÉMENT EN .mp3
                        if not file_path.endswith('.mp3'):
                            new_path = os.path.splitext(file_path)[0] + '.mp3'
                            os.rename(file_path, new_path)
                            file_path = new_path
                        return file_path, os.path.basename(file_path), "audio/mpeg"
        
        raise Exception("Aucun fichier téléchargé trouvé avec la méthode de secours")
        
    except Exception as e:
        st.error(f"❌ Méthode de secours échouée: {str(e)}")
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
    st.session_state.ffmpeg_available = check_ffmpeg()
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
    st.sidebar.warning("⚠️ FFmpeg: Non disponible - Conversion MP3 limitée")

st.sidebar.markdown("---")

# Avertissement sur les limitations MP3
if not st.session_state.ffmpeg_available:
    st.sidebar.markdown("""
    <div class='warning-box'>
    <strong>⚠️ MP3 sans FFmpeg</strong><br>
    Sans FFmpeg, les MP3 seront des fichiers audio natifs renommés.
    Pour une vraie conversion MP3, installez FFmpeg.
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
        
        # Avertissement spécifique pour MP3
        if download_format == "MP3 (Audio)" and not st.session_state.ffmpeg_available:
            st.warning("""
            **⚠️ Conversion MP3 limitée:** 
            Sans FFmpeg, le fichier sera un format audio natif (généralement m4a) renommé en .mp3.
            Pour une vraie conversion MP3, installez FFmpeg.
            """)
        
        if st.button("⬇️ Télécharger"):
            file_path, file_name, mime_type = download_media(
                st.session_state.selected_video_url, 
                download_format
            )
            if file_path:
                with open(file_path, "rb") as f:
                    bytes_data = f.read()
                
                # Afficher le bouton de téléchargement
                st.download_button(
                    label=f"💾 Télécharger {file_name}",
                    data=bytes_data,
                    file_name=file_name,
                    mime=mime_type
                )
                
                # Nettoyage des fichiers temporaires
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                    if os.path.exists(os.path.dirname(file_path)):
                        os.rmdir(os.path.dirname(file_path))
                except:
                    pass

        if st.button("🗑️ Effacer la sélection"):
            st.session_state.selected_video_url = None
            st.session_state.selected_video_data = None
            st.rerun()

elif not st.session_state.search_results:
    st.info("🔍 Lancez une recherche ou collez une URL YouTube")

# Instructions d'installation FFmpeg
with st.sidebar.expander("📋 Installer FFmpeg"):
    st.markdown("""
    **Pour une conversion MP3 complète:**
    
    ```bash
    # Windows (avec chocolatey):
    choco install ffmpeg
    
    # Ubuntu/Debian:
    sudo apt update && sudo apt install ffmpeg
    
    # Mac (avec brew):
    brew install ffmpeg
    
    # Ou avec pip (limité):
    pip install ffmpeg-python
    ```
    
    **Actuellement:** 
    - MP4: ✅ Fonctionne toujours
    - MP3: ⚠️ Format natif renommé (sans FFmpeg)
    """)
