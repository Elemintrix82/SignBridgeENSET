from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Entraîne les modèles ML SignBridge (RF + LSTM)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--algo',
            choices=['rf', 'lstm', 'all'],
            default='all',
            help='Algorithme à entraîner',
        )

    def handle(self, *args, **options):
        algo = options['algo']
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n=== Entraînement SignBridge ({algo}) ===\n'))

        try:
            from ml_engine.model_trainer import ModelTrainer
            trainer = ModelTrainer()

            if algo == 'rf':
                result = trainer.train_random_forest()
                self._print_result('Random Forest', result)
            elif algo == 'lstm':
                result = trainer.train_lstm()
                self._print_result('LSTM', result)
            else:
                results = trainer.train_all()
                for name, result in results.items():
                    self._print_result(name, result)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}'))

    def _print_result(self, name, result):
        if result.get('status') == 'success':
            acc = result.get('accuracy', 0)
            nb  = result.get('nb_classes', 0)
            self.stdout.write(self.style.SUCCESS(
                f'✅ {name}: accuracy={acc:.4f}, classes={nb}'
            ))
        elif result.get('status') == 'skipped':
            self.stdout.write(self.style.WARNING(
                f'⚠️  {name}: ignoré — {result.get("reason", "inconnu")}'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'❌ {name}: erreur — {result.get("error", "inconnu")}'
            ))
