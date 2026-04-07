import mariadb
import requests
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REPO = os.getenv("REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

MAX_FORKS_TO_SCAN = 20


def get_db_connection():
    try:
        return mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=3306,
            database=os.getenv("DB_NAME")
        )
    except mariadb.Error as e:
        print(f"DB error: {e}")
        sys.exit(1)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS forks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) UNIQUE,
            description TEXT,
            html_url VARCHAR(255),
            readme_url VARCHAR(255),
            announced TINYINT(1) DEFAULT 0,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            repo_full_name VARCHAR(255),
            tag_name VARCHAR(255),
            tag_commit_sha VARCHAR(255),
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(repo_full_name, tag_name)
        )
    """)

    conn.commit()
    return conn


def get_forks():
    forks = []
    page = 1

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    while True:
        url = f"https://api.github.com/repos/{REPO}/forks?per_page=100&page={page}"
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            break

        data = r.json()
        if not data:
            break

        forks.extend(data)
        page += 1
        time.sleep(0.2)

    return forks


def get_tags(repo):
    url = f"https://api.github.com/repos/{repo}/tags"

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return []

    return r.json()


def send_new_repo(repo, desc, url):
    payload = {
        "username": "Archipelago Watcher",
        "embeds": [{
            "title": "🚀 Nouveau repository détecté",
            "color": 5763719,
            "fields": [
                {"name": "📦 Repo", "value": f"`{repo}`", "inline": False},
                {"name": "📝 Description", "value": desc or "Aucune", "inline": False},
                {"name": "🔗 Lien", "value": url, "inline": False}
            ],
            "footer": {"text": datetime.now().strftime('%d/%m/%Y %H:%M')}
        }]
    }

    requests.post(WEBHOOK_URL, json=payload)


def send_repo_update(repo, tag, url):
    payload = {
        "username": "Archipelago Watcher",
        "embeds": [{
            "title": "🔄 Nouvelle information de repository",
            "color": 16766720,
            "fields": [
                {"name": "📦 Repo", "value": f"`{repo}`", "inline": False},
                {"name": "🏷️ Nouveau tag", "value": tag, "inline": True},
                {"name": "🔗 Release", "value": url, "inline": False}
            ],
            "footer": {"text": datetime.now().strftime('%d/%m/%Y %H:%M')}
        }]
    }

    requests.post(WEBHOOK_URL, json=payload)


def main():
    conn = init_db()
    cur = conn.cursor()

    forks = get_forks()

    for f in forks[:MAX_FORKS_TO_SCAN]:
        full_name = f["full_name"]
        tags = get_tags(full_name)
        cur.execute("SELECT id, announced FROM forks WHERE full_name = ?", (full_name,))
        row = cur.fetchone()

        if row is None:
            # Nouveau fork en base
            cur.execute("""
                INSERT INTO forks (full_name, description, html_url, readme_url, announced)
                VALUES (?, ?, ?, ?, 0)
            """, (
                full_name,
                f.get("description"),
                f["html_url"],
                f["html_url"] + "/blob/" + f.get("default_branch", "main") + "/README.md"
            ))
            conn.commit()

            announced = 0
        else:
            announced = row[1]
        for tag in tags:
            tag_name = tag["name"]
            sha = tag["commit"]["sha"]

            cur.execute("""
                SELECT id FROM tags WHERE repo_full_name = ? AND tag_name = ?
            """, (full_name, tag_name))

            is_new_tag = cur.fetchone() is None

            if is_new_tag:
                cur.execute("""
                    INSERT INTO tags (repo_full_name, tag_name, tag_commit_sha)
                    VALUES (?, ?, ?)
                """, (full_name, tag_name, sha))

                conn.commit()
                send_repo_update(
                    full_name,
                    tag_name,
                    f"{f['html_url']}/releases/tag/{tag_name}"
                )
                if announced == 0:
                    send_new_repo(
                        full_name,
                        f.get("description"),
                        f["html_url"]
                    )

                    cur.execute("""
                        UPDATE forks SET announced = 1 WHERE full_name = ?
                    """, (full_name,))
                    conn.commit()

    conn.close()


if __name__ == "__main__":
    main()