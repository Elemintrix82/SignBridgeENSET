import sys
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

SKIP_ML_COMMANDS = {
    'migrate', 'makemigrations', 'collectstatic',
    'shell', 'test', 'setup_demo_data', 'train_model',
    'extract_landmarks', 'createsuperuser', 'dbshell',
    'showmigrations', 'sqlmigrate', 'check',
}


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'SignBridge Core'

    def ready(self):
        current_cmd = sys.argv[1] if len(sys.argv) > 1 else ''
        if current_cmd in SKIP_ML_COMMANDS:
            return

        try:
            import threading
            t = threading.Thread(target=self._load_ml_models, daemon=True)
            t.start()
        except Exception as e:
            logger.warning(f'Impossible de charger les modèles ML: {e}')

    def _load_ml_models(self):
        try:
            from ml_engine.gesture_classifier import GestureClassifier
            classifier = GestureClassifier()
            classifier.load_models()
            logger.info('Modèles ML chargés avec succès')
        except FileNotFoundError:
            logger.warning('Modèles ML non trouvés — mode démo actif (sans reconnaissance)')
        except Exception as e:
            logger.warning(f'Erreur chargement ML (non bloquant): {e}')
