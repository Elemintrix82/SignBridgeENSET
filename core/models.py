from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('prenom', 'Admin')
        extra_fields.setdefault('nom', 'SignBridge')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('UTILISATEUR', 'Utilisateur'),
    ]

    username = None
    email    = models.EmailField(unique=True, verbose_name='Adresse email')
    prenom   = models.CharField(max_length=50, verbose_name='Prénom')
    nom      = models.CharField(max_length=50, verbose_name='Nom')
    role     = models.CharField(max_length=20, choices=ROLE_CHOICES, default='UTILISATEUR')

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['prenom', 'nom']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f'{self.prenom} {self.nom} <{self.email}>'

    @property
    def full_name(self):
        return f'{self.prenom} {self.nom}'

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    @property
    def initials(self):
        return f'{self.prenom[0]}{self.nom[0]}'.upper() if self.prenom and self.nom else 'U'


class SignDictionary(models.Model):
    CATEGORIE_CHOICES = [
        ('ALPHABET', 'Alphabet'),
        ('CHIFFRE',  'Chiffre'),
    ]
    DIFFICULTE_CHOICES = [
        ('FACILE',   'Facile'),
        ('MOYEN',    'Moyen'),
        ('DIFFICILE','Difficile'),
    ]

    mot           = models.CharField(max_length=100, unique=True, verbose_name='Mot')
    categorie     = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='ALPHABET')
    animation_glb = models.FileField(upload_to='animations/', null=True, blank=True)
    video_demo    = models.FileField(upload_to='videos/', null=True, blank=True)
    description   = models.TextField(blank=True)
    difficulte    = models.CharField(max_length=20, choices=DIFFICULTE_CHOICES, default='FACILE')
    est_dynamique = models.BooleanField(default=False)
    nb_frames     = models.IntegerField(default=0)
    est_valide    = models.BooleanField(default=False)
    ajoute_par    = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Signe LSF'
        verbose_name_plural = 'Signes LSF'
        ordering = ['mot']

    def __str__(self):
        return f'{self.mot} ({self.get_categorie_display()})'

    @property
    def has_animation(self):
        return bool(self.animation_glb)


class DatasetSample(models.Model):
    SOURCE_CHOICES = [
        ('WEBCAM',        'Webcam'),
        ('VIDEO_IMPORT',  'Import vidéo'),
        ('SYNTHESE',      'Synthèse'),
    ]
    QUALITE_CHOICES = [
        ('BONNE',   'Bonne'),
        ('MOYENNE', 'Moyenne'),
        ('MAUVAISE','Mauvaise'),
    ]

    signe          = models.ForeignKey(SignDictionary, on_delete=models.CASCADE, related_name='samples')
    landmarks_data = models.JSONField(default=list)
    source         = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='WEBCAM')
    qualite        = models.CharField(max_length=20, choices=QUALITE_CHOICES, default='BONNE')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Échantillon dataset'
        verbose_name_plural = 'Échantillons dataset'
        ordering = ['-created_at']

    def __str__(self):
        return f'Sample {self.signe.mot} [{self.source}]'


class TranslationSession(models.Model):
    MODE_CHOICES = [
        ('TEXT_TO_SIGN',  'Texte → Signe'),
        ('SIGN_TO_TEXT',  'Signe → Texte'),
        ('VIDEO_TO_TEXT', 'Vidéo → Texte'),
    ]

    utilisateur  = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    mode         = models.CharField(max_length=20, choices=MODE_CHOICES)
    texte_entree = models.TextField(null=True, blank=True)
    texte_sortie = models.TextField(null=True, blank=True)
    nb_signes    = models.IntegerField(default=0)
    duree_ms     = models.IntegerField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Session traduction'
        verbose_name_plural = 'Sessions traduction'
        ordering = ['-created_at']

    def __str__(self):
        user = self.utilisateur.email if self.utilisateur else 'Anonyme'
        return f'[{self.get_mode_display()}] {user} — {self.created_at:%d/%m/%Y %H:%M}'


class MLModelVersion(models.Model):
    ALGO_CHOICES = [
        ('RANDOM_FOREST', 'Random Forest'),
        ('LSTM',          'LSTM'),
        ('HYBRIDE',       'Hybride RF+LSTM'),
    ]

    version      = models.CharField(max_length=20)
    algorithme   = models.CharField(max_length=20, choices=ALGO_CHOICES)
    nb_classes   = models.IntegerField(default=0)
    nb_samples   = models.IntegerField(default=0)
    accuracy     = models.FloatField(default=0.0)
    est_actif    = models.BooleanField(default=False)
    parametres   = models.JSONField(default=dict)
    trained_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Version modèle ML'
        verbose_name_plural = 'Versions modèle ML'
        ordering = ['-trained_at']

    def __str__(self):
        return f'v{self.version} {self.get_algorithme_display()} — acc:{self.accuracy:.2%}'

    def save(self, *args, **kwargs):
        if self.est_actif:
            MLModelVersion.objects.filter(est_actif=True).exclude(pk=self.pk).update(est_actif=False)
        super().save(*args, **kwargs)
