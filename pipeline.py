import os
import shutil
import logging
import readxml
import ytprocess
import pam
import s3
import rss_manager

logger = logging.getLogger("Pipeline")

PROCESSED_FOLDER = "MEDIA/Processed-xml"
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def process_single_url(url, source_type="RSS"):
    """
    Pipeline complet pour une URL : Download -> PAM API -> S3 Upload.
    """
    try:
        logger.info(f"--- 🚀 Démarrage traitement ({source_type}) ---")
        
        # 1. Download & Metadata
        # Note: on unpack le tuple retourné par ytprocess
        (
            author, 
            title, 
            description, 
            file_hash, 
            thumb, 
            channel_img, 
            duration
        ) = ytprocess.download_and_extract_metadata(url)
        
        logger.info(f"✅ Fichier téléchargé : {file_hash}.mp3 ({duration})")

        # Enrichissement description
        enriched_description = (
            f"{description}\n\n"
            f"--- MEDIA ASSETS ---\n"
            f"⏱️ Durée : {duration}\n"
            f"🖼️ Miniature Video (HD) : {thumb}\n"
            f"👤 Image Chaîne : {channel_img}"
        )

        # 2. Création Asset PAM
        pam_asset_id = pam.create_asset(title, author, enriched_description)
        logger.info(f"🆔 Asset PAM créé : {pam_asset_id}")

        # 3. Upload S3
        s3.upload_to_s3(file_hash, pam_asset_id)
        
        return True, title

    except Exception as e:
        logger.error(f"❌ Echec traitement : {e}")
        return False, str(e)

def run_batch_xml(xml_folder, is_running_callback=None):
    """
    Scanne le dossier XML et lance le traitement pour chaque fichier.
    """
    count = 0
    if not os.path.exists(xml_folder):
        return 0

    for filename in os.listdir(xml_folder):
        # Vérification interruption utilisateur
        if is_running_callback and not is_running_callback():
            logger.info("🛑 Arrêt immédiat demandé (XML Loop).")
            break

        if not filename.lower().endswith(".xml"):
            continue
        
        xml_path = os.path.join(xml_folder, filename)
        logger.info(f"📂 Traitement XML : {filename}")
        
        try:
            uri = readxml.extract_uri_from_xml(xml_path)
            success, _ = process_single_url(uri, source_type="XML")
            
            if success:
                dest_path = os.path.join(PROCESSED_FOLDER, filename)
                shutil.move(xml_path, dest_path)
                logger.info(f"📦 Archivé : {filename}")
                count += 1
        except Exception as e:
            logger.error(f"Erreur sur {filename}: {e}")
            
    return count

def run_rss_check(channels, limit=15, is_running_callback=None):
    """
    Vérifie les flux RSS pour la liste de chaînes fournie.
    """
    count = 0
    for channel_id in channels:
        # Vérification interruption utilisateur
        if is_running_callback and not is_running_callback():
            logger.info("🛑 Arrêt immédiat demandé (RSS Channel Loop).")
            break

        logger.info(f"📡 Scan chaîne : {channel_id} (Limit: {limit})")
        
        new_videos = rss_manager.check_rss_feed(channel_id, limit=limit)
        
        for vid in new_videos:
            if is_running_callback and not is_running_callback():
                logger.info("🛑 Arrêt immédiat demandé (RSS Video Loop).")
                break

            success, _ = process_single_url(vid['link'], source_type="RSS")
            if success:
                rss_manager.add_to_history(channel_id, vid)
                count += 1
    return count