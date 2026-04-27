import logging
import numpy as np

logger = logging.getLogger(__name__)


class LandmarkExtractor:
    """Extrait et normalise les landmarks de mains via MediaPipe."""

    def __init__(self, max_num_hands=2):
        self.max_num_hands = max_num_hands
        self._hands = None
        self._mp_hands = None
        self._initialized = False

    def _init_mediapipe(self):
        if self._initialized:
            return True
        try:
            import mediapipe as mp
            self._mp_hands = mp.solutions.hands
            self._hands = self._mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=self.max_num_hands,
                min_detection_confidence=0.5,
            )
            self._initialized = True
            return True
        except ImportError:
            logger.error('MediaPipe non installé')
            return False
        except Exception as e:
            logger.error(f'Erreur init MediaPipe: {e}')
            return False

    def extract_from_frame(self, frame_rgb: np.ndarray) -> dict:
        """
        Extrait les landmarks d'une frame RGB.
        Retourne dict: {landmarks, hand_detected, num_hands, raw_landmarks}
        """
        if not self._init_mediapipe():
            return self._empty_result()

        try:
            results = self._hands.process(frame_rgb)

            if not results.multi_hand_landmarks:
                return self._empty_result()

            all_landmarks = []
            raw_landmarks = []

            for hand_lm in results.multi_hand_landmarks:
                wrist = hand_lm.landmark[0]
                normalized = []
                raw = []

                for point in hand_lm.landmark:
                    normalized.extend([
                        point.x - wrist.x,
                        point.y - wrist.y,
                        point.z - wrist.z,
                    ])
                    raw.append({'x': point.x, 'y': point.y, 'z': point.z})

                all_landmarks.append(normalized)
                raw_landmarks.append(raw)

            primary = np.array(all_landmarks[0], dtype=np.float32)

            return {
                'landmarks':     primary.tolist(),
                'all_landmarks': [lm for lm in all_landmarks],
                'raw_landmarks': raw_landmarks[0],
                'hand_detected': True,
                'num_hands':     len(all_landmarks),
            }

        except Exception as e:
            logger.error(f'Erreur extraction landmarks: {e}')
            return self._empty_result()

    def extract_from_video(self, video_path: str, fps_target: int = 10) -> list:
        """
        Extrait les landmarks de chaque frame d'une vidéo.
        Retourne liste de vecteurs landmarks.
        """
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f'Impossible d\'ouvrir la vidéo: {video_path}')
                return []

            fps_video = cap.get(cv2.CAP_PROP_FPS) or 30
            skip = max(1, int(fps_video / fps_target))

            frames_landmarks = []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % skip == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = self.extract_from_frame(rgb)
                    if result['hand_detected']:
                        frames_landmarks.append(result['landmarks'])

                frame_idx += 1

            cap.release()
            return frames_landmarks

        except Exception as e:
            logger.error(f'Erreur extraction vidéo: {e}')
            return []

    def normalize_sequence(self, sequence: list, target_len: int = 30) -> np.ndarray:
        """Normalise une séquence de landmarks à une longueur cible."""
        if not sequence:
            return np.zeros((target_len, 63), dtype=np.float32)

        arr = np.array(sequence, dtype=np.float32)
        n   = len(arr)

        if n == target_len:
            return arr
        if n > target_len:
            indices = np.linspace(0, n - 1, target_len, dtype=int)
            return arr[indices]

        result = np.zeros((target_len, arr.shape[1] if arr.ndim > 1 else 63), dtype=np.float32)
        result[:n] = arr
        return result

    @staticmethod
    def _empty_result():
        return {
            'landmarks':     [],
            'all_landmarks': [],
            'raw_landmarks': [],
            'hand_detected': False,
            'num_hands':     0,
        }

    def close(self):
        if self._hands:
            try:
                self._hands.close()
            except Exception:
                pass
        self._initialized = False
