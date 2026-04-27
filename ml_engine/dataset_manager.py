import json
import logging
import numpy as np
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


def _scale_normalize(lm63: np.ndarray) -> np.ndarray:
    """
    Normalise par la distance poignet→MCP-majeur (point 9).
    Si les données ont déjà été normalisées (MCP-majeur ≈ 1), ne touche rien.
    Rend les features indépendants de la taille de main / distance caméra.
    """
    lm = lm63.reshape(21, 3).copy().astype(np.float32)
    scale = float(np.linalg.norm(lm[9]))
    if scale > 1e-6:
        # Si scale ≈ 1.0 les données sont déjà normalisées (généré via augment())
        # Si scale >> 1 ou << 1, on normalise.
        if abs(scale - 1.0) > 0.05:
            lm /= scale
    return lm.flatten()

DATASET_DIR = Path(getattr(settings, 'BASE_DIR', '.')) / 'dataset'


class DatasetManager:
    """Gère le dataset d'entraînement (landmarks + labels)."""

    def __init__(self):
        self.landmarks_dir = DATASET_DIR / 'landmarks'
        self.registry_path = DATASET_DIR / 'registry.json'
        self.landmarks_dir.mkdir(parents=True, exist_ok=True)
        DATASET_DIR.mkdir(parents=True, exist_ok=True)

    def load_dataset(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Charge le dataset depuis la base de données.
        Retourne (X, y) numpy arrays.
        """
        try:
            import django
            from core.models import DatasetSample

            samples = DatasetSample.objects.filter(
                qualite__in=['BONNE', 'MOYENNE']
            ).select_related('signe')

            if not samples.exists():
                logger.warning('Dataset vide — aucun sample en base')
                return np.array([]), np.array([])

            X_list = []
            y_list = []

            for sample in samples:
                lm = sample.landmarks_data
                if isinstance(lm, list) and len(lm) >= 63:
                    X_list.append(_scale_normalize(np.array(lm[:63], dtype=np.float32)))
                    y_list.append(sample.signe.mot.upper())

            if not X_list:
                return np.array([]), np.array([])

            return np.array(X_list, dtype=np.float32), np.array(y_list)

        except Exception as e:
            logger.error(f'Erreur chargement dataset: {e}')
            return np.array([]), np.array([])

    def load_sequence_dataset(self, seq_len: int = 30) -> tuple[np.ndarray, np.ndarray]:
        """
        Charge le dataset de séquences pour LSTM.
        Retourne (X, y) de forme (N, seq_len, 63).
        """
        try:
            from core.models import DatasetSample, SignDictionary

            dynamic_signs = SignDictionary.objects.filter(est_dynamique=True)
            X_list = []
            y_list = []

            for sign in dynamic_signs:
                samples = DatasetSample.objects.filter(signe=sign, qualite='BONNE')
                for sample in samples:
                    lm = sample.landmarks_data
                    if isinstance(lm, list) and len(lm) >= seq_len:
                        seq = np.array(lm[:seq_len], dtype=np.float32)
                        if seq.shape == (seq_len, 63):
                            X_list.append(seq)
                            y_list.append(sign.mot.upper())

            if not X_list:
                return np.array([]).reshape(0, seq_len, 63), np.array([])

            return np.array(X_list, dtype=np.float32), np.array(y_list)

        except Exception as e:
            logger.error(f'Erreur chargement séquences: {e}')
            return np.array([]).reshape(0, seq_len, 63), np.array([])

    def save_sample(self, sign_id: int, landmarks: list, source: str = 'WEBCAM'):
        """Sauvegarde un sample en base de données."""
        try:
            from core.models import DatasetSample, SignDictionary
            sign   = SignDictionary.objects.get(pk=sign_id)
            sample = DatasetSample.objects.create(
                signe=sign,
                landmarks_data=landmarks,
                source=source,
            )
            return sample.pk
        except Exception as e:
            logger.error(f'Erreur sauvegarde sample: {e}')
            return None

    def get_stats(self) -> dict:
        """Retourne les statistiques du dataset."""
        try:
            from core.models import DatasetSample
            from django.db.models import Count

            total = DatasetSample.objects.count()
            by_sign = DatasetSample.objects.values('signe__mot').annotate(
                count=Count('id')
            ).order_by('-count')

            return {
                'total_samples': total,
                'by_sign': list(by_sign[:20]),
                'num_classes': len(set(s['signe__mot'] for s in by_sign)),
            }
        except Exception as e:
            logger.error(f'Erreur stats dataset: {e}')
            return {'total_samples': 0, 'by_sign': [], 'num_classes': 0}
