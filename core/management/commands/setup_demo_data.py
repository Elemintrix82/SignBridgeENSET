from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import SignDictionary

User = get_user_model()

LSF_DESCRIPTIONS = {
    'A': 'Poing fermé, pouce sur le côté. Doigts repliés, pouce visible.',
    'B': 'Quatre doigts tendus et joints, pouce replié sur la paume.',
    'C': 'Main en forme de C, doigts légèrement courbés, paume vers soi.',
    'D': 'Index tendu et courbé, autres doigts repliés, pouce touche le majeur.',
    'E': 'Doigts repliés vers la paume, ongles vers le bas.',
    'F': 'Pouce et index forment un cercle, trois autres doigts tendus.',
    'G': 'Index et pouce pointent horizontalement vers la gauche.',
    'H': 'Index et majeur tendus côte à côte horizontalement.',
    'I': 'Seul l\'auriculaire est tendu, les autres repliés.',
    'J': 'Auriculaire tendu, décrit un J dans l\'air.',
    'K': 'Index et majeur en V, pouce entre les deux.',
    'L': 'Index tendu vers le haut, pouce tendu horizontalement, forme un L.',
    'M': 'Trois doigts repliés sur le pouce, auriculaire replié.',
    'N': 'Deux doigts repliés sur le pouce.',
    'O': 'Tous les doigts forment un O avec le pouce.',
    'P': 'Comme K mais pointé vers le bas.',
    'Q': 'Comme G mais pointé vers le bas.',
    'R': 'Index et majeur croisés, tendus.',
    'S': 'Poing fermé, pouce sur les doigts repliés.',
    'T': 'Pouce entre index et majeur replié.',
    'U': 'Index et majeur tendus et joints verticalement.',
    'V': 'Index et majeur tendus en V (victoire).',
    'W': 'Index, majeur et annulaire tendus, écartés.',
    'X': 'Index replié en crochet.',
    'Y': 'Pouce et auriculaire tendus, autres repliés.',
    'Z': 'Index tendu, dessine un Z dans l\'air.',
    '0': 'Tous les doigts forment un O fermé avec le pouce.',
    '1': 'Index tendu vers le haut, autres doigts repliés.',
    '2': 'Index et majeur tendus en V.',
    '3': 'Pouce, index et majeur tendus.',
    '4': 'Quatre doigts tendus, pouce replié sur la paume.',
    '5': 'Cinq doigts ouverts et écartés, paume vers l\'avant.',
    '6': 'Deux mains : main gauche ouverte (5 doigts), main droite index tendu (1).',
    '7': 'Deux mains : main gauche ouverte (5 doigts), main droite index+majeur en V (2).',
    '8': 'Deux mains : main gauche ouverte (5 doigts), main droite index+majeur+annulaire (3).',
    '9': 'Deux mains : main gauche ouverte (5 doigts), main droite 4 doigts tendus sans pouce (4).',
}

DEMO_SIGNS = (
    [(l, 'ALPHABET') for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] +
    [(str(n), 'CHIFFRE') for n in range(10)]
)


class Command(BaseCommand):
    help = 'Crée les données de démonstration SignBridge (A-Z + 0-9)'

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Supprime les signes des anciennes catégories avant création')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== SignBridge - Données démo ===\n'))

        if options['clean']:
            old = SignDictionary.objects.exclude(categorie__in=['ALPHABET', 'CHIFFRE'])
            count = old.count()
            old.delete()
            self.stdout.write(self.style.WARNING(f'  [CLEAN] {count} anciens signes supprimés'))

        admin = self._create_user(
            email='admin@signbridge.fr',
            password='Admin@2024',
            prenom='Admin',
            nom='SignBridge',
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
        )

        self._create_user(
            email='demo@signbridge.fr',
            password='Demo@2024',
            prenom='Demo',
            nom='Utilisateur',
            role='UTILISATEUR',
        )

        created = updated = 0
        for mot, categorie in DEMO_SIGNS:
            desc = LSF_DESCRIPTIONS.get(mot, f'Signe LSF pour {mot}')
            sign, is_new = SignDictionary.objects.get_or_create(
                mot=mot,
                defaults={
                    'categorie':     categorie,
                    'description':   desc,
                    'difficulte':    'FACILE',
                    'est_dynamique': False,
                    'est_valide':    True,
                    'ajoute_par':    admin,
                }
            )
            if is_new:
                created += 1
                self.stdout.write(f'  [+] {mot} ({categorie})')
            else:
                changed = False
                if sign.categorie != categorie:
                    sign.categorie = categorie
                    changed = True
                if not sign.est_valide:
                    sign.est_valide = True
                    changed = True
                if not sign.description:
                    sign.description = desc
                    changed = True
                if changed:
                    sign.save()
                    updated += 1
                    self.stdout.write(f'  [~] {mot} mis à jour')

        self.stdout.write(self.style.SUCCESS(
            f'\n[DONE] {created} signes créés, {updated} mis à jour\n'
            f'   admin@signbridge.fr / Admin@2024\n'
            f'   demo@signbridge.fr  / Demo@2024\n'
        ))

    def _create_user(self, email, password, prenom, nom, role, **extra):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'prenom': prenom, 'nom': nom, 'role': role, **extra}
        )
        if created:
            user.set_password(password)
            for k, v in extra.items():
                setattr(user, k, v)
            user.save()
            self.stdout.write(f'  [OK] Utilisateur {email} créé')
        else:
            self.stdout.write(f'  [--] Utilisateur {email} existe déjà')
        return user
