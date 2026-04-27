import json
import base64
import asyncio
import logging
import time
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from collections import deque, Counter

logger = logging.getLogger(__name__)


class SignRecognitionConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classifier     = None
        self.mp_hands       = None   # utilisé uniquement en mode fallback (image)
        self.hands          = None
        self._ml_ready      = False
        self._ml_loading    = False
        self._last_pred     = 0.0
        # Fenêtre glissante pour majority-vote (lissage des prédictions RF)
        self._pred_history  = deque(maxlen=5)
        # 60 ms = ~16 pred/sec max (navigateur envoie à 12 fps → pas de perte)
        self._MIN_PRED_INTERVAL = 0.06

    # ── Connexion ──────────────────────────────────────────────────────────────

    async def connect(self):
        await self.accept()
        await self.send(json.dumps({
            'type':     'connection_established',
            'message':  'SignBridge WebSocket connecté',
            'ml_ready': False,
        }))
        if not self._ml_loading:
            self._ml_loading = True
            asyncio.ensure_future(self._init_ml_async())

    async def _init_ml_async(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._init_ml_sync)
        try:
            await self.send(json.dumps({
                'type':     'connection_established',
                'message':  'Modèle ML prêt' if self._ml_ready else 'ML non disponible',
                'ml_ready': self._ml_ready,
            }))
        except Exception:
            pass

    def _init_ml_sync(self):
        try:
            from ml_engine.gesture_classifier import GestureClassifier
            self.classifier = GestureClassifier()
            self.classifier.load_models()
            self._ml_ready   = True
            self._ml_loading = False
            logger.info('RF chargé — mode landmark-only actif')

            # MediaPipe Python disponible uniquement pour le fallback image
            try:
                import cv2
                import mediapipe as mp
                self.mp_hands = mp.solutions.hands
                self.hands    = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.70,
                    min_tracking_confidence=0.60,
                )
                logger.info('MediaPipe Python disponible (fallback image)')
            except Exception:
                logger.info('MediaPipe Python absent — mode landmark-only uniquement')

        except Exception as e:
            logger.warning(f'ML non disponible: {e}')
            self._ml_ready   = False
            self._ml_loading = False

    # ── Déconnexion ────────────────────────────────────────────────────────────

    async def disconnect(self, close_code):
        if self.hands:
            try: self.hands.close()
            except Exception: pass

    # ── Réception ─────────────────────────────────────────────────────────────

    async def receive(self, text_data):
        try:
            now = time.time()
            if now - self._last_pred < self._MIN_PRED_INTERVAL:
                return
            self._last_pred = now

            data = json.loads(text_data)
            loop = asyncio.get_running_loop()

            if 'landmarks' in data:
                # ── Chemin rapide : landmarks extraits par MediaPipe JS ────────
                # ~500 octets, pas de décodage image, pas de MediaPipe serveur
                result = await loop.run_in_executor(
                    None, self._predict_from_landmarks, data['landmarks']
                )
            elif 'frame' in data:
                # ── Fallback : image JPEG (si MediaPipe JS non disponible) ─────
                result = await loop.run_in_executor(
                    None, self._process_frame_sync, data['frame']
                )
            else:
                return

            if result:
                await self.send(json.dumps(result))

        except Exception as e:
            logger.error(f'Erreur receive: {e}')

    # ── Prédiction depuis landmarks (chemin rapide) ────────────────────────────

    def _predict_from_landmarks(self, landmarks_list):
        """
        Reçoit 63 floats (21 points × 3D normalisés) extraits par MediaPipe JS.
        Ne fait que la prédiction RF + majority vote → très rapide (~5 ms).
        """
        try:
            if not self._ml_ready or self.classifier is None:
                return {'type': 'no_hand', 'hand_detected': False, 'landmarks': [], 'ml_loading': True}

            features = np.array(landmarks_list, dtype=np.float32).reshape(1, -1)
            if features.shape[1] != 63:
                logger.warning(f'Landmarks: attendu 63 features, reçu {features.shape[1]}')
                return None

            gesture, confidence = self.classifier.predict_static(features)
            smoothed_conf       = self._smooth(gesture, float(confidence))

            return {
                'type':           'gesture_detected',
                'geste':          gesture,
                'confiance':      round(smoothed_conf, 3),
                'sign_type':      'static',
                'hand_detected':  True,
                'landmarks':      [],
                'low_confidence': smoothed_conf < 0.12,   # seulement si vraiment incertain
            }
        except Exception as e:
            logger.error(f'Erreur predict_from_landmarks: {e}')
            return None

    # ── Prédiction depuis image (fallback) ────────────────────────────────────

    def _process_frame_sync(self, frame_b64: str):
        try:
            if ',' in frame_b64:
                frame_b64 = frame_b64.split(',')[1]

            frame_bytes = base64.b64decode(frame_b64)
            nparr       = np.frombuffer(frame_bytes, np.uint8)

            import cv2
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return None

            frame     = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_LINEAR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if not self._ml_ready or self.hands is None:
                return {'type': 'no_hand', 'hand_detected': False, 'landmarks': [], 'ml_loading': True}

            results = self.hands.process(rgb_frame)
            if not results.multi_hand_landmarks:
                self._pred_history.clear()
                return {'type': 'no_hand', 'hand_detected': False, 'landmarks': []}

            hand_lm = results.multi_hand_landmarks[0]
            wrist   = hand_lm.landmark[0]
            mcp9    = hand_lm.landmark[9]
            # Normalisation d'échelle : distance poignet→MCP-majeur
            dx9 = mcp9.x - wrist.x; dy9 = mcp9.y - wrist.y; dz9 = mcp9.z - wrist.z
            scale = float(np.sqrt(dx9*dx9 + dy9*dy9 + dz9*dz9)) or 1.0
            features_vec = []
            for point in hand_lm.landmark:
                features_vec.extend([
                    (point.x - wrist.x) / scale,
                    (point.y - wrist.y) / scale,
                    (point.z - wrist.z) / scale,
                ])

            raw_lm   = [{'x': p.x, 'y': p.y, 'z': p.z} for p in hand_lm.landmark]
            features = np.array(features_vec, dtype=np.float32).reshape(1, -1)

            gesture, confidence = self.classifier.predict_static(features)
            smoothed_conf       = self._smooth(gesture, float(confidence))

            return {
                'type':           'gesture_detected',
                'geste':          gesture,
                'confiance':      round(smoothed_conf, 3),
                'sign_type':      'static',
                'hand_detected':  True,
                'landmarks':      raw_lm,
                'low_confidence': smoothed_conf < 0.12,
            }
        except Exception as e:
            logger.error(f'Erreur process_frame_sync: {e}')
            return None

    # ── Majority-vote smoothing ────────────────────────────────────────────────

    def _smooth(self, gesture: str, confidence: float) -> float:
        """
        Ajoute la prédiction à l'historique et retourne une confiance lissée.
        Si le signe courant est majoritaire dans la fenêtre → boost confiance.
        Sinon → pénalité (signal instable).
        """
        self._pred_history.append((gesture, confidence))

        if len(self._pred_history) < 3:
            return confidence

        labels = [g for g, _ in self._pred_history]
        votes  = Counter(labels)
        best_label, count = votes.most_common(1)[0]

        if best_label == gesture:
            vote_ratio = count / len(self._pred_history)
            return min(confidence * (0.70 + 0.30 * vote_ratio), 1.0)
        else:
            return confidence * 0.60
