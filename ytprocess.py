import os
import hashlib
import logging
import yt_dlp
from tqdm import tqdm

logger = logging.getLogger(__name__)

OUTPUT_DIR = "MEDIA/Audio"

def get_channel_infos(channel_identifier):
    """
    Récupère le nom et l'avatar d'une chaîne.
    Retourne (nom, url_avatar, id_chaine).
    """
    # Si c'est juste un ID, on reconstruit l'URL
    url = f"https://www.youtube.com/channel/{channel_identifier}" if channel_identifier.startswith("UC") else channel_identifier

    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlist_items': '0',
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            name = info.get('channel', info.get('uploader', 'Inconnu'))
            ch_id = info.get('channel_id', info.get('id')) 
            
            thumbnails = info.get('thumbnails', [])
            avatar = thumbnails[-1]['url'] if thumbnails else "https://robohash.org/default"
            
            return name, avatar, ch_id
            
    except Exception as e:
        logger.warning(f"⚠️ Erreur métadonnées chaîne pour {channel_identifier} : {e}")
        return channel_identifier, f"https://robohash.org/{channel_identifier}", channel_identifier

def format_duration(seconds):
    """Convertit des secondes (int) en string 'MM:SS' ou 'HH:MM:SS'."""
    if not seconds:
        return "00:00"
    
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def download_and_extract_metadata(url):
    """
    Télécharge l'audio via yt-dlp et extrait les métadonnées.
    Retourne: (author, title, description, file_hash, thumb_url, channel_img, duration_str)
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pbar = None

    def progress_hook(d):
        nonlocal pbar
        if d['status'] == 'downloading':
            if pbar is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                logger.info("🔨 Téléchargement et conversion...")
                pbar = tqdm(total=total, unit='B', unit_scale=True, desc="🎵 Téléchargement", colour="green")
            
            downloaded = d.get('downloaded_bytes', 0)
            if pbar:
                pbar.update(downloaded - pbar.n)
                
        elif d['status'] == 'finished':
            if pbar:
                pbar.close()
                pbar = None
            print("Conversion audio en cours... 🔨")

    try:
        # 1. Extraction des métadonnées
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl_info:
            info = ydl_info.extract_info(url, download=False)
            
            original_title = info.get("title", "audio_sans_titre")
            description = info.get("description", "")
            author = info.get("uploader", "Inconnu")
            channel_url = info.get("channel_url")
            thumbnail_url = info.get("thumbnail", "Pas de miniature")
            duration_sec = info.get("duration", 0)
            duration_str = format_duration(duration_sec)

            channel_image_url = info.get("channel_thumbnail") or info.get("uploader_avatar")
            if not channel_image_url and channel_url:
                _, channel_image_url, _ = get_channel_infos(channel_url)

        # 2. Préparation du fichier
        filename_hash = hashlib.md5(original_title.encode('utf-8')).hexdigest()
        output_template = os.path.join(OUTPUT_DIR, f"{filename_hash}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }],
        }

        # 3. Téléchargement
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return author, original_title, description, filename_hash, thumbnail_url, channel_image_url, duration_str

    except Exception as e:
        if pbar:
            pbar.close()
        logger.error(f"Erreur yt_dlp : {e}")
        raise e