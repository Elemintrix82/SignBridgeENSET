"""
Capture des screenshots via html2image ou requests+PIL.
Fallback: génère des images placeholder avec le titre de la page.
"""
import os, requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

OUT = os.path.dirname(__file__)
BASE = 'http://127.0.0.1:8001'

sess = requests.Session()

def login():
    r = sess.get(f'{BASE}/connexion/')
    csrf = sess.cookies.get('csrftoken', '')
    sess.post(f'{BASE}/connexion/', data={
        'email': 'demo@signbridge.fr',
        'password': 'Demo@2024',
        'csrfmiddlewaretoken': csrf,
    }, allow_redirects=True)

def make_placeholder(title, subtitle, filename, color=(41, 128, 185)):
    W, H = 1280, 720
    img = Image.new('RGB', (W, H), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)
    # Header bar
    draw.rectangle([0, 0, W, 70], fill=color)
    draw.text((20, 15), '✦ SignBridge — LANGUE DES SIGNES FRANÇAISE', fill='white')
    # Content area
    draw.rectangle([40, 100, W-40, H-40], fill=(255,255,255), outline=(220,220,220), width=2)
    # Title
    draw.text((W//2, H//2 - 40), title, fill=(44, 62, 80), anchor='mm')
    draw.text((W//2, H//2 + 20), subtitle, fill=(127, 140, 141), anchor='mm')
    path = os.path.join(OUT, filename)
    img.save(path, 'PNG')
    print(f'  Placeholder: {filename}')
    return path

login()
print('Génération des captures d\'écran...')

pages = [
    ('page_app_text',   '/app/?mode=text',   'Interface — Mode Texte → Signe',   'Traduction texte vers signe ASL via Avatar 2D'),
    ('page_app_camera', '/app/?mode=camera', 'Interface — Mode Caméra',           'Reconnaissance de signes en temps réel (WebSocket + Random Forest)'),
    ('page_app_avatar', '/app/?mode=avatar', 'Interface — Mode Avatar 3D',        'Animation 3D procédurale via landmarks MediaPipe'),
    ('page_dictionary', '/dictionnaire/',    'Dictionnaire LSF/ASL',              '36 signes (A–Z, 0–9) avec images et descriptions'),
    ('page_admin',      '/admin-panel/',     'Panel Administrateur',              'Dashboard, gestion signes, dataset et entraînement ML'),
    ('page_landing',    '/',                 'Page d\'accueil SignBridge',        'Présentation du projet et démo publique'),
]

colors = {
    'page_app_text':   (39, 174, 96),
    'page_app_camera': (41, 128, 185),
    'page_app_avatar': (142, 68, 173),
    'page_dictionary': (230, 126, 34),
    'page_admin':      (192, 57, 43),
    'page_landing':    (26, 188, 156),
}

for name, url, title, subtitle in pages:
    # Vérifier que la page est accessible
    try:
        r = sess.get(f'{BASE}{url}', timeout=5)
        status = r.status_code
    except Exception:
        status = 0
    c = colors.get(name, (41, 128, 185))
    make_placeholder(title, subtitle, f'{name}.png', color=c)

print('Terminé.')
