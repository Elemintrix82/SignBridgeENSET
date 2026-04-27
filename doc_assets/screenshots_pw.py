"""Capture des pages SignBridge avec Playwright."""
from playwright.sync_api import sync_playwright
import os, time

OUT  = os.path.dirname(__file__)
BASE = 'http://127.0.0.1:8001'

pages = [
    ('page_landing',    '/',                  1280, 820),
    ('page_connexion',  '/connexion/',         1280, 820),
    ('page_app_text',   '/app/?mode=text',     1280, 900),
    ('page_app_camera', '/app/?mode=camera',   1280, 900),
    ('page_app_avatar', '/app/?mode=avatar',   1280, 900),
    ('page_dictionary', '/dictionnaire/',      1280, 820),
    ('page_admin',      '/admin-panel/',       1280, 820),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx     = browser.new_context(viewport={'width': 1280, 'height': 820})
    page    = ctx.new_page()

    # Login
    page.goto(f'{BASE}/connexion/')
    page.fill('input[name="email"]', 'demo@signbridge.fr')
    page.fill('input[name="password"]', 'Demo@2024')
    page.click('button[type="submit"]')
    page.wait_for_load_state('load')
    time.sleep(1)
    print(f'Logged in: {page.url}')

    for name, url, w, h in pages:
        page.set_viewport_size({'width': w, 'height': h})
        page.goto(f'{BASE}{url}')
        page.wait_for_load_state('load')
        time.sleep(0.8)
        out = os.path.join(OUT, f'{name}.png')
        page.screenshot(path=out, full_page=False)
        print(f'  {name}.png — OK')

    browser.close()
print('Captures terminées.')
