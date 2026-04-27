from django.core.management.base import BaseCommand
from pathlib import Path


class Command(BaseCommand):
    help = 'Extrait les landmarks depuis les vidéos du dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default='dataset/raw',
            help='Répertoire source des vidéos',
        )
        parser.add_argument(
            '--sign',
            default=None,
            help='Extraire uniquement pour ce signe (mot)',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['source'])
        sign_filter = options.get('sign')

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Extraction landmarks ===\n'))

        if not source_dir.exists():
            self.stdout.write(self.style.ERROR(f'Répertoire introuvable: {source_dir}'))
            return

        try:
            from ml_engine.landmark_extractor import LandmarkExtractor
            from ml_engine.dataset_manager import DatasetManager
            from core.models import SignDictionary

            extractor = LandmarkExtractor()
            dm        = DatasetManager()

            video_extensions = {'.mp4', '.avi', '.mov', '.webm'}
            total = 0

            for video_file in source_dir.rglob('*'):
                if video_file.suffix.lower() not in video_extensions:
                    continue

                sign_name = video_file.parent.name
                if sign_filter and sign_name.lower() != sign_filter.lower():
                    continue

                try:
                    sign = SignDictionary.objects.get(mot__iexact=sign_name)
                except SignDictionary.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  Signe "{sign_name}" non trouvé en base'))
                    continue

                self.stdout.write(f'  Traitement: {video_file.name}...')
                landmarks_seq = extractor.extract_from_video(str(video_file))

                if landmarks_seq:
                    sample_id = dm.save_sample(sign.pk, landmarks_seq, source='VIDEO_IMPORT')
                    if sample_id:
                        total += 1
                        self.stdout.write(self.style.SUCCESS(f'    ✓ {len(landmarks_seq)} frames → sample #{sample_id}'))
                    else:
                        self.stdout.write(self.style.ERROR('    ✗ Erreur sauvegarde'))
                else:
                    self.stdout.write(self.style.WARNING('    ⚠ Aucune main détectée'))

            extractor.close()
            self.stdout.write(self.style.SUCCESS(f'\n✅ {total} samples créés'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}'))
