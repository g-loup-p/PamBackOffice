import os
import logging
import boto3
from botocore.client import Config

logger = logging.getLogger(__name__)

# CONSTANTES S3
# TODO: Idéalement, charger ces valeurs depuis des variables d'environnement pour la sécurité
HOST = "s3.fr-par.scw.cloud"
KEY_ID = "SCWGHGQW6RA7GYG0793C"
KEY_SECRET = "ce8c7900-b8fa-459c-af5a-ce7f7b7d6ef9"
BUCKET = "pam-ina"
REGION = "fr-par"
PREFIX = "audio"

def upload_to_s3(file_title, asset_id):
    """
    Upload un fichier MP3 local vers un bucket S3 compatible.
    Supprime le fichier local après succès.
    """
    try:
        s3_client = boto3.client(
            "s3",
            region_name=REGION,
            endpoint_url=f"https://{HOST}",
            aws_access_key_id=KEY_ID,
            aws_secret_access_key=KEY_SECRET,
            config=Config(signature_version="s3v4")
        )

        local_file_path = f"MEDIA/Audio/{file_title}.mp3"
        s3_key = f"{PREFIX}/{asset_id}.mp3"

        s3_client.upload_file(local_file_path, BUCKET, s3_key)
        logger.info(f"🚀 Upload terminé : {s3_key}")

        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logger.info("🗑️  Fichier local nettoyé")

    except Exception as e:
        logger.error(f"🔥 Erreur S3 : {e}")
        raise e