# Charger les variables depuis le fichier .env
ifneq ("$(wildcard .env)","")
    include .env
    export $(shell sed 's/=.*//' .env)
endif

PYTHON = ./venv/bin/python3
# On récupère les variables du .env ou on met des valeurs par défaut
DB_USER_ENV = $(DB_USER)
DB_PASS_ENV = $(DB_PASSWORD)
DB_NAME_ENV = $(DB_NAME)

.PHONY: run db-status help

run:
	@echo "🚀 Lancement du moniteur..."
	@$(PYTHON) monitor.py

db-status:
	@echo "📊 Statistiques de la base MariaDB :"
	@mysql -u$(DB_USER_ENV) -p'$(DB_PASS_ENV)' -e "USE $(DB_NAME_ENV); SELECT COUNT(*) as total_forks FROM forks;"
	@echo "\n🕒 5 derniers forks détectés :"
	@mysql -u$(DB_USER_ENV) -p'$(DB_PASS_ENV)' -e "USE $(DB_NAME_ENV); SELECT full_name, detected_at FROM forks ORDER BY detected_at DESC LIMIT 5;"

help:
	@echo "Usage: make [run|db-status]"
