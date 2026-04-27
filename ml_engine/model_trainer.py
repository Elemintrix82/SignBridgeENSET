import os
import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from django.conf import settings
from .dataset_manager import DatasetManager

logger = logging.getLogger(__name__)

MODEL_DIR = Path(getattr(settings, 'ML_MODEL_DIR', 'signbridge_model'))


class ModelTrainer:
    """Entraîne les modèles RF et LSTM depuis le dataset en base."""

    def __init__(self):
        self.dm        = DatasetManager()
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

    def train_all(self) -> dict:
        """Lance l'entraînement RF + LSTM. Retourne les métriques."""
        results = {}

        logger.info('=== Début entraînement SignBridge ===')

        rf_result = self.train_random_forest()
        results['random_forest'] = rf_result

        seq_result = self.train_lstm()
        results['lstm'] = seq_result

        self._save_model_info(results)
        logger.info('=== Entraînement terminé ===')
        return results

    def train_random_forest(self) -> dict:
        logger.info('Entraînement Random Forest...')
        X, y = self.dm.load_dataset()

        if len(X) == 0:
            logger.warning('Pas de données pour RF')
            return {'status': 'skipped', 'reason': 'no_data'}

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder
            from sklearn.model_selection import train_test_split
            import joblib

            le = LabelEncoder()
            y_enc = le.fit_transform(y)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
            )

            clf = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=2,
                random_state=42,
                n_jobs=-1,
            )
            clf.fit(X_train, y_train)
            accuracy = clf.score(X_test, y_test)

            joblib.dump(clf, MODEL_DIR / 'rf_model.pkl')
            joblib.dump(le,  MODEL_DIR / 'label_encoder.pkl')

            self._register_model('RANDOM_FOREST', accuracy, len(le.classes_), len(X))

            logger.info(f'RF accuracy: {accuracy:.4f}, classes: {len(le.classes_)}')
            return {
                'status':     'success',
                'accuracy':   float(accuracy),
                'nb_classes': len(le.classes_),
                'nb_samples': len(X),
                'classes':    list(le.classes_),
            }

        except Exception as e:
            logger.error(f'Erreur entraînement RF: {e}')
            return {'status': 'error', 'error': str(e)}

    def train_lstm(self) -> dict:
        logger.info('Entraînement LSTM...')
        X, y = self.dm.load_sequence_dataset()

        if len(X) == 0:
            logger.warning('Pas de données séquentielles pour LSTM')
            return {'status': 'skipped', 'reason': 'no_data'}

        try:
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            import tensorflow as tf
            from sklearn.preprocessing import LabelEncoder
            from sklearn.model_selection import train_test_split
            import joblib

            le = LabelEncoder()
            y_enc = le.fit_transform(y)
            n_classes = len(le.classes_)

            y_cat = tf.keras.utils.to_categorical(y_enc, num_classes=n_classes)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y_cat, test_size=0.2, random_state=42
            )

            model = tf.keras.Sequential([
                tf.keras.layers.LSTM(128, return_sequences=True, input_shape=(30, 63)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.LSTM(64),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(n_classes, activation='softmax'),
            ])

            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy'],
            )

            early_stop = tf.keras.callbacks.EarlyStopping(
                patience=10, restore_best_weights=True
            )

            history = model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=50,
                batch_size=32,
                callbacks=[early_stop],
                verbose=0,
            )

            _, accuracy = model.evaluate(X_test, y_test, verbose=0)

            model.save(str(MODEL_DIR / 'lstm_model.h5'))
            joblib.dump(le, MODEL_DIR / 'label_encoder.pkl')

            self._register_model('LSTM', accuracy, n_classes, len(X))

            logger.info(f'LSTM accuracy: {accuracy:.4f}, classes: {n_classes}')
            return {
                'status':     'success',
                'accuracy':   float(accuracy),
                'nb_classes': n_classes,
                'nb_samples': len(X),
                'epochs':     len(history.history['loss']),
            }

        except Exception as e:
            logger.error(f'Erreur entraînement LSTM: {e}')
            return {'status': 'error', 'error': str(e)}

    def _register_model(self, algo: str, accuracy: float, nb_classes: int, nb_samples: int):
        try:
            from core.models import MLModelVersion
            version = datetime.now().strftime('%Y%m%d_%H%M')
            MLModelVersion.objects.create(
                version=version,
                algorithme=algo,
                accuracy=accuracy,
                nb_classes=nb_classes,
                nb_samples=nb_samples,
                est_actif=True,
                parametres={'trained_at': version},
            )
        except Exception as e:
            logger.error(f'Erreur enregistrement modèle: {e}')

    def _save_model_info(self, results: dict):
        info = {
            'trained_at': datetime.now().isoformat(),
            'results':    results,
        }
        try:
            with open(MODEL_DIR / 'model_info.json', 'w') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f'Erreur sauvegarde model_info: {e}')
