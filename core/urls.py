from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Pages publiques
    path('',                          views.landing,             name='landing'),
    path('connexion/',                views.connexion,           name='connexion'),
    path('inscription/',              views.inscription,         name='inscription'),
    path('deconnexion/',              views.deconnexion,         name='deconnexion'),
    path('dictionnaire/',             views.dictionnaire,        name='dictionnaire'),
    path('dictionnaire/<str:mot>/',   views.dictionnaire_detail, name='dictionnaire_detail'),

    # Pages protégées
    path('app/',                      views.interface,           name='interface'),
    path('profil/',                   views.profil,              name='profil'),

    # Admin panel
    path('admin-panel/',              views.admin_dashboard,     name='admin_dashboard'),
    path('admin-panel/signes/',       views.admin_signs,         name='admin_signs'),
    path('admin-panel/dataset/',      views.admin_dataset,       name='admin_dataset'),
    path('admin-panel/training/',     views.admin_training,      name='admin_training'),

    # API
    path('api/translate/text-to-sign/',  views.api_translate_text_to_sign,  name='api_text_to_sign'),
    path('api/translate/video-to-text/', views.api_translate_video_to_text, name='api_video_to_text'),
    path('api/dictionary/',             views.api_dictionary_list,         name='api_dictionary'),
    path('api/ml/status/',              views.api_ml_status,               name='api_ml_status'),
    path('api/stats/',                  views.api_stats,                   name='api_stats'),
    path('api/admin/train/',            views.api_admin_train,             name='api_admin_train'),
    path('api/avatar-landmarks/',       views.api_avatar_landmarks,        name='api_avatar_landmarks'),
]
