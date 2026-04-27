"""
import_landmarks_json.py
Importe les landmarks depuis kaggle_landmarks.json (produit par extract_landmarks_script.py)
et ré-entraîne le Random Forest.

Usage :
    python manage.py import_landmarks_json
    python manage.py import_landmarks_json --clear   # vide anciens KAGGLE_IMG
    python manage.py import_landmarks_json --no-train
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import SignDictionary, DatasetSample

JSON_FILE = Path(__file__).resolve().parents[4] / 'kaggle_landmarks.json'


class Command(BaseCommand):
    help = 'Importe les landmarks extraits des images Kaggle et ré-entraîne le RF'

    def add_arguments(self, parser):
        parser.add_argument('--clear',    action='store_true',
                            help='Supprimer les anciens samples KAGGLE_IMG')
        parser.add_argument('--no-train', action='store_true',
                            help='Import uniquement, sans ré-entraîner')
        parser.add_argument('--file',     type=str, default=str(JSON_FILE),
                            help='Chemin du fichier JSON')

    def handle(self, *args, **options):
        json_path = Path(options['file'])
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== Import landmarks depuis JSON ===\n'
        ))

        if not json_path.exists():
            self.stdout.write(self.style.ERROR(
                f'  Fichier introuvable : {json_path}\n'
                '  Lancez d\'abord : python extract_landmarks_script.py\n'
            ))
            return

        if options['clear']:
            deleted = DatasetSample.objects.filter(source='KAGGLE_IMG').delete()[0]
            self.stdout.write(self.style.WARNING(
                f'  [CLEAN] {deleted} anciens samples KAGGLE_IMG supprimés\n'
            ))

        with open(json_path, 'r') as f:
            data = json.load(f)

        total_ok = total_skip = 0
        for label, landmarks_list in sorted(data.items()):
            sign = SignDictionary.objects.filter(mot__iexact=label).first()
            if not sign:
                self.stdout.write(self.style.WARNING(
                    f'  [!] "{label}" absent de la base — ignoré'
                ))
                total_skip += len(landmarks_list)
                continue

            objs = [
                DatasetSample(
                    signe=sign,
                    landmarks_data=lm[:63],
                    source='KAGGLE_IMG',
                    qualite='BONNE',
                )
                for lm in landmarks_list if len(lm) >= 63
            ]
            DatasetSample.objects.bulk_create(objs, batch_size=500)
            total_ok += len(objs)
            self.stdout.write(f'  [{label:2s}] {len(objs)} samples importés')

        self.stdout.write(self.style.SUCCESS(
            f'\n  Total importé : {total_ok} samples '
            f'({total_skip} ignorés — signe absent)\n'
        ))

        if not options['no_train']:
            self.stdout.write('  Lancement ré-entraînement RF...\n')
            from django.core.management import call_command
            call_command('generate_asl_training', retrain_only=True)
