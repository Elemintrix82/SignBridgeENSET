"""
import_kaggle_asl.py
Télécharge le dataset Kaggle "MediaPipe Processed ASL Dataset" et l'importe en base.

Prérequis :
    1. Créer un compte Kaggle → Settings → API → "Create Legacy API Key"
    2. Placer kaggle.json dans l'un de ces emplacements (cherché dans cet ordre) :
         - Racine du projet  (signbridge/kaggle.json)
         - Téléchargements   (C:\\Users\\<vous>\\Downloads\\kaggle.json)
         - Dossier par défaut (C:\\Users\\<vous>\\.kaggle\\kaggle.json)
    3. Ou passer le chemin explicitement :
         python manage.py import_kaggle_asl --credentials "C:\\chemin\\kaggle.json"
    4. pip install kaggle

Usage :
    python manage.py import_kaggle_asl
    python manage.py import_kaggle_asl --credentials "C:\\Users\\ELEMINTRIX\\Downloads\\kaggle.json"
    python manage.py import_kaggle_asl --limit 500   # 500 samples max par signe
"""
import os
import csv
import json
import shutil
import tempfile
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import SignDictionary, DatasetSample

DATASET_SLUG = 'vignonantoine/mediapipe-processed-asl-dataset'

# Emplacements cherchés automatiquement (dans l'ordre)
KAGGLE_SEARCH_PATHS = [
    Path(__file__).resolve().parents[4] / 'kaggle.json',        # racine du projet
    Path.home() / 'Downloads'     / 'kaggle.json',              # Téléchargements FR
    Path.home() / 'Téléchargements' / 'kaggle.json',            # alias accent
    Path.home() / '.kaggle'       / 'kaggle.json',              # emplacement officiel
]


def _find_kaggle_json(explicit: str | None) -> Path | None:
    """Retourne le premier kaggle.json trouvé, ou None."""
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    for p in KAGGLE_SEARCH_PATHS:
        if p.exists():
            return p
    return None


def _install_kaggle_json(src: Path) -> Path:
    """Copie kaggle.json vers ~/.kaggle/kaggle.json et fixe les permissions."""
    dest_dir = Path.home() / '.kaggle'
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / 'kaggle.json'
    shutil.copy2(src, dest)
    try:
        dest.chmod(0o600)
    except Exception:
        pass
    return dest


class Command(BaseCommand):
    help = 'Importe le dataset Kaggle ASL MediaPipe en base'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0,
                            help='Samples max par signe (0 = tout)')
        parser.add_argument('--clear', action='store_true',
                            help='Vide les samples Kaggle existants avant import')
        parser.add_argument('--credentials', type=str, default=None,
                            help='Chemin explicite vers kaggle.json')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== SignBridge — Import Kaggle ASL ===\n'
        ))

        # ── 1. Localiser kaggle.json ──────────────────────────────────────────
        src = _find_kaggle_json(options['credentials'])
        if src is None:
            checked = '\n'.join(f'     • {p}' for p in KAGGLE_SEARCH_PATHS)
            self.stdout.write(self.style.ERROR(
                '\n  [ERREUR] kaggle.json introuvable !\n\n'
                '  Emplacements cherches :\n'
                f'{checked}\n\n'
                '  Solutions :\n'
                '  A) Deposez kaggle.json dans la racine du projet ou dans Downloads\n'
                '  B) Passez le chemin exact :\n'
                '     python manage.py import_kaggle_asl --credentials "C:\\...\\kaggle.json"\n'
            ))
            return

        self.stdout.write(f'  [OK] kaggle.json trouve : {src}')

        # ── 2. Installer dans ~/.kaggle si nécessaire ─────────────────────────
        default_dest = Path.home() / '.kaggle' / 'kaggle.json'
        if src != default_dest:
            _install_kaggle_json(src)
            self.stdout.write(f'  [OK] Copie vers {default_dest}')

        # ── 3. Télécharger le dataset ─────────────────────────────────────────
        self.stdout.write(f'  Telechargement de {DATASET_SLUG}...')
        try:
            import kaggle
            kaggle.api.authenticate()
            with tempfile.TemporaryDirectory() as tmp:
                kaggle.api.dataset_download_files(
                    DATASET_SLUG, path=tmp, unzip=True, quiet=False
                )
                self._import_csv(Path(tmp), options['limit'], options['clear'])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n  Erreur Kaggle : {e}'))

    # ── Import CSV → base ─────────────────────────────────────────────────────

    def _import_csv(self, folder: Path, limit: int, clear: bool):
        csv_files = list(folder.glob('**/*.csv'))
        if not csv_files:
            self.stdout.write(self.style.ERROR('  Aucun CSV trouvé dans le dataset'))
            return

        self.stdout.write(f'  {len(csv_files)} fichier(s) CSV trouvé(s)')

        if clear:
            deleted = DatasetSample.objects.filter(source='KAGGLE').delete()[0]
            self.stdout.write(f'  [CLEAN] {deleted} anciens samples Kaggle supprimés')

        total = 0
        for csv_path in csv_files:
            total += self._load_csv(csv_path, limit)

        self.stdout.write(self.style.SUCCESS(f'\n  Total importé : {total} samples'))

        if total > 0:
            self.stdout.write('\n  Lancement de l\'entraînement RF...')
            from django.core.management import call_command
            call_command('generate_asl_training', retrain_only=True)

    def _load_csv(self, csv_path: Path, limit: int) -> int:
        created = 0
        counts  = {}

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows   = list(reader)

        for row in rows:
            # Déterminer le label (colonne 'label' ou 'sign' ou première colonne)
            label = (row.get('label') or row.get('sign') or
                     row.get('class') or list(row.values())[0] or '').upper().strip()
            if not label:
                continue

            # Trouver le signe en base
            sign = SignDictionary.objects.filter(mot__iexact=label).first()
            if not sign:
                continue

            if limit and counts.get(label, 0) >= limit:
                continue

            # Extraire les 63 landmarks
            try:
                vals = []
                for i in range(21):
                    vals.append(float(row.get(f'x{i}') or row.get(f'landmark_{i}_x') or 0))
                    vals.append(float(row.get(f'y{i}') or row.get(f'landmark_{i}_y') or 0))
                    vals.append(float(row.get(f'z{i}') or row.get(f'landmark_{i}_z') or 0))
                if len(vals) < 63:
                    # Essayer extraction par ordre de colonnes numériques
                    num_cols = [v for k, v in row.items()
                                if k != 'label' and k != 'sign' and k != 'class']
                    vals = [float(v) for v in num_cols[:63]]
            except (ValueError, KeyError):
                continue

            if len(vals) < 63:
                continue

            DatasetSample.objects.create(
                signe=sign,
                landmarks_data=vals[:63],
                source='KAGGLE',
                qualite='BONNE',
            )
            counts[label] = counts.get(label, 0) + 1
            created += 1

        for lbl, cnt in sorted(counts.items()):
            self.stdout.write(f'  [+] {lbl} : {cnt} samples')

        return created
