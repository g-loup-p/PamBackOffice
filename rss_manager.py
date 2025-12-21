import json
import os
import logging
import time
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

HISTORY_FILE = "processed_history.json"

def load_history():
    """Charge l'historique et gère la migration legacy."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            logger.warning("⚠️ Migration de l'historique vers le format structuré.")
            return {"_LEGACY": [{"id": vid} for vid in data]}
            
        return data
    except Exception as e:
        logger.error(f"Erreur chargement historique: {e}")
        return {}

def save_history_data(data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde historique: {e}")

def add_to_history(channel_id, video_data):
    """Ajoute une vidéo à l'historique d'une chaîne spécifique."""
    history = load_history()
    
    if channel_id not in history:
        history[channel_id] = []
    
    existing_ids = [v["id"] for v in history[channel_id]]
    if video_data["id"] not in existing_ids:
        history[channel_id].append({
            "id": video_data["id"],
            "title": video_data.get("title", "Sans titre"),
            "thumb": video_data.get("thumb", ""),
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_history_data(history)

def remove_video_from_history(channel_id, video_id):
    """Supprime une vidéo de l'historique pour permettre un re-téléchargement."""
    history = load_history()
    if channel_id in history:
        original_len = len(history[channel_id])
        history[channel_id] = [v for v in history[channel_id] if v["id"] != video_id]
        if len(history[channel_id]) < original_len:
            save_history_data(history)
            return True
    return False

def clear_channel_history(channel_id):
    history = load_history()
    if channel_id in history:
        del history[channel_id]
        save_history_data(history)

def get_channel_history(channel_id):
    history = load_history()
    return history.get(channel_id, [])

def check_rss_feed(channel_id, limit=15):
    """
    Récupère les dernières vidéos via RSS.
    """
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    new_videos = []
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Erreur RSS {channel_id}: Code {response.status_code}")
            return []

        root = ET.fromstring(response.content)
        ns = {
            'yt': 'http://www.youtube.com/xml/schemas/2015', 
            'media': 'http://search.yahoo.com/mrss/', 
            'atom': 'http://www.w3.org/2005/Atom'
        }

        history = load_history()
        
        # Liste des IDs déjà traités
        processed_ids = []
        if channel_id in history:
            processed_ids = [v["id"] for v in history[channel_id]]
        if "_LEGACY" in history:
            processed_ids += [v["id"] for v in history["_LEGACY"]]

        all_entries = root.findall('atom:entry', ns)
        entries_to_process = all_entries[:limit]

        for entry in entries_to_process:
            video_id = entry.find('yt:videoId', ns).text
            link = entry.find('atom:link', ns).attrib['href']
            title = entry.find('atom:title', ns).text
            
            thumb = ""
            media_group = entry.find('media:group', ns)
            if media_group is not None:
                media_thumb = media_group.find('media:thumbnail', ns)
                if media_thumb is not None:
                    thumb = media_thumb.attrib['url']
            
            if video_id not in processed_ids:
                logger.info(f"🆕 Nouvelle vidéo détectée : {title}")
                new_videos.append({
                    "id": video_id,
                    "link": link,
                    "title": title,
                    "thumb": thumb
                })
            
    except Exception as e:
        logger.error(f"Erreur parsing RSS pour {channel_id}: {e}")

    return new_videos