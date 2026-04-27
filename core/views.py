import json
import logging
import unicodedata
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.db.models import Q, Count
from .models import CustomUser, SignDictionary, DatasetSample, TranslationSession, MLModelVersion
from .forms import InscriptionForm, ConnexionForm
from .decorators import admin_required

logger = logging.getLogger(__name__)


def normalize_text(text):
    nfkd = unicodedata.normalize('NFKD', text.lower().strip())
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def landing(request):
    if request.user.is_authenticated:
        return redirect('core:interface')
    featured_signs = SignDictionary.objects.filter(
        categorie='ALPHABET', est_valide=True
    )[:4]
    stats = {
        'total_signs': SignDictionary.objects.count(),
        'valid_signs': SignDictionary.objects.filter(est_valide=True).count(),
        'total_users': CustomUser.objects.filter(role='UTILISATEUR').count(),
    }
    return render(request, 'landing.html', {
        'featured_signs': featured_signs,
        'stats': stats,
    })


def connexion(request):
    if request.user.is_authenticated:
        return redirect('core:interface')

    form = ConnexionForm(request=request)
    if request.method == 'POST':
        form = ConnexionForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if form.cleaned_data.get('remember'):
                request.session.set_expiry(604800)
            else:
                request.session.set_expiry(28800)
            login(request, user)
            next_url = request.GET.get('next', '/app/')
            return redirect(next_url)

    return render(request, 'auth/connexion.html', {'form': form})


def inscription(request):
    if request.user.is_authenticated:
        return redirect('core:interface')

    form = InscriptionForm()
    if request.method == 'POST':
        form = InscriptionForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            request.session['welcome_toast'] = f'Bienvenue {user.prenom} !'
            return redirect('core:interface')

    return render(request, 'auth/inscription.html', {'form': form})


@require_POST
def deconnexion(request):
    logout(request)
    return redirect('core:landing')


@login_required
def interface(request):
    mode    = request.GET.get('mode', 'text')
    if mode not in ('text', 'camera', 'avatar'):
        mode = 'text'
    q       = request.GET.get('q', '').strip()          # pré-remplissage depuis le dictionnaire
    welcome = request.session.pop('welcome_toast', None)
    return render(request, 'app/interface.html', {
        'mode':          mode,
        'pre_query':     q,
        'welcome_toast': welcome,
    })


def dictionnaire(request):
    query     = request.GET.get('q', '').strip()
    categorie = request.GET.get('cat', '')
    page_num  = int(request.GET.get('page', 1))

    signs = SignDictionary.objects.filter(categorie__in=['ALPHABET', 'CHIFFRE'])
    if query:
        signs = signs.filter(Q(mot__icontains=query) | Q(description__icontains=query))
    if categorie:
        signs = signs.filter(categorie=categorie)

    per_page   = 24
    total      = signs.count()
    offset     = (page_num - 1) * per_page
    signs_page = signs[offset:offset + per_page]
    total_pages = (total + per_page - 1) // per_page

    categories = SignDictionary.CATEGORIE_CHOICES

    return render(request, 'dictionary/index.html', {
        'signs':       signs_page,
        'query':       query,
        'categorie':   categorie,
        'categories':  categories,
        'page':        page_num,
        'total_pages': total_pages,
        'total':       total,
    })


def dictionnaire_detail(request, mot):
    sign = get_object_or_404(SignDictionary, mot__iexact=mot)
    related = SignDictionary.objects.filter(
        categorie=sign.categorie
    ).exclude(pk=sign.pk)[:4]
    return render(request, 'dictionary/detail.html', {
        'sign':    sign,
        'related': related,
    })


@login_required
def profil(request):
    sessions = TranslationSession.objects.filter(
        utilisateur=request.user
    ).order_by('-created_at')[:20]
    stats = {
        'total_sessions':   sessions.count(),
        'text_to_sign':     TranslationSession.objects.filter(utilisateur=request.user, mode='TEXT_TO_SIGN').count(),
        'sign_to_text':     TranslationSession.objects.filter(utilisateur=request.user, mode='SIGN_TO_TEXT').count(),
        'total_signs_used': sum(s.nb_signes for s in sessions),
    }
    return render(request, 'profile/index.html', {
        'sessions': sessions,
        'stats':    stats,
    })


@login_required
@admin_required
def admin_dashboard(request):
    stats = {
        'total_users':    CustomUser.objects.count(),
        'total_signs':    SignDictionary.objects.count(),
        'valid_signs':    SignDictionary.objects.filter(est_valide=True).count(),
        'total_samples':  DatasetSample.objects.count(),
        'total_sessions': TranslationSession.objects.count(),
    }
    active_model = MLModelVersion.objects.filter(est_actif=True).first()
    recent_sessions = TranslationSession.objects.order_by('-created_at')[:10]
    return render(request, 'admin_panel/dashboard.html', {
        'stats':           stats,
        'active_model':    active_model,
        'recent_sessions': recent_sessions,
    })


@login_required
@admin_required
def admin_signs(request):
    signs = SignDictionary.objects.all().order_by('categorie', 'mot')
    return render(request, 'admin_panel/signs.html', {'signs': signs})


@login_required
@admin_required
def admin_dataset(request):
    samples_by_sign = DatasetSample.objects.values(
        'signe__mot'
    ).annotate(count=Count('id')).order_by('-count')
    total_samples = DatasetSample.objects.count()
    return render(request, 'admin_panel/dataset.html', {
        'samples_by_sign': samples_by_sign,
        'total_samples':   total_samples,
    })


@login_required
@admin_required
def admin_training(request):
    models = MLModelVersion.objects.all().order_by('-trained_at')
    active_model = models.filter(est_actif=True).first()
    return render(request, 'admin_panel/training.html', {
        'models':       models,
        'active_model': active_model,
    })


# ── API Endpoints ──────────────────────────────────────────────────────────────

@csrf_exempt
def api_translate_text_to_sign(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        body = json.loads(request.body)
        text = body.get('text', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    if not text:
        return JsonResponse({'error': 'Texte vide'}, status=400)

    if len(text) > 500:
        return JsonResponse({'error': 'Texte trop long (max 500 caractères)'}, status=400)

    words = re.findall(r"[a-zA-ZÀ-ÿ'0-9]+", text.lower())
    sequence = []
    words_found = 0
    words_not_found = 0
    total_duration = 0

    for word in words:
        normalized = normalize_text(word)
        sign = SignDictionary.objects.filter(mot__iexact=normalized).first()

        if sign:
            # Build static URL for animation GLB (files live in static_signs/, served via /static/)
            if sign.animation_glb:
                # animation_glb.name stores path like "static_signs/animations/bonjour.glb"
                # or "animations/bonjour.glb" — extract relative part after static_signs/ if present
                anim_name = sign.animation_glb.name.replace('\\', '/')
                if 'static_signs/' in anim_name:
                    anim_rel = anim_name.split('static_signs/', 1)[1]
                else:
                    anim_rel = anim_name
                from django.templatetags.static import static as static_url
                anim_url = request.build_absolute_uri(static_url(anim_rel))
            else:
                anim_url = None
            duration = sign.nb_frames * 100 if sign.nb_frames else 1200
            sequence.append({
                'word':          word,
                'sign_id':       sign.pk,
                'animation_url': anim_url,
                'duration_ms':   duration,
                'found':         True,
                'categorie':     sign.categorie,
            })
            words_found  += 1
            total_duration += duration
        else:
            letters = [c.upper() for c in word if c.isalpha() or c.isdigit()]
            letter_duration = len(letters) * 600
            sequence.append({
                'word':          word,
                'fallback':      'alphabet',
                'letters':       letters,
                'duration_ms':   letter_duration,
                'found':         False,
            })
            words_not_found  += 1
            total_duration   += letter_duration

    if request.user.is_authenticated:
        TranslationSession.objects.create(
            utilisateur=request.user,
            mode='TEXT_TO_SIGN',
            texte_entree=text,
            nb_signes=len(sequence),
            duree_ms=total_duration,
        )

    return JsonResponse({
        'sequence':         sequence,
        'total_duration_ms': total_duration,
        'words_found':      words_found,
        'words_not_found':  words_not_found,
    })


def api_dictionary_list(request):
    if request.method == 'GET':
        cat   = request.GET.get('categorie', '')
        query = request.GET.get('q', '')
        signs = SignDictionary.objects.all()
        if cat:
            signs = signs.filter(categorie=cat)
        if query:
            signs = signs.filter(mot__icontains=query)

        data = [{
            'id':         s.pk,
            'mot':        s.mot,
            'categorie':  s.categorie,
            'difficulte': s.difficulte,
            'est_valide': s.est_valide,
            'has_anim':   s.has_animation,
            'description': s.description,
        } for s in signs[:100]]
        return JsonResponse({'signs': data, 'total': signs.count()})

    if request.method == 'POST':
        if not request.user.is_authenticated or not request.user.is_admin:
            return JsonResponse({'error': 'Non autorisé'}, status=403)
        try:
            body = json.loads(request.body)
            sign = SignDictionary.objects.create(
                mot=body['mot'],
                categorie=body.get('categorie', 'ALPHABET'),
                description=body.get('description', ''),
                difficulte=body.get('difficulte', 'FACILE'),
                ajoute_par=request.user,
            )
            return JsonResponse({'id': sign.pk, 'mot': sign.mot}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def api_ml_status(request):
    active = MLModelVersion.objects.filter(est_actif=True).first()
    return JsonResponse({
        'model_active':   active is not None,
        'version':        active.version if active else None,
        'algorithme':     active.algorithme if active else None,
        'accuracy':       active.accuracy if active else None,
        'nb_classes':     active.nb_classes if active else None,
        'total_samples':  DatasetSample.objects.count(),
        'total_signs':    SignDictionary.objects.count(),
    })


def api_stats(request):
    return JsonResponse({
        'total_signs':    SignDictionary.objects.count(),
        'valid_signs':    SignDictionary.objects.filter(est_valide=True).count(),
        'total_users':    CustomUser.objects.filter(is_active=True).count(),
        'total_sessions': TranslationSession.objects.count(),
        'total_samples':  DatasetSample.objects.count(),
    })


def api_admin_train(request):
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requis'}, status=405)

    import threading
    def run_training():
        try:
            from ml_engine.model_trainer import ModelTrainer
            trainer = ModelTrainer()
            trainer.train_all()
        except Exception as e:
            logger.error(f'Erreur entraînement: {e}')

    t = threading.Thread(target=run_training, daemon=True)
    t.start()
    return JsonResponse({'status': 'training_started', 'message': 'Entraînement lancé en arrière-plan'})


@require_GET
@login_required
def api_avatar_landmarks(request):
    """
    Retourne les poses 3D moyennes (21 landmarks) pour chaque signe A-Z + 0-9.
    Utilisé par Hand3DRenderer (Three.js) pour animer la main 3D.

    GET /api/avatar-landmarks/
    Réponse : { "A": [{x,y,z}×21], "B": [...], ... }
    """
    import numpy as np

    # Récupérer tous les signes alphabet + chiffres valides
    signs = SignDictionary.objects.filter(
        mot__regex=r'^[A-Za-z0-9]$',
        est_valide=True,
    ).prefetch_related('samples')

    result = {}
    for sign in signs:
        label = sign.mot.upper()
        samples = list(
            DatasetSample.objects
            .filter(signe=sign, qualite='BONNE')
            .values_list('landmarks_data', flat=True)[:40]
        )
        # Filtrer les samples valides (63 floats)
        valid = [s for s in samples if s and len(s) >= 63]
        if not valid:
            continue

        # Calcul de la pose moyenne
        arr  = np.array([s[:63] for s in valid], dtype=np.float32)
        mean = arr.mean(axis=0).reshape(21, 3)

        # Centrage sur le poignet (point 0) — même convention que le client webcam
        wrist = mean[0].copy()
        mean  = mean - wrist        # tous les points relatifs au poignet

        result[label] = [
            {'x': round(float(p[0]), 5),
             'y': round(float(p[1]), 5),
             'z': round(float(p[2]), 5)}
            for p in mean
        ]

    return JsonResponse(result)


@csrf_exempt
@login_required
def api_translate_video_to_text(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    video_file = request.FILES.get('video')
    if not video_file:
        return JsonResponse({'error': 'Aucun fichier vidéo fourni'}, status=400)

    allowed_types = {'video/mp4', 'video/avi', 'video/quicktime', 'video/webm', 'video/x-msvideo'}
    if video_file.content_type not in allowed_types and not video_file.name.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
        return JsonResponse({'error': 'Format non supporté. Utilisez MP4, AVI, MOV ou WebM.'}, status=400)

    max_size = 100 * 1024 * 1024  # 100 Mo
    if video_file.size > max_size:
        return JsonResponse({'error': 'Fichier trop volumineux (max 100 Mo)'}, status=400)

    import tempfile, os
    suffix = os.path.splitext(video_file.name)[1] or '.mp4'
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in video_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        from ml_engine.video_processor import VideoProcessor
        processor = VideoProcessor()
        result = processor.process_video(tmp_path)

        if 'error' in result and not result.get('text'):
            return JsonResponse({'error': result['error']}, status=422)

        if request.user.is_authenticated:
            TranslationSession.objects.create(
                utilisateur=request.user,
                mode='SIGN_TO_TEXT',
                texte_entree=video_file.name,
                nb_signes=result.get('nb_words', 0),
                duree_ms=0,
            )

        return JsonResponse({
            'text':      result.get('text', ''),
            'segments':  result.get('segments', []),
            'nb_frames': result.get('nb_frames', 0),
            'nb_words':  result.get('nb_words', 0),
        })
    except Exception as e:
        logger.error(f'Erreur traitement vidéo upload: {e}')
        return JsonResponse({'error': 'Erreur interne du serveur'}, status=500)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
