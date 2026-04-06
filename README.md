# ARCHIPELAGO HOOKER

Ce bot surveille les nouveaux forks du dépôt [Archipelago](https://github.com/ArchipelagoMW/Archipelago) et envoie une notification sur Discord via webhook pour avertir des nouveaux fork.
Afin de remplir sa mission, une execution régulière doit être mise en place.


## Installation

1. Cloner le dépôt github.
2. Créer un environnement virtuel : `python3 -m venv venv`
3. Activer l'environnement : `source venv/bin/activate`
4. Installer les dépendances requises : `pip install -r requirements.txt`


## Configuration

Créez un fichier `.env` à la racine du projet avec le contenu suivant :

```env
REPO="URL_DU_REPO_ARCHIPELAGO"
DISCORD_WEBHOOK_URL=VOTRE_WEBHOOK_DISCORD
DB_FILE="NOM_DU_FICHIER_DB_JSON"
GITHUB_TOKEN=VOTRE_TOKEN_GITHUB (Optionnel mais recommandé)
```

Le fichier `forks_db.json` sera créé automatiquement lors du premier lancement pour stocker l'état actuel des forks.
