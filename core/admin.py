from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, SignDictionary, DatasetSample, TranslationSession, MLModelVersion


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display  = ('email', 'prenom', 'nom', 'role', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'prenom', 'nom')
    ordering      = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('prenom', 'nom', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'prenom', 'nom', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(SignDictionary)
class SignDictionaryAdmin(admin.ModelAdmin):
    list_display  = ('mot', 'categorie', 'difficulte', 'est_valide', 'has_animation_display', 'updated_at')
    list_filter   = ('categorie', 'difficulte', 'est_valide', 'est_dynamique')
    search_fields = ('mot', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def has_animation_display(self, obj):
        if obj.animation_glb:
            return format_html('<span style="color:green">✓ Oui</span>')
        return format_html('<span style="color:red">✗ Non</span>')
    has_animation_display.short_description = 'Animation GLB'


@admin.register(DatasetSample)
class DatasetSampleAdmin(admin.ModelAdmin):
    list_display = ('signe', 'source', 'qualite', 'created_at')
    list_filter  = ('source', 'qualite')
    readonly_fields = ('created_at',)


@admin.register(TranslationSession)
class TranslationSessionAdmin(admin.ModelAdmin):
    list_display  = ('utilisateur', 'mode', 'nb_signes', 'duree_ms', 'created_at')
    list_filter   = ('mode',)
    readonly_fields = ('created_at',)


@admin.register(MLModelVersion)
class MLModelVersionAdmin(admin.ModelAdmin):
    list_display  = ('version', 'algorithme', 'accuracy', 'nb_classes', 'nb_samples', 'est_actif', 'trained_at')
    list_filter   = ('algorithme', 'est_actif')
    readonly_fields = ('trained_at',)


admin.site.site_header = 'SignBridge Administration'
admin.site.site_title  = 'SignBridge'
admin.site.index_title = 'Tableau de bord administrateur'
