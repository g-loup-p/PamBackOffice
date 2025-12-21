# Pam BackOffice

Pam B.O. est un outils permettant de gérer le téléchargement de média vers le PAM interne (LP SAN 2025)
![Logo](https://pamtube.netlify.app/Wiki/logo_light.svg)

## Fonctionalitées:

Le logiciel permet d'acquérir des médias depuis Youtube de différentes manières:
- Depuis l'url d'une vidéo Youtube. (**youtube.com/watch?v=...** ou **youtu.be/...**)
- Depuis des fichiers XML se trouvant dans un dossier.
- De manière plus automatique en suivants les nouvelles vidéos d'une chaîne Youtube.

Quelques fonctionnalitées suplémentaires:
* Suppervision par affichage des logs.
* Mode automatique (Système d'abonnement a une chaîne Youtube et détection automatique de nouveaux XML), cette fonctionnalité permet de laisser le programme tourner tout seul.
* Interface de gestion des abonnements
* Paramètres de gestion:
    * Du temps de raffraichissement du mode automatique (en secondes)
    * Définition du dossier où se trouve les fichiers XML
    * Profondeur de téléchargement des vidéos des chaînes Youtube (ex: 15 dernières vidéos, ou les 5 dernières...)
* Mode Light/Dark
* Accès direct a la platefrome  [PamTube](https://pamtube.netlify.app)

## Installation:

Pour installer le programme, téléchargez la dernière version disponible.

- Décompressez le fichier Zip
- Assurez vous d'avoir Python 3.14.2 d'installé sur votre machine et d'avoir la liste des dépendances du programmes 'requirements.txt' installé aussi.
- Utilisez l'invite de commande, placez vous dans le dossier du programme "PamBackOffice" et executez la commande suivante:
```bash
  cd PamBackOffice
  python main_ui.py
```

⚠️ Ce programme à été développé pour la partie interface avec [Flet](https://flet.dev/), l'interface Flet à été développé sous Windows, il n'y a pas eu de test de compatibilité de l'interface pour d'autres systèmes d'exploitation, des bugs pourraient donc surevenir.

▶️ Besoin d'aide sur l'utilisation du logiciel, consultez le [Wiki](https://github.com/g-loup-p/PamBackOffice/wiki)
