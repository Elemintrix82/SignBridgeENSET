"""
extract_from_images.py
Extrait les landmarks MediaPipe directement depuis les images JPEG/PNG
du dossier kaggle_dataset/, sauvegarde en base et ré-entraîne le RF.

Usage :
    python manage.py extract_from_images
    python manage.py extract_from_images --limit 500    # max 500 images/signe
    python manage.py extract_from_images --clear        # vide anciens KAGGLE_IMG
    python manage.py extract_from_images --no-train     # extraction seulement

Sources utilisées :
    • kaggle_dataset/processed_combine_asl_dataset/a-z/  (lettres, ~2000-5500/lettre)
    • kaggle_dataset/processed_combine_asl_dataset/0-9/  (chiffres, ~62-113/chiffre)
    • kaggle_dataset/American Sign Language Digits Dataset/0-9/ (chiffres, ~500/chiffre)
"""
import os
import numpy as np
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import SignDictionary, DatasetSample

IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}

# Chemins des datasets d'images
BASE = Path(__file__).resolve().parents[4] / 'kaggle_dataset'
COMBINED  = BASE / 'processed_combine_asl_dataset'
DIGITS_DS = BASE / 'American Sign Language Digits Dataset'


def _init_mediapipe():
    import mediapipe as mp
    hands = mp.solutions.hands.Hands(
        static_image_mode=True,      # mode image statique (plus précis)
        max_num_hands=1,
        min_detection_confidence=0.4,
    )
    return hands


def _extract_landmarks(hands, img_path: Path):
    """Retourne un vecteur de 63 floats (landmarks normalisés/poignet) ou None."""
    import cv2
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    if not results.multi_hand_landmarks:
        return None
    lm_obj = results.multi_hand_landmarks[0]
    wrist = lm_obj.landmark[0]
    vec = []
    for pt in lm_obj.landmark:
        vec.extend([pt.x - wrist.x, pt.y - wrist.y, pt.z - wrist.z])
    return vec  # 63 valeurs


def _images_in(folder: Path, limit: int):
    """Retourne jusqu'à `limit` chemins d'images dans un dossier."""
    imgs = [p for p in folder.iterdir()
            if p.suffix.lower() in IMAGE_EXTS]
    if limit and len(imgs) > limit:
        # Échantillonnage régulier pour couvrir la diversité
        step = len(imgs) // limit
        imgs = imgs[::step][:limit]
    return imgs


class Command(BaseCommand):
    help = 'Extrait landmarks MediaPipe depuis les images kaggle_dataset/ et ré-entraîne le RF'

    def add_arguments(self, parser):
        parser.add_argument('--limit',    type=int, default=500,
                            help='Max images traitées par signe (0=toutes, défaut=500)')
        parser.add_argument('--clear',    action='store_true',
                            help='Supprimer les anciens samples KAGGLE_IMG avant extraction')
        parser.add_argument('--no-train', action='store_true',
                            help='Extraire seulement, sans ré-entraîner le RF')
        parser.add_argument('--sign',     type=str, default=None,
                            help='Traiter un seul signe (ex: --sign A ou --sign 3)')

    def handle(self, *args, **options):
        limit     = options['limit']
        clear     = options['clear']
        no_train  = options['no_train']
        sign_only = options['sign'].upper() if options['sign'] else None

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== SignBridge — Extraction landmarks depuis images ===\n'
        ))

        if clear:
            deleted = DatasetSample.objects.filter(source='KAGGLE_IMG').delete()[0]
            self.stdout.write(self.style.WARNING(f'  [CLEAN] {deleted} anciens samples KAGGLE_IMG supprimés\n'))

        # ── Init MediaPipe ─────────────────────────────────────────────────────
        self.stdout.write('  Initialisation MediaPipe...')
        try:
            hands = _init_mediapipe()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erreur MediaPipe : {e}'))
            return

        total_ok = total_fail = 0
        sign_stats = {}   # {label: {'ok': int, 'fail': int, 'mean_lm': np.array}}

        # ══════════════════════════════════════════════════════════════════════
        # SOURCE 1 — processed_combine_asl_dataset  (lettres a-z + chiffres 0-9)
        # ══════════════════════════════════════════════════════════════════════
        if COMBINED.exists():
            self.stdout.write(f'\n  [SOURCE 1] {COMBINED.name}')
            for folder in sorted(COMBINED.iterdir()):
                if not folder.is_dir():
                    continue
                label = folder.name.upper()  # 'a' → 'A', '0' → '0'
                if sign_only and label != sign_only:
                    continue
                ok, fail, mean_lm = self._process_folder(
                    hands, folder, label, limit, sign_stats)
                total_ok   += ok
                total_fail += fail
        else:
            self.stdout.write(self.style.WARNING(f'  [!] Dossier absent : {COMBINED}'))

        # ══════════════════════════════════════════════════════════════════════
        # SOURCE 2 — ASL Digits Dataset  (chiffres 0-9, ~500 images/chiffre)
        #            uniquement si le combined a peu d'images pour les chiffres
        # ══════════════════════════════════════════════════════════════════════
        if DIGITS_DS.exists():
            self.stdout.write(f'\n  [SOURCE 2] {DIGITS_DS.name}')
            for digit_folder in sorted(DIGITS_DS.iterdir()):
                if not digit_folder.is_dir():
                    continue
                label = digit_folder.name  # '0' … '9'
                if not label.isdigit():
                    continue
                if sign_only and label != sign_only:
                    continue
                # Chercher sous-dossier "Input Images - Sign X"
                input_sub = next(
                    (d for d in digit_folder.iterdir()
                     if d.is_dir() and 'input' in d.name.lower()), None)
                src = input_sub if input_sub else digit_folder
                # Limiter à 300 supplémentaires pour les chiffres
                extra_limit = min(limit, 300) if limit else 300
                ok, fail, _ = self._process_folder(
                    hands, src, label, extra_limit, sign_stats)
                total_ok   += ok
                total_fail += fail
        else:
            self.stdout.write(self.style.WARNING(f'  [!] Dossier absent : {DIGITS_DS}'))

        hands.close()

        # ── Résumé extraction ──────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\n  Extraction terminée : {total_ok} landmarks sauvegardés '
            f'({total_fail} images sans main détectée)\n'
        ))

        # ── Analyse poses moyennes → rapport ──────────────────────────────────
        self._report_poses(sign_stats)

        # ── Ré-entraînement ────────────────────────────────────────────────────
        if not no_train:
            self.stdout.write('\n  Lancement ré-entraînement RF...')
            from django.core.management import call_command
            call_command('generate_asl_training', retrain_only=True)

    # ── Traitement d'un dossier ────────────────────────────────────────────────

    def _process_folder(self, hands, folder: Path, label: str,
                        limit: int, sign_stats: dict):
        sign = SignDictionary.objects.filter(mot__iexact=label).first()
        if not sign:
            self.stdout.write(self.style.WARNING(f'    [!] "{label}" absent de la base — ignoré'))
            return 0, 0, None

        images = _images_in(folder, limit)
        if not images:
            self.stdout.write(self.style.WARNING(f'    [!] Aucune image dans {folder}'))
            return 0, 0, None

        ok = fail = 0
        landmarks_accumulator = []
        batch = []

        for img_path in images:
            lm = _extract_landmarks(hands, img_path)
            if lm is None:
                fail += 1
                continue
            batch.append(DatasetSample(
                signe=sign, landmarks_data=lm,
                source='KAGGLE_IMG', qualite='BONNE',
            ))
            landmarks_accumulator.append(lm)
            ok += 1
            if len(batch) >= 200:
                DatasetSample.objects.bulk_create(batch, batch_size=200)
                batch.clear()

        if batch:
            DatasetSample.objects.bulk_create(batch, batch_size=200)

        # Stocker la moyenne pour analyse des poses
        mean_lm = np.mean(landmarks_accumulator, axis=0) if landmarks_accumulator else None
        if label not in sign_stats:
            sign_stats[label] = {'ok': 0, 'fail': 0, 'mean_lm': None}
        sign_stats[label]['ok']   += ok
        sign_stats[label]['fail'] += fail
        if mean_lm is not None:
            if sign_stats[label]['mean_lm'] is None:
                sign_stats[label]['mean_lm'] = mean_lm
            else:
                sign_stats[label]['mean_lm'] = (sign_stats[label]['mean_lm'] + mean_lm) / 2

        rate = ok / (ok + fail) * 100 if (ok + fail) else 0
        self.stdout.write(
            f'    [{label}] {ok} OK / {fail} sans main  ({rate:.0f}% détection)'
        )
        return ok, fail, mean_lm

    # ── Analyse des poses moyennes ─────────────────────────────────────────────

    def _report_poses(self, sign_stats: dict):
        """
        Analyse les landmarks moyens extraits des vraies images
        et détermine quels doigts sont étendus pour chaque signe.
        Affiche un rapport pour aider à corriger HandSignRenderer.POSES.
        """
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write('  ANALYSE DES POSES RÉELLES (landmarks moyens)')
        self.stdout.write('─' * 60)
        self.stdout.write('  Format: [pouce index majeur annulaire auriculaire]')
        self.stdout.write('  1=étendu  0=replié  (seuil distance tip/palm > 0.15)\n')

        # Indices MediaPipe des tips et MCPs
        # landmark order: wrist=0, thumb=[1-4], index=[5-8], middle=[9-12],
        #                 ring=[13-16], pinky=[17-20]
        TIP_IDX  = [4, 8, 12, 16, 20]   # tip de chaque doigt
        MCP_IDX  = [2, 5,  9, 13, 17]   # base de chaque doigt

        for label in sorted(sign_stats.keys(),
                            key=lambda x: (not x.isdigit(), x)):
            stats = sign_stats[label]
            if stats['mean_lm'] is None:
                continue
            lm = np.array(stats['mean_lm']).reshape(21, 3)

            ext = []
            for tip_i, mcp_i in zip(TIP_IDX, MCP_IDX):
                dist = float(np.linalg.norm(lm[tip_i] - lm[mcp_i]))
                ext.append(1 if dist > 0.15 else 0)

            ok   = stats['ok']
            fail = stats['fail']
            self.stdout.write(
                f'  {label:2s} | ext={ext} | '
                f'{ok} images OK  ({fail} sans détection)'
            )

        self.stdout.write('─' * 60 + '\n')
