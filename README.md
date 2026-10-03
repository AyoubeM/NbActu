# 🏀 NBA Actu • Bot Discord & Dashboard Web

Application Python 100% autosuffisante et sans frais d'hébergement.  
Chaque matin à **07h30 (heure française)** :
1. Récupère tous les matchs de la nuit passée via l'API officielle NBA / ESPN.
2. Identifie les diffuseurs officiels en France (**beIN SPORTS**, **Amazon Prime Video**, **NBA League Pass**).
3. Trouve les résumés vidéo officiels (priorité aux résumés en français, bascule immédiate sur les résumés officiels NBA US 10 min en haute définition).
4. Analyse la dynamique et la forme des équipes (séries de victoires/défaites, L10, classement).
5. Compile les statistiques détaillées de **tous les joueurs de la ligue** (Points, Rebonds, Passes, %, +/-, GameScore, MVP de la nuit et focus spécial Français 🇫🇷).
6. Publie automatiquement le **Dashboard Web interactif** sur **GitHub Pages**.
7. Envoie le récapitulatif sur **Discord** avec protection **Anti-Spoiler**.

---

## 📸 Aperçu des Fonctionnalités

* 🛡️ **Mode Anti-Spoiler :** Les scores sont masqués sur Discord (`|| 108 - 114 ||`) et floutés sur le web pour préserver le suspense avant de visionner le résumé vidéo.
* 📺 **Détection des Diffuseurs FR :** Affichage clair des antennes (*beIN SPORTS 1*, *Prime Video*, *NBA League Pass*).
* 🎬 **Résumés Vidéo :** Liens directs pour lancer les vidéos immédiatement.
* 📊 **Dashboard Web Moderne :** Consultation de l'intégralité des boxscores de tous les joueurs de chaque équipe, recherche en direct, classement des conférences et suivi des joueurs français (*Victor Wembanyama, Bilal Coulibaly, Zaccharie Risacher, Alexandre Sarr, Rudy Gobert...*).

---

## 🚀 Installation & Configuration Rapide

### 1. Activer GitHub Pages sur le dépôt
1. Sur GitHub, va dans **Settings** > **Pages** de ton dépôt `AyoubeM/NbActu`.
2. Sous **Build and deployment** > **Source**, choisis **GitHub Actions**.

### 2. Ajouter le Webhook Discord dans les Secrets GitHub
1. Sur Discord, fais un clic-droit sur ton salon > **Modifier le salon** > **Intégrations** > **Webhooks** > **Créer un webhook**.
2. Copie l'URL du Webhook.
3. Sur GitHub, va dans **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.
4. Nom : `DISCORD_WEBHOOK_URL`
5. Valeur : Colle ton URL de Webhook Discord.

---

## 🧪 Test Local & Manuel

### Lancer en local sur votre machine
```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer votre fichier de configuration local
cp .env.example .env
# (Renseignez votre DISCORD_WEBHOOK_URL dans .env)

# Exécuter pour la nuit dernière
python main.py

# Tester avec une date historique précise (ex: 15 matchs joués le 14 avril 2024)
python main.py 20240414
```

### Visualiser le Dashboard Web en local
Ouvrez simplement le fichier `web/index.html` dans votre navigateur ou lancez un serveur local rapide :
```bash
cd web
python -m http.server 8000
# Rendez-vous sur http://localhost:8000
```

### Lancer manuellement depuis GitHub
1. Va dans l'onglet **Actions** de ton dépôt GitHub.
2. Clique sur **NBA Morning Recap & Dashboard** dans la colonne de gauche.
3. Clique sur **Run workflow** (tu peux laisser vide pour la date du jour ou saisir une date au format `YYYYMMDD`).

---

## 📁 Architecture du Projet

```text
NbActu/
├── .github/
│   └── workflows/
│       └── morning_recap.yml     # Cron quotidien & déploiement GitHub Pages
├── config/
│   └── settings.py               # Lecture des paramètres (.env ou variables d'environnement)
├── modules/
│   ├── nba_api.py                # Scoreboard, boxscores et stats de tous les joueurs
│   ├── broadcaster.py            # Détection TV en France (beIN, Prime Video, League Pass)
│   ├── team_analysis.py          # Analyse de forme (streaks W/L, L10, classement)
│   ├── player_analysis.py        # Notes d'impact, Top 5 MVP et focus joueurs français
│   ├── highlights.py             # Recherche des vidéos (FR + fallback officiel NBA US)
│   ├── discord_notifier.py       # Envoi Discord Webhook avec Rich Embeds & Anti-Spoiler
│   └── web_generator.py          # Génération des données pour le dashboard web
├── web/
│   ├── index.html                # Tableau de bord interactif responsive
│   ├── style.css                 # Style sombre moderne, glassmorphism & animations
│   └── app.js                    # Logique client (anti-spoiler, filtres, boxscores)
├── main.py                       # Point d'entrée de l'application
├── requirements.txt              # Dépendances Python légères
├── .gitignore                    # Exclusion stricte des fichiers sensibles (.env, cache)
└── .env.example                  # Modèle de configuration
```
