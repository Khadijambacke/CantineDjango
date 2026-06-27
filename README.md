
# CantinEntreprise - Système de Gestion de Cantine d'Entreprise
CantinEntreprise est une application web moderne de gestion de cantine d'entreprise. Elle permet aux employés de consulter les menus et de réserver leurs repas, aux cuisiniers de planifier les repas et de suivre les portions à préparer, et aux gestionnaires de suivre les comptes et l'administration des employés.
Ce projet comporte un **Backend en Django** (API REST) et un **Frontend en HTML/CSS/JavaScript (TailwindCSS)**.
---
## Fonctionnalités principales
### 👤 Espace Employé
* **Consultation du planning** : Liste des repas du jour et à venir.
* **Réservations** : Possibilité de réserver un repas par solde (compte interne débité) ou paiement sur place.
* **Annulation** : Annuler une réservation dans les délais impartis (avec remboursement si payé par solde).
* **Code QR individuel** : Génération d'un code QR unique par réservation, à présenter à la cuisine.
* **Notifications** : Alertes en temps réel (ex. compte validé, repas prêt, réservation annulée).
### 👨‍🍳 Espace Cuisinier
* **Planification des menus** : Associer des plats du catalogue à des dates spécifiques.
* **Statistiques de préparation** : Connaître à l'avance le nombre exact de portions réservées à préparer pour le lendemain.
* **Validation par QR Code** : Scanner le QR Code de la réservation d'un employé pour marquer instantanément son repas comme "consommé".
* **Gestion des avis** : Consulter les évaluations et commentaires laissés par les employés.
### 💼 Espace Gestionnaire & Administrateur
* **Gestion des employés** : Suivi des profils, affectation des rôles, et gestion du solde de cantine.
* **Gestion du catalogue** : Ajout et modification des plats (plats principaux, entrées, desserts).
* **Tableau de bord** : Statistiques globales sur les ventes, les plats les plus réservés et la satisfaction.
---
##  Technologies utilisées
### Backend (Django API REST)
* **Framework principal** : Django 4.2 & Django REST Framework (DRF)
* **Authentification** : Jetons sécurisés **JWT** (JSON Web Tokens) via `PyJWT`
* **Sécurité & OTP** : Validation de compte par code OTP envoyé par mail (SMTP) ou console
* **Génération de QR Codes** : Bibliothèque Python `qrcode` et `Pillow`
* **Base de données** : MySQL via le connecteur `mysqlclient`
* **Documentation API** : OpenAPI 3 & Swagger via `drf-spectacular`
* **CORS** : `django-cors-headers` pour autoriser le frontend local
### Frontend (Single Page Application - Vanilla JS)
* **Structure** : HTML5 sémantique
* **Style & Design** : TailwindCSS (via CDN) avec une charte graphique premium (mode clair/sombre, animations fluides, boutons animés)
* **Icônes** : FontAwesome 6 (via CDN)
* **Communication API** : API native **`fetch()`** intégrée au navigateur (centralisée dans `assets/js/app.js`)
---
## 📂 Structure du projet
```text
CantineDjango/
│
├── backend/                  # Partie API Django
│   ├── api/                  # Application Django principale (Modèles, Vues, Sérialiseurs)
│   │   ├── views/            # Contrôleurs de l'API (auth, menus, réservations...)
│   │   ├── models.py         # Modèles de données (User, MenuJour, Reservation...)
│   │   └── authentication.py # Middleware d'authentification JWT custom
│   ├── config/               # Configuration du projet Django (settings.py, urls.py)
│   ├── manage.py             # Script de gestion Django
│   └── requirements.txt      # Dépendances Python du projet
│
├── frontend/                 # Partie Interface Utilisateur
│   ├── assets/               
│   │   ├── css/              # Feuilles de styles custom
│   │   └── js/               # Scripts JS (app.js centralise les appels API)
│   ├── login.html            # Page de connexion
│   ├── register.html         # Page d'inscription (avec validation OTP)
│   ├── dashboard-employe.html# Espace Employé
│   ├── dashboard-cuisinier.html # Espace Cuisine
│   ├── dashboard-gestionnaire.html # Espace Gestion
│   └── ...                   # Autres pages HTML (menu, panier, commandes)
│
└── env                       # Fichier de configuration des variables d'environnement
```
---
## ⚙️ Installation et Démarrage
### 1. Prérequis
* Python 3.10+
* MySQL (XAMPP, Laragon ou un serveur MySQL standalone)
### 2. Configuration du Backend
1. **Créer un environnement virtuel** dans le dossier racine :
   ```bash
   python -m venv .venv
   ```
2. **Activer l'environnement virtuel** :
   * **Windows (PowerShell)** :
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * **Windows (CMD)** :
     ```cmd
     .venv\Scripts\activate.bat
     ```
   * **macOS/Linux** :
     ```bash
     source .venv/bin/activate
     ```
3. **Installer les dépendances** :
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Configuration de l'environnement** :
   * Renommez ou copiez le fichier `env` à la racine en `.env` :
     ```bash
     copy env .env
     ```
   * Configurez vos accès à la base de données MySQL dans ce fichier `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`).
   * Créez la base de données MySQL vide (nommée par défaut `gescantine_app`).
5. **Exécuter les migrations** pour créer les tables :
   ```bash
   python backend/manage.py migrate
   ```
6. **Lancer le serveur de développement** :
   ```bash
   python backend/manage.py runserver
   ```
   Le backend tourne maintenant sur `http://127.0.0.1:8000/`.
### 3. Utilisation du Frontend
1. Ouvrez directement le fichier [frontend/index.html](file:///C:/MyProjets/CantineDjango/frontend/index.html) dans votre navigateur (ou utilisez une extension d'éditeur de code comme *Live Server* dans VS Code).
2. Assurez-vous que le backend Django est actif pour que le frontend puisse s'y connecter et échanger des données.
---
##  Documentation de l'API (Swagger)
Une fois le backend Django démarré, vous pouvez accéder à la documentation interactive de toutes les routes de l'API :
* **Swagger UI** : `http://127.0.0.1:8000/api/schema/swagger-ui/`
* **Redoc** : `http://127.0.0.1:8000/api/schema/redoc/`

