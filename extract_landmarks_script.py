"""
Script standalone d'extraction de landmarks MediaPipe depuis les images kaggle_dataset/.
Exécuter AVANT manage.py (pas de Django, pas de TensorFlow chargé).

Sortie : kaggle_landmarks.json
    { "A": [[63 floats], ...], "B": [...], ..., "0": [...], ... }

Usage :
    python extract_landmarks_script.py
    python extract_landmarks_script.py --limit 400
    python extract_landmarks_script.py --sign A
"""
import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent
KAGGLE    = BASE_DIR / 'kaggle_dataset'
COMBINED  = KAGGLE / 'processed_combine_asl_dataset'
DIGITS_DS = KAGGLE / 'American Sign Language Digits Dataset'
OUT_FILE  = BASE_DIR / 'kaggle_landmarks.json'

IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}


def init_mp():
    import mediapipe as mp
    return mp.solutions.hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.2,  # seuil bas pour images recadrées
    )


def extract(hands, img_path: Path):
    import cv2
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)
    if not res.multi_hand_landmarks:
        return None
    lm  = res.multi_hand_landmarks[0]
    w   = lm.landmark[0]
    vec = []
    for pt in lm.landmark:
        vec.extend([pt.x - w.x, pt.y - w.y, pt.z - w.z])
    return vec


def sample_images(folder: Path, limit: int):
    imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    if limit and len(imgs) > limit:
        step = max(1, len(imgs) // limit)
        imgs = imgs[::step][:limit]
    return imgs


def process_folder(hands, folder: Path, label: str, limit: int):
    imgs = sample_images(folder, limit)
    ok_lm, fail = [], 0
    for p in imgs:
        lm = extract(hands, p)
        if lm:
            ok_lm.append(lm)
        else:
            fail += 1
    rate = len(ok_lm) / (len(ok_lm) + fail) * 100 if (ok_lm or fail) else 0
    print(f'  [{label:2s}] {len(ok_lm):4d} OK  {fail:3d} sans main  ({rate:.0f}%)')
    return ok_lm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--sign',  type=str, default=None)
    args = parser.parse_args()

    limit     = args.limit
    sign_only = args.sign.upper() if args.sign else None

    print('\n=== Extraction landmarks MediaPipe depuis images ===\n')
    print('Initialisation MediaPipe...')
    hands = init_mp()

    data = {}  # label → liste de vecteurs 63 floats

    # ── Source 1 : processed_combine_asl_dataset ──────────────────────────────
    if COMBINED.exists():
        print(f'\n[SOURCE 1] {COMBINED.name}')
        for folder in sorted(COMBINED.iterdir()):
            if not folder.is_dir():
                continue
            label = folder.name.upper()
            if sign_only and label != sign_only:
                continue
            lms = process_folder(hands, folder, label, limit)
            if lms:
                data.setdefault(label, []).extend(lms)

    # ── Source 2 : ASL Digits Dataset (chiffres, ~500 images/chiffre) ─────────
    if DIGITS_DS.exists():
        print(f'\n[SOURCE 2] {DIGITS_DS.name}')
        for d_folder in sorted(DIGITS_DS.iterdir()):
            if not d_folder.is_dir():
                continue
            label = d_folder.name
            if not label.isdigit():
                continue
            if sign_only and label != sign_only:
                continue
            # Sous-dossier "Input Images - Sign X"
            sub = next((x for x in d_folder.iterdir()
                        if x.is_dir() and 'input' in x.name.lower()), d_folder)
            extra = min(limit, 300) if limit else 300
            lms = process_folder(hands, sub, label, extra)
            if lms:
                data.setdefault(label, []).extend(lms)

    hands.close()

    # ── Analyse des poses (quels doigts étendus) ──────────────────────────────
    print('\n' + '-' * 60)
    print('ANALYSE POSES REELLES (seuil distance tip/mcp > 0.15)')
    print('Format : [pouce index majeur annulaire auriculaire]')
    print('-' * 60)

    TIP = [4, 8, 12, 16, 20]
    MCP = [2, 5,  9, 13, 17]

    pose_report = {}
    for label in sorted(data.keys(), key=lambda x: (not x.isdigit(), x)):
        vecs  = np.array(data[label])
        mean  = vecs.mean(axis=0).reshape(21, 3)
        ext   = []
        for ti, mi in zip(TIP, MCP):
            dist = float(np.linalg.norm(mean[ti] - mean[mi]))
            ext.append(1 if dist > 0.15 else 0)
        pose_report[label] = ext
        print(f'  {label:2s} | {ext}  ({len(data[label])} samples)')

    print('─' * 60)

    # ── Sauvegarde JSON ────────────────────────────────────────────────────────
    out = {k: [lm for lm in v] for k, v in data.items()}
    with open(OUT_FILE, 'w') as f:
        json.dump(out, f)

    total = sum(len(v) for v in data.values())
    print(f'\nSauvegardé : {OUT_FILE}  ({total} landmarks au total)')
    print('Lancer ensuite : python manage.py import_landmarks_json\n')


if __name__ == '__main__':
    main()
