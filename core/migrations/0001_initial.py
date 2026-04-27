import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Adresse email')),
                ('prenom', models.CharField(max_length=50, verbose_name='Prénom')),
                ('nom', models.CharField(max_length=50, verbose_name='Nom')),
                ('role', models.CharField(choices=[('ADMIN', 'Administrateur'), ('UTILISATEUR', 'Utilisateur')], default='UTILISATEUR', max_length=20)),
                ('groups', models.ManyToManyField(blank=True, related_name='customuser_set', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='customuser_set', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Utilisateur',
                'verbose_name_plural': 'Utilisateurs',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='SignDictionary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mot', models.CharField(max_length=100, unique=True, verbose_name='Mot')),
                ('categorie', models.CharField(choices=[('ALPHABET', 'Alphabet'), ('SALUTATION', 'Salutation'), ('CHIFFRE', 'Chiffre'), ('COULEUR', 'Couleur'), ('FAMILLE', 'Famille'), ('QUOTIDIEN', 'Quotidien'), ('AUTRE', 'Autre')], default='AUTRE', max_length=20)),
                ('animation_glb', models.FileField(blank=True, null=True, upload_to='animations/')),
                ('video_demo', models.FileField(blank=True, null=True, upload_to='videos/')),
                ('description', models.TextField(blank=True)),
                ('difficulte', models.CharField(choices=[('FACILE', 'Facile'), ('MOYEN', 'Moyen'), ('DIFFICILE', 'Difficile')], default='FACILE', max_length=20)),
                ('est_dynamique', models.BooleanField(default=False)),
                ('nb_frames', models.IntegerField(default=0)),
                ('est_valide', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ajoute_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Signe LSF',
                'verbose_name_plural': 'Signes LSF',
                'ordering': ['mot'],
            },
        ),
        migrations.CreateModel(
            name='MLModelVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=20)),
                ('algorithme', models.CharField(choices=[('RANDOM_FOREST', 'Random Forest'), ('LSTM', 'LSTM'), ('HYBRIDE', 'Hybride RF+LSTM')], max_length=20)),
                ('nb_classes', models.IntegerField(default=0)),
                ('nb_samples', models.IntegerField(default=0)),
                ('accuracy', models.FloatField(default=0.0)),
                ('est_actif', models.BooleanField(default=False)),
                ('parametres', models.JSONField(default=dict)),
                ('trained_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Version modèle ML',
                'verbose_name_plural': 'Versions modèle ML',
                'ordering': ['-trained_at'],
            },
        ),
        migrations.CreateModel(
            name='TranslationSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('TEXT_TO_SIGN', 'Texte → Signe'), ('SIGN_TO_TEXT', 'Signe → Texte'), ('VIDEO_TO_TEXT', 'Vidéo → Texte')], max_length=20)),
                ('texte_entree', models.TextField(blank=True, null=True)),
                ('texte_sortie', models.TextField(blank=True, null=True)),
                ('nb_signes', models.IntegerField(default=0)),
                ('duree_ms', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('utilisateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Session traduction',
                'verbose_name_plural': 'Sessions traduction',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DatasetSample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('landmarks_data', models.JSONField(default=list)),
                ('source', models.CharField(choices=[('WEBCAM', 'Webcam'), ('VIDEO_IMPORT', 'Import vidéo'), ('SYNTHESE', 'Synthèse')], default='WEBCAM', max_length=20)),
                ('qualite', models.CharField(choices=[('BONNE', 'Bonne'), ('MOYENNE', 'Moyenne'), ('MAUVAISE', 'Mauvaise')], default='BONNE', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('signe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='core.signdictionary')),
            ],
            options={
                'verbose_name': 'Échantillon dataset',
                'verbose_name_plural': 'Échantillons dataset',
                'ordering': ['-created_at'],
            },
        ),
    ]
