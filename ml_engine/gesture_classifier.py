import os
import warnings
import logging
import numpy as np
from pathlib import Path
from django.conf import settings

# Supprimer les warnings verbeux de TensorFlow avant tout import TF
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Supprimer les logs TF et absl au niveau Python
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

MODEL_DIR = Path(getattr(settings, 'ML_MODEL_DIR', 'signbridge_model'))


class GestureClassifier:
    """Classifieur hybride RF (statique) + LSTM (dynamique)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'rf_model'):
            self.rf_model      = None
            self.lstm_model    = None
            self.label_encoder = None
            self._loaded       = False

    def load_models(self):
        if self._loaded:
            return True

        try:
            import joblib

            rf_path = MODEL_DIR / 'rf_model.pkl'
            le_path = MODEL_DIR / 'label_encoder.pkl'

            if not rf_path.exists():
                raise FileNotFoundError(f'Modèle RF introuvable: {rf_path}')

            self.rf_model      = joblib.load(rf_path)
            self.label_encoder = joblib.load(le_path)
            logger.info('Modèle Random Forest chargé')

            # Cherche le modèle LSTM : format natif .keras d'abord, puis .h5
            lstm_path = MODEL_DIR / 'lstm_model.keras'
            if not lstm_path.exists():
                lstm_path = MODEL_DIR / 'lstm_model.h5'
            if lstm_path.exists():
                import tensorflow as tf
                # Supprimer les warnings TF lors du chargement
                tf.get_logger().setLevel('ERROR')
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    self.lstm_model = tf.keras.models.load_model(str(lstm_path))
                logger.info('Modèle LSTM chargé')

            self._loaded = True
            return True

        except FileNotFoundError as e:
            logger.warning(f'Modèles ML non trouvés: {e}')
            self._loaded = False
            return False
        except Exception as e:
            logger.error(f'Erreur chargement modèles: {e}')
            self._loaded = False
            return False

    def predict_static(self, features: np.ndarray) -> tuple[str, float]:
        """Prédit un signe statique (alphabet/chiffre) via Random Forest."""
        if not self._loaded or self.rf_model is None:
            return 'DEMO', 0.5

        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)

            proba   = self.rf_model.predict_proba(features)[0]
            pred_idx = np.argmax(proba)
            confidence = proba[pred_idx]
            label = self.label_encoder.inverse_transform([pred_idx])[0]
            return label, float(confidence)

        except Exception as e:
            logger.error(f'Erreur prédiction RF: {e}')
            return 'ERREUR', 0.0

    def predict_dynamic(self, sequence: np.ndarray) -> tuple[str, float]:
        """Prédit un signe dynamique (mot) via LSTM."""
        if not self._loaded or self.lstm_model is None:
            return 'DEMO', 0.5

        try:
            if sequence.ndim == 2:
                sequence = sequence[np.newaxis, ...]

            preds      = self.lstm_model.predict(sequence, verbose=0)
            pred_idx   = np.argmax(preds[0])
            confidence = float(preds[0][pred_idx])
            label      = self.label_encoder.inverse_transform([pred_idx])[0]
            return label, confidence

        except Exception as e:
            logger.error(f'Erreur prédiction LSTM: {e}')
            return 'ERREUR', 0.0

    @property
    def is_loaded(self):
        return self._loaded

    @property
    def classes(self):
        if self.label_encoder is not None:
            return list(self.label_encoder.classes_)
        return []
