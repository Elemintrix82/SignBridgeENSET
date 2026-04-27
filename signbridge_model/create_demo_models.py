"""
create_demo_models.py
Génère des modèles RF et LSTM synthétiques pour la démo SignBridge.
Compatible avec sklearn 1.4.x+ et Keras 2.x/3.x.
Usage: python signbridge_model/create_demo_models.py
"""
import os
import sys
import json
import warnings
import numpy as np

# Supprimer les warnings verbeux avant les imports ML
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
import logging as _logging
_logging.getLogger('tensorflow').setLevel(_logging.ERROR)
_logging.getLogger('absl').setLevel(_logging.ERROR)

# Ensure we can import from project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

MODEL_DIR = SCRIPT_DIR

# ── Classes LSF pour la démo ──────────────────────────────────────
CLASSES = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z',
    'BONJOUR', 'MERCI', 'OUI', 'NON', 'AIDE',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
]

N_FEATURES_STATIC  = 63   # 21 points × 3 coords (x,y,z) normalisés
N_FEATURES_DYNAMIC = 63   # même shape par frame
SEQ_LEN            = 30   # 30 frames pour LSTM
N_SAMPLES_PER_CLASS = 40

print(f"Génération des modèles démo pour {len(CLASSES)} classes...")


# ── 1. Générer les données synthétiques ─────────────────────────
def make_synthetic_data(n_classes, n_features, n_samples):
    """Génère des données avec un signal distinctif par classe."""
    X, y = [], []
    for cls_idx in range(n_classes):
        center = np.zeros(n_features)
        # Chaque classe a un "centre" légèrement différent
        center[cls_idx % n_features] = 0.5
        center[(cls_idx * 3) % n_features] = -0.3
        for _ in range(n_samples):
            sample = center + np.random.randn(n_features) * 0.15
            X.append(sample)
            y.append(cls_idx)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def make_synthetic_sequences(n_classes, seq_len, n_features, n_samples):
    """Génère des séquences synthétiques pour LSTM."""
    X, y = [], []
    for cls_idx in range(n_classes):
        for _ in range(n_samples):
            seq = np.random.randn(seq_len, n_features).astype(np.float32) * 0.1
            seq[:, cls_idx % n_features] += np.linspace(0, 0.5, seq_len)
            X.append(seq)
            y.append(cls_idx)
    return np.array(X), np.array(y, dtype=np.int32)


# ── 2. Label Encoder ─────────────────────────────────────────────
print("Création du LabelEncoder...")
try:
    import joblib
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    le.fit(CLASSES)

    le_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
    joblib.dump(le, le_path)
    print(f"  LabelEncoder sauvé: {le_path}")
except ImportError as e:
    print(f"  ERREUR: {e}")
    print("  Installez scikit-learn: pip install scikit-learn joblib")
    sys.exit(1)


# ── 3. Random Forest ─────────────────────────────────────────────
print("Entraînement Random Forest...")
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    X_rf, y_rf = make_synthetic_data(len(CLASSES), N_FEATURES_STATIC, N_SAMPLES_PER_CLASS)
    X_train, X_test, y_train, y_test = train_test_split(X_rf, y_rf, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    accuracy = rf.score(X_test, y_test)
    print(f"  Accuracy RF (démo): {accuracy:.2%}")

    rf_path = os.path.join(MODEL_DIR, 'rf_model.pkl')
    joblib.dump(rf, rf_path)
    print(f"  Modèle RF sauvé: {rf_path}")

except Exception as e:
    print(f"  ERREUR RF: {e}")
    sys.exit(1)


# ── 4. LSTM (TensorFlow/Keras) ───────────────────────────────────
print("Entraînement LSTM...")
try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')

    X_lstm, y_lstm = make_synthetic_sequences(
        len(CLASSES), SEQ_LEN, N_FEATURES_DYNAMIC, N_SAMPLES_PER_CLASS // 2
    )
    y_cat = tf.keras.utils.to_categorical(y_lstm, num_classes=len(CLASSES))

    # Architecture compatible Keras 2.x ET 3.x
    # On utilise input_shape dans la première couche au lieu de layers.Input()
    # pour éviter le paramètre batch_shape incompatible avec Keras 2.15
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.LSTM(
        64,
        return_sequences=False,
        input_shape=(SEQ_LEN, N_FEATURES_DYNAMIC),
    ))
    model.add(tf.keras.layers.Dropout(0.3))
    model.add(tf.keras.layers.Dense(64, activation='relu'))
    model.add(tf.keras.layers.Dense(len(CLASSES), activation='softmax'))

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )

    # Entraînement rapide (juste pour la démo)
    history = model.fit(
        X_lstm, y_cat,
        epochs=10,
        batch_size=32,
        validation_split=0.2,
        verbose=0,
    )
    val_acc = history.history.get('val_accuracy', [0])[-1]
    print(f"  Accuracy LSTM (démo): {val_acc:.2%}")

    # Sauvegarder en format natif .keras (plus moderne, évite le warning HDF5 legacy)
    lstm_path = os.path.join(MODEL_DIR, 'lstm_model.keras')
    try:
        model.save(lstm_path)
    except Exception:
        # Fallback .h5 si le format .keras n'est pas supporté (Keras < 2.12)
        lstm_path = os.path.join(MODEL_DIR, 'lstm_model.h5')
        model.save(lstm_path)
    print(f"  Modèle LSTM sauvé: {lstm_path}")

except ImportError:
    print("  TensorFlow non disponible — modèle LSTM non créé (mode RF seul)")
except Exception as e:
    print(f"  ERREUR LSTM: {e}")


# ── 5. Mise à jour model_info.json ────────────────────────────────
from datetime import datetime

info_path = os.path.join(MODEL_DIR, 'model_info.json')
info = {
    "trained_at": datetime.now().isoformat(),
    "status": "demo",
    "note": "Modèles synthétiques pour démo — remplacer par vrais modèles entraînés",
    "classes": CLASSES,
    "n_classes": len(CLASSES),
    "n_features_static": N_FEATURES_STATIC,
    "seq_len": SEQ_LEN,
    "results": {
        "rf_accuracy_demo": float(accuracy) if 'accuracy' in vars() else None,
        "lstm_val_accuracy_demo": float(val_acc) if 'val_acc' in vars() else None,
    }
}
with open(info_path, 'w', encoding='utf-8') as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
print(f"  model_info.json mis à jour: {info_path}")

print("\nModèles démo créés avec succès!")
print(f"  rf_model.pkl        : {os.path.join(MODEL_DIR, 'rf_model.pkl')}")
print(f"  lstm_model.keras    : {os.path.join(MODEL_DIR, 'lstm_model.keras')}")
print(f"  label_encoder.pkl   : {os.path.join(MODEL_DIR, 'label_encoder.pkl')}")
print(f"  model_info.json     : {info_path}")
print("\nPour utiliser avec SignBridge, lancez le serveur normalement.")
