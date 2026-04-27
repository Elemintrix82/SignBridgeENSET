"""
Capture des pages SignBridge via requests + session Django.
"""
import requests, os, time

BASE = 'http://127.0.0.1:8001'
OUT  = os.path.dirname(__file__)
sess = requests.Session()

# Login
def login():
    r = sess.get(f'{BASE}/connexion/')
    csrf = sess.cookies.get('csrftoken', '')
    r2 = sess.post(f'{BASE}/connexion/', data={
        'email': 'demo@signbridge.fr',
        'password': 'Demo@2024',
        'csrfmiddlewaretoken': csrf,
    }, allow_redirects=True)
    print(f'Login: {r2.status_code} → {r2.url}')

def save_html(name, url):
    r = sess.get(f'{BASE}{url}')
    path = os.path.join(OUT, f'{name}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(r.text)
    print(f'  {name}: {r.status_code}')
    return r.status_code == 200

login()
pages = [
    ('page_landing',     '/'),
    ('page_connexion',   '/connexion/'),
    ('page_app_text',    '/app/?mode=text'),
    ('page_app_camera',  '/app/?mode=camera'),
    ('page_app_avatar',  '/app/?mode=avatar'),
    ('page_dictionary',  '/dictionnaire/'),
    ('page_admin',       '/admin-panel/'),
]
for name, url in pages:
    save_html(name, url)

print('HTML pages saved.')
