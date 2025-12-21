import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def extract_uri_from_xml(file_path):
    """
    Lit un fichier XML et extrait le contenu de la balise <uri>.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Recherche de la balise URI
        uri_node = root.find('uri')
        
        if uri_node is None or not uri_node.text:
            raise ValueError("Balise <uri> manquante ou vide dans le XML")

        uri = uri_node.text.strip()
        logger.info(f"🔍 URI trouvée : {uri}")
        return uri

    except Exception as e:
        logger.error(f"💥 Erreur de lecture XML sur {file_path} : {e}")
        raise e