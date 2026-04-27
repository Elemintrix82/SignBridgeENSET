"""
Génère les diagrammes PlantUML pour le rapport SignBridge.
Télécharge les images PNG depuis le serveur public PlantUML.
"""
import zlib, base64, requests, os

OUT = os.path.dirname(__file__)

# Encodage PlantUML (deflate + base64 custom)
_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'

def _encode6(b):
    return _CHARS[b & 0x3F]

def _encode3bytes(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return _encode6(c1) + _encode6(c2) + _encode6(c3) + _encode6(c4)

def plantuml_encode(text):
    data = zlib.compress(text.encode('utf-8'))[2:-4]
    result = ''
    i = 0
    while i < len(data):
        b1 = data[i]
        b2 = data[i+1] if i+1 < len(data) else 0
        b3 = data[i+2] if i+2 < len(data) else 0
        result += _encode3bytes(b1, b2, b3)
        i += 3
    return result

def fetch(name, code):
    enc = plantuml_encode(code)
    url = f'https://www.plantuml.com/plantuml/png/{enc}'
    print(f'  Fetching {name}...', end=' ')
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            path = os.path.join(OUT, f'{name}.png')
            with open(path, 'wb') as f:
                f.write(r.content)
            print(f'OK ({len(r.content)//1024} KB)')
            return path
        else:
            print(f'FAIL {r.status_code}')
    except Exception as e:
        print(f'ERROR: {e}')
    return None

# ── 1. Diagramme de cas d'utilisation ────────────────────────────────────────
USE_CASE = """
@startuml
skinparam backgroundColor #FAFAFA
skinparam actorStyle awesome
skinparam usecase {
  BackgroundColor #EBF5FB
  BorderColor #2980B9
  ArrowColor #2980B9
}
skinparam actor {
  BackgroundColor #D5F5E3
  BorderColor #1E8449
}

left to right direction
title Diagramme de Cas d'Utilisation — SignBridge

actor "Utilisateur\\nnon connecté" as Guest
actor "Utilisateur\\nconnecté" as User
actor "Administrateur" as Admin

rectangle "SignBridge" {
  usecase "Consulter la page d'accueil" as UC1
  usecase "Consulter le dictionnaire LSF" as UC2
  usecase "S'inscrire" as UC3
  usecase "Se connecter" as UC4

  usecase "Traduire Texte → Signe (Avatar 2D)" as UC5
  usecase "Traduire Texte → Avatar 3D" as UC6
  usecase "Reconnaissance via webcam\\n(Signe → Texte)" as UC7
  usecase "Importer une vidéo\\n(Vidéo → Texte)" as UC8
  usecase "Consulter son profil" as UC9
  usecase "Utiliser la saisie vocale" as UC10

  usecase "Gérer le dictionnaire\\n(CRUD signes)" as UC11
  usecase "Gérer le dataset\\n(DatasetSample)" as UC12
  usecase "Lancer l'entraînement\\ndu modèle ML" as UC13
  usecase "Consulter le dashboard\\nadministrateur" as UC14
}

Guest --> UC1
Guest --> UC2
Guest --> UC3
Guest --> UC4

User --> UC5
User --> UC6
User --> UC7
User --> UC8
User --> UC9
User --> UC10
User --> UC2

Admin --> UC11
Admin --> UC12
Admin --> UC13
Admin --> UC14
Admin --> UC5
Admin --> UC6

UC3 .> UC4 : <<include>>
UC7 .> UC6 : <<extend>>
@enduml
"""

# ── 2. Diagramme de séquence — Reconnaissance webcam ────────────────────────
SEQUENCE_CAM = """
@startuml
skinparam backgroundColor #FAFAFA
skinparam sequenceArrowThickness 2
skinparam roundcorner 5
skinparam sequenceParticipant underline
skinparam sequence {
  BoxBackgroundColor #EBF5FB
  BoxBorderColor #2980B9
  ArrowColor #2C3E50
  LifeLineBorderColor #7F8C8D
  ParticipantBackgroundColor #D6EAF8
  ParticipantBorderColor #2980B9
}

title Diagramme de Séquence — Reconnaissance de Signe (Webcam)

actor "Utilisateur" as U
participant "Interface\\nNavigateur\\n(interface.html)" as UI
participant "MediaPipe\\nHands (JS)" as MP
participant "WebSocket\\nClient\\n(webcam_client.js)" as WS_C
participant "Django Channels\\nASGI Server" as WS_S
participant "SignRecognition\\nConsumer\\n(consumers.py)" as CON
participant "GestureClassifier\\n(Random Forest)" as RF
database "Base de\\nDonnées\\n(SQLite)" as DB

U -> UI : Active la caméra (mode Camera)
UI -> MP : Initialise MediaPipe Hands
MP --> UI : Modèle chargé (WASM)

loop Chaque frame (~12 fps)
  UI -> MP : Envoie frame vidéo
  MP -> MP : Détecte landmarks\\n(21 points x,y,z)
  MP --> UI : Retourne 63 coordonnées
  UI -> WS_C : Transmet landmarks
  WS_C -> WS_S : JSON {landmarks: [63 floats],\\nconfidence: float}\\n(WebSocket ws/sign-recognition/)
  WS_S -> CON : dispatch()
  CON -> CON : Normalise landmarks\\n(centrage poignet)
  CON -> RF : predict(landmarks)
  RF -> RF : Random Forest\\n(100 arbres, 36 classes)
  RF --> CON : {label: "A", confidence: 0.87}
  CON -> DB : Mise à jour session\\n(optionnel)
  CON --> WS_S : JSON {prediction: "A",\\nconfidence: 0.87}
  WS_S --> WS_C : Résultat WebSocket
  WS_C --> UI : Affiche signe reconnu
  UI --> U : Affiche lettre + confiance\\ndans l'interface
end

U -> UI : Désactive caméra
UI -> WS_C : Ferme connexion WebSocket
@enduml
"""

# ── 3. Diagramme de séquence — Texte vers Signe ──────────────────────────────
SEQUENCE_TTS = """
@startuml
skinparam backgroundColor #FAFAFA
skinparam sequenceArrowThickness 2
skinparam roundcorner 5
skinparam sequence {
  ArrowColor #2C3E50
  ParticipantBackgroundColor #D5F5E3
  ParticipantBorderColor #1E8449
}

title Diagramme de Séquence — Texte vers Avatar 3D

actor "Utilisateur" as U
participant "Interface\\n(interface.html)" as UI
participant "Hand3DRenderer\\n(Three.js)" as H3D
participant "API Django\\n/api/translate/text-to-sign/" as API
participant "API Django\\n/api/avatar-landmarks/" as APILM
database "SignDictionary\\n+ DatasetSample" as DB

U -> UI : Saisit texte (ex: "BONJOUR")
note right : onAvatar3DInput() déclenché

alt Renderer non initialisé
  UI -> H3D : new Hand3DRenderer('canvas')
  UI -> APILM : GET /api/avatar-landmarks/
  APILM -> DB : SELECT signes + landmarks\\n(40 samples par signe)
  DB --> APILM : 36 poses (A-Z, 0-9)
  APILM --> UI : JSON {A:[{x,y,z}×21], B:...}
  UI -> H3D : loadPoses(poses)
end

UI -> API : POST /api/translate/text-to-sign/\\n{text: "BONJOUR"}
API -> DB : SELECT SignDictionary\\npour chaque mot
DB --> API : Séquence signes +\\nURLs animation GLB
API --> UI : JSON {sequence:[{word, letters,\\nduration_ms}...]}

loop Pour chaque lettre de la séquence
  UI -> H3D : showSign(letter)
  H3D -> H3D : Tween interpolation\\n(ease in-out, 450ms)
  H3D -> H3D : _applyPose()\\n(21 sphères + 26 cylindres)
  H3D --> UI : Rendu Three.js WebGL
  UI --> U : Main 3D animée\\nlettre par lettre
end
@enduml
"""

# ── 4. Diagramme de classes ───────────────────────────────────────────────────
CLASS_DIAG = """
@startuml
skinparam backgroundColor #FAFAFA
skinparam classBackgroundColor #EBF5FB
skinparam classBorderColor #2980B9
skinparam arrowColor #2C3E50
skinparam class {
  HeaderBackgroundColor #2980B9
  HeaderFontColor #FFFFFF
  FontSize 12
}

title Diagramme de Classes — SignBridge

package "core (Django App)" {
  class CustomUser {
    +id: int
    +email: EmailField
    +prenom: CharField
    +nom: CharField
    +role: CharField [ADMIN|UTILISATEUR]
    +is_active: bool
    --
    +is_admin(): bool
    +__str__(): str
  }

  class SignDictionary {
    +id: int
    +mot: CharField
    +categorie: CharField [ALPHABET|CHIFFRE]
    +description: TextField
    +difficulte: CharField
    +est_valide: bool
    +est_dynamique: bool
    +nb_frames: int
    +animation_glb: FileField
    +ajoute_par: FK(CustomUser)
    --
    +has_animation: bool
    +__str__(): str
  }

  class DatasetSample {
    +id: int
    +signe: FK(SignDictionary)
    +landmarks_data: JSONField [63 floats]
    +source: CharField
    +qualite: CharField [BONNE|MOYENNE|MAUVAISE]
    +created_at: DateTimeField
    --
    +__str__(): str
  }

  class TranslationSession {
    +id: int
    +utilisateur: FK(CustomUser)
    +mode: CharField [TEXT_TO_SIGN|SIGN_TO_TEXT]
    +texte_entree: TextField
    +nb_signes: int
    +duree_ms: int
    +created_at: DateTimeField
    --
    +__str__(): str
  }

  class MLModelVersion {
    +id: int
    +version: CharField
    +algorithme: CharField [RF|LSTM|ENSEMBLE]
    +accuracy: FloatField
    +nb_classes: int
    +est_actif: bool
    +trained_at: DateTimeField
    +model_path: CharField
    --
    +__str__(): str
  }

  class SignRecognitionConsumer {
    +channel_layer
    --
    +connect()
    +disconnect()
    +receive(text_data)
    +_predict_landmarks(landmarks)
  }
}

package "ml_engine" {
  class GestureClassifier {
    -_instance: GestureClassifier
    +rf_model: RandomForestClassifier
    +label_encoder: LabelEncoder
    +lstm_model: Sequential
    +is_loaded: bool
    --
    +{static} get_instance(): GestureClassifier
    +load_models(): void
    +predict_static(landmarks): tuple
    +predict_dynamic(sequence): tuple
  }

  class LandmarkExtractor {
    +hands: mp.Hands
    --
    +extract_from_frame(frame): list
    +extract_from_video(path, fps_target): list
    +normalize_sequence(seq, target_len): ndarray
    +close(): void
  }

  class ModelTrainer {
    +classifier: GestureClassifier
    --
    +train_all(): void
    +train_random_forest(): dict
    +train_lstm(): dict
    +_load_dataset(): tuple
  }

  class VideoProcessor {
    +extractor: LandmarkExtractor
    +classifier: GestureClassifier
    --
    +process_video(path): dict
    +_segment_sequence(landmarks): list
  }
}

' Relations
CustomUser "1" -- "0..*" SignDictionary : ajoute_par >
CustomUser "1" -- "0..*" TranslationSession : utilisateur >
SignDictionary "1" -- "0..*" DatasetSample : signe >
GestureClassifier ..> LandmarkExtractor : utilise
SignRecognitionConsumer ..> GestureClassifier : utilise
VideoProcessor ..> LandmarkExtractor : utilise
VideoProcessor ..> GestureClassifier : utilise
ModelTrainer ..> GestureClassifier : entraîne
@enduml
"""

# ── 5. Schéma synoptique ──────────────────────────────────────────────────────
SYNOPTIC = """
@startuml
skinparam backgroundColor #F8F9FA
skinparam componentStyle rectangle
skinparam component {
  BackgroundColor #EBF5FB
  BorderColor #2980B9
  FontSize 12
}
skinparam rectangle {
  BackgroundColor #FDFEFE
  BorderColor #AAB7B8
}
skinparam arrow {
  Color #2C3E50
  FontSize 10
}

title Schéma Synoptique — Architecture SignBridge

rectangle "COUCHE PRÉSENTATION\\n(Navigateur)" as PRES #D6EAF8 {
  component "interface.html\\n(Tailwind CSS)" as TMPL
  component "webcam_client.js\\n(MediaPipe JS)" as WCAM
  component "hand3d_renderer.js\\n(Three.js r160)" as H3D
  component "avatar_player.js\\n(Canvas 2D)" as AVP
  component "speech_input.js\\n(Web Speech API)" as SPEECH
  component "video_upload.js\\n(XHR Upload)" as VUP
}

rectangle "COUCHE TRANSPORT" as TRANS #D5F5E3 {
  component "HTTP/HTTPS\\n(WhiteNoise + Django)" as HTTP
  component "WebSocket\\n(Django Channels\\nASGI/Daphne)" as WS
}

rectangle "COUCHE APPLICATION\\n(Django 5.2)" as APP #FCF3CF {
  component "views.py\\n(14 vues HTML + 7 API)" as VIEWS
  component "consumers.py\\n(SignRecognitionConsumer)" as CONS
  component "urls.py + routing.py\\n(Routes HTTP + WS)" as URLS
  component "models.py\\n(5 modèles ORM)" as MODELS
  component "forms.py + decorators.py" as FORMS
}

rectangle "COUCHE ML / IA" as ML #FADBD8 {
  component "GestureClassifier\\n(Singleton)" as GC
  component "Random Forest\\n(100 arbres, 36 classes\\n769 Mo, acc=83%)" as RF
  component "LSTM TensorFlow\\n(30 frames séquences)" as LSTM
  component "LandmarkExtractor\\n(MediaPipe Python)" as LE
  component "VideoProcessor" as VP
  component "ModelTrainer" as MT
}

rectangle "COUCHE DONNÉES" as DATA #E8DAEF {
  database "SQLite\\n(db.sqlite3, 58 Mo)" as DB
  component "DatasetSample\\n(38 087 samples)" as DS
  component "signbridge_model/\\n(rf_model.pkl\\nlstm_model.keras)" as FILES
  component "static_signs/\\n(55+ .glb animations)" as GLB
  component "static/images/signs/\\n(36 images JPG)" as IMGS
}

' Flux
WCAM --> WS : landmarks JSON\\n(63 floats/frame)
WS --> CONS : WebSocket
CONS --> GC : predict()
GC --> RF : classify
RF --> CONS : label + confidence
CONS --> WS : résultat JSON
WS --> WCAM : signe reconnu

TMPL --> HTTP : Requêtes HTTP
HTTP --> VIEWS : dispatch
VIEWS --> MODELS : ORM queries
MODELS --> DB : SQL

H3D --> HTTP : GET /api/avatar-landmarks/
AVP --> HTTP : GET /api/translate/text-to-sign/
VUP --> HTTP : POST /api/translate/video-to-text/

VP --> LE : extract_from_video()
VP --> GC : predict_dynamic()
MT --> RF : train_random_forest()
MT --> LSTM : train_lstm()
GC --> FILES : load models
MODELS --> DS : DatasetSample FK
DS --> DB

@enduml
"""

if __name__ == '__main__':
    print('Génération des diagrammes PlantUML...')
    diagrams = [
        ('use_case', USE_CASE),
        ('sequence_webcam', SEQUENCE_CAM),
        ('sequence_tts', SEQUENCE_TTS),
        ('class_diagram', CLASS_DIAG),
        ('synoptic', SYNOPTIC),
    ]
    for name, code in diagrams:
        fetch(name, code)
    print('Terminé.')
