<div align="center">

# 🤟 SignBridge

**Traduction bidirectionnelle Français ↔ Langue des Signes**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-FF6F00?style=flat&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Three.js](https://img.shields.io/badge/Three.js-r160-black?style=flat&logo=three.js&logoColor=white)](https://threejs.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

*Développé à l'ENSET de Douala — Cameroun 🇨🇲*

</div>

---

## Présentation

SignBridge est une application web full-stack permettant la traduction bidirectionnelle entre le français écrit/parlé et la Langue des Signes. Le système couvre trois axes :

- **Texte → Signe** : saisie de texte animée via un avatar 3D procédural (Three.js)
- **Caméra → Texte** : reconnaissance gestuelle en temps réel par webcam (MediaPipe + Random Forest)
- **Parole → Signe** : dictée vocale transcrite puis animée (Web Speech API)

---

## Aperçu des pages

| Page | Description |
|------|-------------|
| `/` | Landing page publique + démo rapide |
| `/app/?mode=text` | Traducteur Texte → Signe (avatar 3D) |
| `/app/?mode=camera` | Traducteur Caméra → Texte (webcam temps réel) |
| `/app/?mode=avatar` | Simulateur Avatar 3D interactif |
| `/dictionnaire/` | Dictionnaire des signes (A–Z, 0–9) |
| `/admin-panel/` | Dashboard administration + entraînement ML |

---

## Stack technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Backend** | Django 5.2 + Python 3.10 | Serveur HTTP, ORM, authentification |
| **ASGI / WebSocket** | Django Channels 4 + Daphne 4 | Streaming temps réel (webcam) |
| **Computer Vision** | MediaPipe Hands 0.10 | Extraction 21 landmarks main (63 features x,y,z) |
| **ML Statique** | scikit-learn — Random Forest | Classification signes statiques (A–Z, 0–9) — 83 % accuracy |
| **ML Dynamique** | TensorFlow 2.15 — LSTM | Signes dynamiques (séquences 30 frames) |
| **Avatar 3D** | Three.js r160 (WebGL) | Rendu procédural : 21 sphères + 26 cylindres |
| **Frontend CSS** | Tailwind CSS v3 (compilé local) | Design system dark/light, responsive |
| **Parole** | Web Speech API | Dictée vocale navigateur (natif) |
| **Fichiers statiques** | WhiteNoise 6 | Serving production sans nginx |
| **Base de données** | SQLite (dev) | Données utilisateurs, signes, dataset |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Navigateur                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Webcam   │  │  Texte/Voix  │  │     Avatar 3D         │ │
│  │MediaPipe │  │  (JS natif)  │  │  Three.js r160        │ │
│  └────┬─────┘  └──────┬───────┘  └───────────┬───────────┘ │
└───────┼───────────────┼──────────────────────┼─────────────┘
        │ WebSocket     │ REST API             │ REST API
        ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django (ASGI/Daphne)                     │
│                                                             │
│  SignRecognitionConsumer   │  Views (REST)                  │
│  ├─ MediaPipe (serveur)    │  ├─ api_translate_text         │
│  ├─ Random Forest predict  │  ├─ api_translate_video        │
│  └─ réponse JSON WS        │  └─ api_avatar_landmarks       │
│                            │                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   ml_engine/                        │    │
│  │  LandmarkExtractor  │  GestureClassifier            │    │
│  │  VideoProcessor     │  ModelTrainer                 │    │
│  │  DatasetManager     │  rf_model.pkl (769 MB)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Models: CustomUser │ SignDictionary │ DatasetSample        │
│          TranslationSession │ TrainingJob                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Structure du projet

```
signbridge/
├── config/                      # Settings, ASGI, WSGI, URLs racine
├── core/                        # Application principale
│   ├── management/commands/     # CLI Django
│   │   ├── setup_demo_data.py   # Données de démonstration
│   │   ├── train_model.py       # Entraînement RF + LSTM
│   │   ├── extract_landmarks.py # Extraction landmarks vidéos
│   │   ├── import_kaggle_asl.py # Import dataset Kaggle ASL
│   │   └── generate_asl_training.py # Génération synthétique
│   ├── migrations/
│   ├── consumers.py             # WebSocket — reconnaissance temps réel
│   ├── models.py                # Modèles de données
│   ├── views.py                 # Pages HTML + API REST
│   ├── urls.py
│   ├── forms.py
│   └── decorators.py
├── ml_engine/                   # Pipeline Machine Learning
│   ├── landmark_extractor.py    # MediaPipe → 63 features
│   ├── gesture_classifier.py    # Prédiction RF / LSTM
│   ├── model_trainer.py         # Entraînement et sauvegarde
│   ├── video_processor.py       # Traitement vidéo frame par frame
│   └── dataset_manager.py       # Gestion des données d'entraînement
├── signbridge_model/            # Modèles entraînés
│   ├── rf_model.pkl             # Random Forest (~769 MB)
│   └── lstm_model.h5            # LSTM TensorFlow
├── templates/                   # 14 templates HTML Tailwind
│   ├── base.html
│   ├── landing.html
│   ├── app/interface.html       # Interface principale (3 modes)
│   ├── dictionary/
│   ├── admin_panel/
│   └── auth/
├── static/
│   ├── css/
│   │   ├── input.css            # Source Tailwind
│   │   └── tailwind.css         # CSS compilé (minifié)
│   └── js/
│       ├── tailwind.config.js   # Config Tailwind CSS
│       ├── hand3d_renderer.js   # Avatar 3D Three.js (21 landmarks)
│       ├── sign_recognition.js  # WebSocket + MediaPipe navigateur
│       ├── avatar_player.js     # Lecture animations GLTF
│       ├── dictionary.js        # Recherche dictionnaire
│       ├── admin_panel.js       # Dashboard admin
│       └── auth.js              # Formulaires connexion
├── static_signs/                # Animations GLB des signes
├── dataset/                     # Vidéos brutes + landmarks extraits
├── doc_assets/                  # Diagrams PlantUML + rapport Word
├── .env.example                 # Template variables d'environnement
├── package.json                 # Scripts Tailwind CSS
└── requirements.txt             # Dépendances Python
```

---

## Installation

### Prérequis

- Python 3.10+
- Node.js 18+ (pour Tailwind CSS)
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/Elemintrix82/SignBridgeENSET.git
cd SignBridgeENSET

# 2. Environnement virtuel Python
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Dépendances Python
pip install -r requirements.txt

# 4. CSS Tailwind (compilation)
npm install
npm run build:css

# 5. Variables d'environnement
cp .env.example .env
# Modifiez .env si nécessaire (SECRET_KEY, etc.)

# 6. Base de données
python manage.py migrate

# 7. Données de démonstration (utilisateurs + signes)
python manage.py setup_demo_data

# 8. Démarrer le serveur ASGI
daphne -p 8000 config.asgi:application
```

Ouvrez **http://localhost:8000**

---

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Administrateur | admin@signbridge.fr | Admin@2024 |
| Utilisateur | demo@signbridge.fr | Demo@2024 |

---

## Pipeline Machine Learning

### Données d'entraînement

| Source | Type | Quantité |
|--------|------|----------|
| `GENERATED` | Landmarks synthétiques (augmentation ×300) | 14 400 samples |
| `KAGGLE` | CSV coordonnées ASL (Kaggle dataset) | 20 834 samples |
| `KAGGLE_IMG` | MediaPipe sur images réelles | 2 853 samples |

### Entraînement

```bash
# Extraire les landmarks depuis les vidéos (dataset/raw/)
python manage.py extract_landmarks

# Importer un dataset Kaggle CSV
python manage.py import_kaggle_asl --file kaggle_asl.csv

# Entraîner Random Forest + LSTM
python manage.py train_model --algo all

# Ou via l'interface : http://localhost:8000/admin-panel/training/
```

### Modèles

- **Random Forest** (scikit-learn) — 100 arbres, 36 classes (A–Z, 0–9)
  - Features : 63 coordonnées (21 landmarks × x,y,z normalisées)
  - Accuracy : **83 %** sur le jeu de test
  - Fichier : `signbridge_model/rf_model.pkl`

- **LSTM** (TensorFlow 2.15) — séquences dynamiques
  - Input : 30 frames × 63 features
  - Sortie : probabilités sur les classes de signes
  - Fichier : `signbridge_model/lstm_model.h5`

### Pipeline temps réel (WebSocket)

```
Webcam (navigateur)
    → MediaPipe Hands JS (21 landmarks)
    → WebSocket ws://…/ws/sign-recognition/
    → SignRecognitionConsumer (Django Channels)
    → GestureClassifier.predict(landmarks)   ← Random Forest
    → JSON { sign, confidence }
    → Navigateur (affichage résultat)
```

---

## API REST

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| `POST` | `/api/translate/text-to-sign/` | Texte → séquence de signes | Connecté |
| `POST` | `/api/translate/video-to-text/` | Vidéo LSF → texte | Connecté |
| `GET` | `/api/dictionary/` | Liste des signes | Public |
| `POST` | `/api/dictionary/` | Ajouter un signe | Admin |
| `GET` | `/api/ml/status/` | Statut du modèle ML | Admin |
| `POST` | `/api/admin/train/` | Lancer l'entraînement | Admin |
| `GET` | `/api/stats/` | Statistiques globales | Admin |
| `WS` | `ws://…/ws/sign-recognition/` | Reconnaissance webcam temps réel | Connecté |

---

## Avatar 3D

L'avatar est entièrement procédural — aucun fichier GLTF requis :

- **21 sphères** pour les articulations (MCP, PIP, DIP, pointe de chaque doigt + poignet)
- **26 cylindres** pour les os (connexions entre articulations)
- **Rendu WebGL** via Three.js r160 avec éclairage directionnel + ambiant
- **Positions** calculées depuis les landmarks MediaPipe moyennés sur les 40 meilleures détections du dataset
- **Auto-animation** : chaque lettre tapée déclenche immédiatement la pose 3D

---

## Design System

- **Palette** : Vert camerounais `#007A5E` · Rouge `#CE1126` · Jaune `#FCD116`
- **Dark mode** : activé par défaut, basculable en clair (classe `dark` sur `<html>`)
- **Typographie** : Poppins (titres) · Inter (corps) · JetBrains Mono (code)
- **Composants** : `.btn-primary` · `.btn-secondary` · `.sb-card` · `.sb-input` · `.badge`

---

## Production

```bash
# .env
DEBUG=False
SECRET_KEY=<clé-secrète-sécurisée>
ALLOWED_HOSTS=votredomaine.com

# Collecte des fichiers statiques
python manage.py collectstatic

# Lancement
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

---

## Licence

Ce projet est distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**ENSET de Douala — Cameroun 🇨🇲**

*SignBridge — Briser les barrières, signer l'avenir* 🤟

</div>
