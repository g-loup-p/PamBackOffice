import logging
import requests

logger = logging.getLogger(__name__)

API_URL = "https://pam.lpsan-2025.fr/assets"
API_TOKEN = "Bearer super-secure-token"  # À sécuriser via config/env

def create_asset(title, author, body):
    """
    Crée un asset via l'API PAM et retourne son ID.
    """
    payload = {
        "title": title,
        "author": author,
        "body": body
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": API_TOKEN
    }

    logger.info(f"📡 Connexion à l'API PAM pour : {title[:30]}...")

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        asset_id = data.get("id")

        if not asset_id:
            raise ValueError("L'API a répondu mais ne contient pas d'ID.")

        logger.info(f"✨ Asset créé avec succès ! ID : {asset_id}")
        return asset_id

    except requests.exceptions.RequestException as e:
        logger.error(f"💀 Erreur de communication API PAM : {e}")
        if response is not None:
             logger.error(f"Contenu réponse serveur : {response.text}")
        raise e
        
    except Exception as e:
        logger.error(f"💀 Erreur inattendue dans PAM : {e}")
        raise e