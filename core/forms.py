from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class InscriptionForm(forms.Form):
    prenom    = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Jean',
            'autocomplete': 'given-name',
            'class': 'sb-input',
        }),
        label='Prénom',
    )
    nom       = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Dupont',
            'autocomplete': 'family-name',
            'class': 'sb-input',
        }),
        label='Nom',
    )
    email     = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'vous@exemple.com',
            'autocomplete': 'email',
            'class': 'sb-input',
        }),
        label='Adresse email',
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'class': 'sb-input',
        }),
        label='Mot de passe',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'class': 'sb-input',
        }),
        label='Confirmer le mot de passe',
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Cette adresse email est déjà utilisée.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Les mots de passe ne correspondent pas.')
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = CustomUser.objects.create_user(
            email=data['email'],
            password=data['password1'],
            prenom=data['prenom'],
            nom=data['nom'],
        )
        return user


class ConnexionForm(forms.Form):
    email    = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'vous@exemple.com',
            'autocomplete': 'email',
            'class': 'sb-input',
        }),
        label='Adresse email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'class': 'sb-input',
        }),
        label='Mot de passe',
    )
    remember = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'sb-checkbox'}),
        label='Se souvenir de moi',
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user    = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email    = cleaned.get('email', '').lower().strip()
        password = cleaned.get('password', '')
        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                raise ValidationError('Email ou mot de passe incorrect.')
            if not self.user.is_active:
                raise ValidationError('Ce compte est désactivé.')
        return cleaned

    def get_user(self):
        return self.user
