import logging
import numpy as np
from pathlib import Path
from .landmark_extractor import LandmarkExtractor
from .gesture_classifier import GestureClassifier

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Traite une vidéo LSF et retourne le texte français correspondant."""

    def __init__(self):
        self.extractor  = LandmarkExtractor()
        self.classifier = GestureClassifier()
        self.classifier.load_models()

    def process_video(self, video_path: str, progress_callback=None) -> dict:
        """
        Traite une vidéo et retourne la traduction.
        progress_callback(percent, message) appelé périodiquement.
        """
        path = Path(video_path)
        if not path.exists():
            return {'error': 'Fichier vidéo introuvable', 'text': ''}

        try:
            if progress_callback:
                progress_callback(10, 'Extraction des frames...')

            frames_landmarks = self.extractor.extract_from_video(str(path), fps_target=10)

            if not frames_landmarks:
                return {
                    'text':     '',
                    'segments': [],
                    'error':    'Aucune main détectée dans la vidéo',
                }

            if progress_callback:
                progress_callback(50, f'{len(frames_landmarks)} frames extraites, classification...')

            segments  = self._segment_sequence(frames_landmarks)
            words     = []
            raw_words = []

            for i, segment in enumerate(segments):
                if progress_callback:
                    pct = 50 + int((i / len(segments)) * 40)
                    progress_callback(pct, f'Classifying segment {i+1}/{len(segments)}...')

                seq = self.extractor.normalize_sequence(segment, target_len=30)
                word, conf = self.classifier.predict_dynamic(seq)

                if conf > 0.6:
                    words.append(word.lower())
                    raw_words.append({'word': word, 'confidence': conf, 'segment_len': len(segment)})

            if progress_callback:
                progress_callback(95, 'Post-traitement...')

            text = ' '.join(words)

            if progress_callback:
                progress_callback(100, 'Terminé')

            return {
                'text':     text,
                'segments': raw_words,
                'nb_frames': len(frames_landmarks),
                'nb_words':  len(words),
            }

        except Exception as e:
            logger.error(f'Erreur traitement vidéo: {e}')
            return {'text': '', 'segments': [], 'error': str(e)}
        finally:
            self.extractor.close()

    def _segment_sequence(self, landmarks: list, pause_frames: int = 5) -> list:
        """Segmente une séquence de landmarks en signes individuels."""
        if len(landmarks) < 10:
            return [landmarks]

        segments = []
        current  = []

        for i, lm in enumerate(landmarks):
            current.append(lm)

            if len(current) >= 30:
                segments.append(current[:30])
                current = current[15:]

        if len(current) >= 10:
            segments.append(current)

        return segments if segments else [landmarks]
