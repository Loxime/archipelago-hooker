import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
REPO = os.getenv("REPO")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_FILE = os.getenv("DB_FILE")

def get_all_forks():
    forks = []
    page = 1
    while True:
        # On récupère par page de 100 
        url = f"https://api.github.com/repos/{REPO}/forks?per_page=100&page={page}"
        response = requests.get(url)
        data = response.json()
        
        if not data or page > 10: # Sécurité pour ne pas boucler à l'infini
            break
            
        forks.extend([f['full_name'] for f in data])
        page += 1
    return set(forks)

def send_discord_alert(repo_name):
    payload = {
        "content": f"🚀 **Nouveau Fork détecté !**\nLe dépôt `{repo_name}` vient de forker Archipelago.",
        "username": "Archipelago Watcher"
    }
    requests.post(WEBHOOK_URL, json=payload)

def main():
    # 1. Charger l'ancienne base
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            old_forks = set(json.load(f))
    else:
        print("Première exécution : Initialisation de la base de données...")
        old_forks = None

    # 2. Récupérer les forks actuels
    current_forks = get_all_forks()

    # 3. Comparer
    if old_forks is not None:
        new_forks = current_forks - old_forks
        for fork in new_forks:
            print(f"Alerte : {fork}")
            send_discord_alert(fork)
    
    # 4. Sauvegarder la nouvelle base
    with open(DB_FILE, "w") as f:
        json.dump(list(current_forks), f)

if __name__ == "__main__":
    main()
