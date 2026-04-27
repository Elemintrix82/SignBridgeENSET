"""
generate_asl_training.py
Génère des landmarks MediaPipe réalistes pour les 36 signes ASL (A-Z + 0-9),
les insère en base, puis ré-entraîne le Random Forest.

Usage :
    python manage.py generate_asl_training            # 300 samples/signe
    python manage.py generate_asl_training --samples 500
    python manage.py generate_asl_training --retrain-only
    python manage.py generate_asl_training --clear    # supprime anciens + régénère
"""
import numpy as np
from django.core.management.base import BaseCommand

# ── Positions canoniques MediaPipe (normalisées / poignet = [0,0,0]) ─────────
# x: droite+   y: bas+ (image)   z: profondeur- (vers caméra)
# Les doigts tendent vers y négatif (haut de l'image)

W = np.zeros(3, dtype=np.float32)

T_CMC   = np.array([-0.050, -0.060,  0.010], dtype=np.float32)
T_MCP   = np.array([-0.100, -0.110,  0.010], dtype=np.float32)
T_IP_E  = np.array([-0.140, -0.100,  0.000], dtype=np.float32)
T_TIP_E = np.array([-0.175, -0.075, -0.005], dtype=np.float32)
T_IP_F  = np.array([-0.080, -0.145,  0.010], dtype=np.float32)
T_TIP_F = np.array([-0.060, -0.170,  0.015], dtype=np.float32)

I_MCP   = np.array([-0.050, -0.190, -0.020], dtype=np.float32)
I_PIP_E = np.array([-0.053, -0.325, -0.040], dtype=np.float32)
I_DIP_E = np.array([-0.057, -0.430, -0.060], dtype=np.float32)
I_TIP_E = np.array([-0.060, -0.510, -0.075], dtype=np.float32)
I_PIP_F = np.array([-0.025, -0.215,  0.010], dtype=np.float32)
I_DIP_F = np.array([ 0.010, -0.195,  0.020], dtype=np.float32)
I_TIP_F = np.array([ 0.025, -0.170,  0.025], dtype=np.float32)

M_MCP   = np.array([ 0.000, -0.210, -0.020], dtype=np.float32)
M_PIP_E = np.array([ 0.000, -0.355, -0.045], dtype=np.float32)
M_DIP_E = np.array([ 0.000, -0.470, -0.065], dtype=np.float32)
M_TIP_E = np.array([ 0.000, -0.560, -0.080], dtype=np.float32)
M_PIP_F = np.array([ 0.020, -0.225,  0.010], dtype=np.float32)
M_DIP_F = np.array([ 0.045, -0.205,  0.020], dtype=np.float32)
M_TIP_F = np.array([ 0.055, -0.175,  0.025], dtype=np.float32)

R_MCP   = np.array([ 0.050, -0.190, -0.020], dtype=np.float32)
R_PIP_E = np.array([ 0.053, -0.325, -0.040], dtype=np.float32)
R_DIP_E = np.array([ 0.057, -0.430, -0.060], dtype=np.float32)
R_TIP_E = np.array([ 0.060, -0.510, -0.075], dtype=np.float32)
R_PIP_F = np.array([ 0.065, -0.205,  0.010], dtype=np.float32)
R_DIP_F = np.array([ 0.085, -0.190,  0.020], dtype=np.float32)
R_TIP_F = np.array([ 0.095, -0.160,  0.025], dtype=np.float32)

P_MCP   = np.array([ 0.090, -0.160, -0.018], dtype=np.float32)
P_PIP_E = np.array([ 0.095, -0.270, -0.030], dtype=np.float32)
P_DIP_E = np.array([ 0.100, -0.360, -0.050], dtype=np.float32)
P_TIP_E = np.array([ 0.102, -0.430, -0.060], dtype=np.float32)
P_PIP_F = np.array([ 0.103, -0.175,  0.010], dtype=np.float32)
P_DIP_F = np.array([ 0.112, -0.160,  0.018], dtype=np.float32)
P_TIP_F = np.array([ 0.120, -0.140,  0.022], dtype=np.float32)


def _build(t_ext, i_ext, m_ext, r_ext, p_ext,
           spread=False, t_mode='fold'):
    """Construit un vecteur de 63 landmarks pour une configuration de main ASL."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC
    lm[2] = T_MCP

    # ── Pouce ──────────────────────────────────────────────────────────────────
    if t_ext:
        lm[3] = T_IP_E;   lm[4] = T_TIP_E
    elif t_mode == 'palm':
        lm[3] = np.array([-0.020, -0.160, 0.005], dtype=np.float32)
        lm[4] = np.array([ 0.010, -0.165, 0.005], dtype=np.float32)
    elif t_mode == 'between':
        lm[3] = np.array([-0.045, -0.210, 0.005], dtype=np.float32)
        lm[4] = np.array([-0.020, -0.225, 0.000], dtype=np.float32)
    elif t_mode == 'over':
        lm[3] = np.array([-0.010, -0.175, 0.010], dtype=np.float32)
        lm[4] = np.array([ 0.020, -0.165, 0.015], dtype=np.float32)
    elif t_mode == 'touch':
        lm[3] = np.array([-0.045, -0.250, 0.000], dtype=np.float32)
        lm[4] = np.array([-0.045, -0.310,-0.010], dtype=np.float32)
    elif t_mode == 'out':
        lm[3] = T_IP_E;   lm[4] = T_TIP_E   # même que étendu mais signalé
    else:
        lm[3] = T_IP_F;   lm[4] = T_TIP_F

    # ── Index ──────────────────────────────────────────────────────────────────
    si = np.array([-0.010, 0, 0], dtype=np.float32) if spread else np.zeros(3)
    lm[5] = I_MCP + si
    if i_ext:
        lm[6] = I_PIP_E + si; lm[7] = I_DIP_E + si; lm[8] = I_TIP_E + si
    else:
        lm[6] = I_PIP_F;      lm[7] = I_DIP_F;      lm[8] = I_TIP_F

    # ── Majeur ─────────────────────────────────────────────────────────────────
    sm = np.array([-0.003, 0, 0], dtype=np.float32) if spread else np.zeros(3)
    lm[9] = M_MCP + sm
    if m_ext:
        lm[10] = M_PIP_E + sm; lm[11] = M_DIP_E + sm; lm[12] = M_TIP_E + sm
    else:
        lm[10] = M_PIP_F;      lm[11] = M_DIP_F;      lm[12] = M_TIP_F

    # ── Annulaire ──────────────────────────────────────────────────────────────
    sr = np.array([0.003, 0, 0], dtype=np.float32) if spread else np.zeros(3)
    lm[13] = R_MCP + sr
    if r_ext:
        lm[14] = R_PIP_E + sr; lm[15] = R_DIP_E + sr; lm[16] = R_TIP_E + sr
    else:
        lm[14] = R_PIP_F;      lm[15] = R_DIP_F;      lm[16] = R_TIP_F

    # ── Auriculaire ────────────────────────────────────────────────────────────
    sp = np.array([0.010, 0, 0], dtype=np.float32) if spread else np.zeros(3)
    lm[17] = P_MCP + sp
    if p_ext:
        lm[18] = P_PIP_E + sp; lm[19] = P_DIP_E + sp; lm[20] = P_TIP_E + sp
    else:
        lm[18] = P_PIP_F;      lm[19] = P_DIP_F;      lm[20] = P_TIP_F

    return lm.flatten()


def _c_shape():
    """C : tous les doigts semi-fléchis, forme arrondie."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC; lm[2] = T_MCP
    lm[3] = np.array([-0.16, -0.09,  0.00], dtype=np.float32)
    lm[4] = np.array([-0.19, -0.06, -0.01], dtype=np.float32)
    for idx, (mcp, pip_e, dip_e, tip_e, pip_f, dip_f, tip_f) in enumerate([
        (I_MCP, I_PIP_E, I_DIP_E, I_TIP_E, I_PIP_F, I_DIP_F, I_TIP_F),
        (M_MCP, M_PIP_E, M_DIP_E, M_TIP_E, M_PIP_F, M_DIP_F, M_TIP_F),
        (R_MCP, R_PIP_E, R_DIP_E, R_TIP_E, R_PIP_F, R_DIP_F, R_TIP_F),
        (P_MCP, P_PIP_E, P_DIP_E, P_TIP_E, P_PIP_F, P_DIP_F, P_TIP_F),
    ]):
        base = 5 + idx * 4
        lm[base]   = mcp
        lm[base+1] = (pip_e + pip_f) / 2
        lm[base+2] = (dip_e + dip_f) / 2
        lm[base+3] = (tip_e + tip_f) / 2
    return lm.flatten()


def _e_shape():
    """E : doigts fléchis à mi-course, bouts vers la paume, pouce en dessous."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC; lm[2] = T_MCP
    # Pouce tiré sous les doigts fléchis
    lm[3] = np.array([-0.020, -0.165,  0.008], dtype=np.float32)
    lm[4] = np.array([ 0.012, -0.170,  0.010], dtype=np.float32)
    # Doigts : entre plié et étendu (75 % fléchi)
    for idx, (mcp, pip_e, pip_f, dip_e, dip_f, tip_e, tip_f) in enumerate([
        (I_MCP, I_PIP_E, I_PIP_F, I_DIP_E, I_DIP_F, I_TIP_E, I_TIP_F),
        (M_MCP, M_PIP_E, M_PIP_F, M_DIP_E, M_DIP_F, M_TIP_E, M_TIP_F),
        (R_MCP, R_PIP_E, R_PIP_F, R_DIP_E, R_DIP_F, R_TIP_E, R_TIP_F),
        (P_MCP, P_PIP_E, P_PIP_F, P_DIP_E, P_DIP_F, P_TIP_E, P_TIP_F),
    ]):
        base = 5 + idx * 4
        lm[base]   = mcp
        lm[base+1] = pip_e * 0.25 + pip_f * 0.75
        lm[base+2] = dip_e * 0.15 + dip_f * 0.85
        lm[base+3] = tip_e * 0.10 + tip_f * 0.90
    return lm.flatten()


def _s_shape():
    """S : poing fermé, pouce croisé PAR-DESSUS les doigts (avant)."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC; lm[2] = T_MCP
    # Pouce très en avant, couvrant les doigts
    lm[3] = np.array([-0.005, -0.178,  0.020], dtype=np.float32)
    lm[4] = np.array([ 0.025, -0.165,  0.025], dtype=np.float32)
    # Doigts fermés (repliés)
    for idx, (mcp, pip_f, dip_f, tip_f) in enumerate([
        (I_MCP, I_PIP_F, I_DIP_F, I_TIP_F),
        (M_MCP, M_PIP_F, M_DIP_F, M_TIP_F),
        (R_MCP, R_PIP_F, R_DIP_F, R_TIP_F),
        (P_MCP, P_PIP_F, P_DIP_F, P_TIP_F),
    ]):
        base = 5 + idx * 4
        lm[base] = mcp; lm[base+1] = pip_f; lm[base+2] = dip_f; lm[base+3] = tip_f
    return lm.flatten()


def _x_shape():
    """X : index crochet (semi-fléchi), autres doigts fermés."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC; lm[2] = T_MCP
    lm[3] = T_IP_F; lm[4] = T_TIP_F
    # Index : entre étendu et fléchi (crochet) — PIP basse, DIP repliée
    lm[5] = I_MCP
    lm[6] = I_PIP_E * 0.55 + I_PIP_F * 0.45   # PIP haute
    lm[7] = I_DIP_E * 0.15 + I_DIP_F * 0.85   # DIP très fléchie
    lm[8] = I_TIP_E * 0.10 + I_TIP_F * 0.90   # bout vers paume
    # Majeur, annulaire, auriculaire : fermés
    for idx, (mcp, pip_f, dip_f, tip_f) in enumerate([
        (M_MCP, M_PIP_F, M_DIP_F, M_TIP_F),
        (R_MCP, R_PIP_F, R_DIP_F, R_TIP_F),
        (P_MCP, P_PIP_F, P_DIP_F, P_TIP_F),
    ]):
        base = 9 + idx * 4
        lm[base] = mcp; lm[base+1] = pip_f; lm[base+2] = dip_f; lm[base+3] = tip_f
    return lm.flatten()


def _t_shape():
    """T : pouce entre index et majeur (sous index), index replié dessus."""
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0] = W
    lm[1] = T_CMC; lm[2] = T_MCP
    # Pouce sort entre index et majeur — position plus basse/centrale
    lm[3] = np.array([-0.052, -0.225,  0.003], dtype=np.float32)
    lm[4] = np.array([-0.028, -0.240, -0.002], dtype=np.float32)
    # Index légèrement moins replié (juste au-dessus du pouce)
    lm[5] = I_MCP
    lm[6] = I_PIP_F * 1.05; lm[7] = I_DIP_F; lm[8] = I_TIP_F
    # Autres doigts fermés
    for idx, (mcp, pip_f, dip_f, tip_f) in enumerate([
        (M_MCP, M_PIP_F, M_DIP_F, M_TIP_F),
        (R_MCP, R_PIP_F, R_DIP_F, R_TIP_F),
        (P_MCP, P_PIP_F, P_DIP_F, P_TIP_F),
    ]):
        base = 9 + idx * 4
        lm[base] = mcp; lm[base+1] = pip_f; lm[base+2] = dip_f; lm[base+3] = tip_f
    return lm.flatten()


def _scale_normalize(lm63: np.ndarray) -> np.ndarray:
    """
    Normalisation d'échelle : divise par la distance poignet→MCP majeur (point 9).
    Rend les features invariants à la distance caméra / taille de main.
    """
    lm = lm63.reshape(21, 3).copy()
    scale = float(np.linalg.norm(lm[9]))   # wrist déjà à l'origine
    if scale > 1e-6:
        lm /= scale
    return lm.flatten()


# ── Table des poses ASL canoniques (CORRIGÉE — plus de doublons) ─────────────
# Légende : (t_ext, i_ext, m_ext, r_ext, p_ext, spread, t_mode)
ASL_POSES = {
    # ── Lettres A-Z ──────────────────────────────────────────────────────────
    'A': _build(False, False, False, False, False, False, 'fold'),    # poing, pouce côté
    'B': _build(False, True,  True,  True,  True,  False, 'palm'),   # 4 doigts droits, pouce replié
    'C': _c_shape(),                                                   # demi-cercle
    'D': _build(False, True,  False, False, False, False, 'touch'),   # index droit, pouce touche majeur
    'E': _e_shape(),                                                   # doigts 75 % fléchis, pouce dessous ← CORRIGÉ
    'F': _build(False, False, True,  True,  True,  False, 'touch'),   # pouce+index touche, autres droits
    'G': _build(False, True,  False, False, False, False, 'fold'),    # index pointé côté
    'H': _build(False, True,  True,  False, False, False, 'fold'),    # index+majeur côté
    'I': _build(False, False, False, False, True,  False, 'fold'),    # auriculaire droit
    'J': _build(False, False, False, False, True,  False, 'fold'),    # auriculaire (+ mouvement en J, statique ≈ I)
    'K': _build(True,  True,  True,  False, False, False, 'between'), # index+majeur V, pouce entre
    'L': _build(True,  True,  False, False, False, False, 'out'),     # L (pouce+index)
    'M': _build(False, False, False, False, False, False, 'over'),    # 3 doigts sur pouce
    'N': _build(False, False, False, False, False, False, 'between'), # 2 doigts sur pouce ← déjà distinct de M
    'O': _build(False, False, False, False, False, False, 'touch'),   # cercle O
    'P': _build(True,  True,  True,  False, False, False, 'between'), # comme K orienté bas
    'Q': _build(False, True,  False, False, False, False, 'fold'),    # comme G orienté bas
    'R': _build(False, True,  True,  False, False, False, 'fold'),    # index+majeur croisés
    'S': _s_shape(),                                                   # poing, pouce DEVANT les doigts ← CORRIGÉ (≠ M)
    'T': _t_shape(),                                                   # pouce entre index/majeur ← CORRIGÉ (≠ N)
    'U': _build(False, True,  True,  False, False, False, 'fold'),    # index+majeur droits ensemble
    'V': _build(False, True,  True,  False, False, True,  'fold'),    # V — index+majeur écartés
    'W': _build(False, True,  True,  True,  False, True,  'fold'),    # W — 3 doigts écartés
    'X': _x_shape(),                                                   # index crochet ← CORRIGÉ (≠ A/E)
    'Y': _build(True,  False, False, False, True,  False, 'fold'),    # pouce+auriculaire étendus
    'Z': _build(False, True,  False, False, False, False, 'fold'),    # index trace Z (statique ≈ index droit)

    # ── Chiffres 0-9 ─────────────────────────────────────────────────────────
    '0': _build(False, False, False, False, False, False, 'touch'),   # cercle (≈ O)
    '1': _build(False, True,  False, False, False, False, 'fold'),    # index seul
    '2': _build(False, True,  True,  False, False, True,  'fold'),    # index+majeur (≈ V)
    '3': _build(True,  True,  True,  False, False, False, 'fold'),    # pouce+index+majeur
    '4': _build(False, True,  True,  True,  True,  False, 'palm'),    # 4 doigts, pouce replié
    '5': _build(True,  True,  True,  True,  True,  True,  'out'),     # tous les doigts
    '6': _build(False, True,  True,  True,  False, False, 'touch'),   # pouce touche auriculaire
    '7': _build(False, True,  True,  False, True,  False, 'fold'),    # pouce touche annulaire
    '8': _build(False, True,  False, True,  True,  False, 'fold'),    # pouce touche majeur
    '9': _build(False, False, False, False, False, False, 'touch'),   # crochet index→pouce (≈ 0)
}


def augment(base: np.ndarray, n: int, sigma: float = 0.026) -> list:
    """
    Génère n variantes d'un vecteur landmarks avec :
    - bruit gaussien (σ = 2.6 %, bien plus réaliste pour une vraie main)
    - rotation 2D ±15° (variation d'orientation caméra)
    - mise à l'échelle ±12 % (distance caméra)
    - translation légère ±4 %
    Puis normalisation d'échelle (poignet→MCP-majeur = 1.0)
    → les features sont invariants à la taille de main et à la distance.
    """
    samples = []
    lm = base.reshape(21, 3).copy()
    for _ in range(n):
        v = lm.copy()
        # Bruit
        v += np.random.randn(21, 3).astype(np.float32) * sigma
        # Mise à l'échelle
        sc = 1.0 + np.random.uniform(-0.12, 0.12)
        v *= sc
        # Rotation 2D (plan image)
        angle = np.random.uniform(-0.26, 0.26)   # ±15°
        c, s = float(np.cos(angle)), float(np.sin(angle))
        xr = v[:, 0] * c - v[:, 1] * s
        yr = v[:, 0] * s + v[:, 1] * c
        v[:, 0] = xr; v[:, 1] = yr
        # Translation (le poignet reste à l'origine après normalisation)
        v[:, 0] += np.random.uniform(-0.04, 0.04)
        v[:, 1] += np.random.uniform(-0.04, 0.04)
        # ── Normalisation d'échelle ──────────────────────────────────────
        # Divise par la distance poignet (pt 0) → MCP-majeur (pt 9)
        # Cela rend les features indépendants de la taille de main
        norm_vec = _scale_normalize(v.flatten())
        samples.append(norm_vec.tolist())
    return samples


class Command(BaseCommand):
    help = 'Génère des landmarks ASL réalistes et entraîne le Random Forest'

    def add_arguments(self, parser):
        parser.add_argument('--samples',      type=int, default=300)
        parser.add_argument('--retrain-only', action='store_true')
        parser.add_argument('--clear',        action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== SignBridge — Génération landmarks ASL ===\n'
        ))
        if not options['retrain_only']:
            self._generate(options['samples'], options['clear'])
        self._train_rf()

    def _generate(self, n_samples, clear_old):
        from core.models import SignDictionary, DatasetSample
        if clear_old:
            deleted = DatasetSample.objects.filter(source='GENERATED').delete()[0]
            self.stdout.write(f'  [CLEAN] {deleted} anciens samples supprimés')

        total = 0
        for label, base_lm in ASL_POSES.items():
            sign = SignDictionary.objects.filter(mot=label).first()
            if not sign:
                self.stdout.write(self.style.WARNING(f'  [!] {label} absent de la base'))
                continue
            objs = [
                __import__('core.models', fromlist=['DatasetSample']).DatasetSample(
                    signe=sign,
                    landmarks_data=lm,
                    source='GENERATED',
                    qualite='BONNE',
                )
                for lm in augment(base_lm, n_samples)
            ]
            DatasetSample.objects.bulk_create(objs, batch_size=500)
            total += len(objs)
            self.stdout.write(f'  [+] {label} : {len(objs)} samples')

        self.stdout.write(self.style.SUCCESS(
            f'\n  Total généré : {total} samples pour {len(ASL_POSES)} signes\n'
        ))

    def _train_rf(self):
        self.stdout.write('  Entraînement Random Forest...')
        try:
            import json, joblib
            from pathlib import Path
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder
            from sklearn.model_selection import train_test_split
            from django.conf import settings
            from core.models import DatasetSample

            rows = DatasetSample.objects.filter(
                qualite__in=['BONNE', 'MOYENNE']
            ).select_related('signe')

            X, y = [], []
            for s in rows:
                lm = s.landmarks_data
                if isinstance(lm, list) and len(lm) >= 63:
                    X.append(lm[:63])
                    y.append(s.signe.mot.upper())

            if not X:
                self.stdout.write(self.style.ERROR('  Aucun sample — abandon'))
                return

            X = np.array(X, dtype='float32')
            y = np.array(y)
            le = LabelEncoder()
            y_enc = le.fit_transform(y)
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
            )
            clf = RandomForestClassifier(
                n_estimators=300, max_depth=None,
                min_samples_split=2, random_state=42, n_jobs=-1,
            )
            clf.fit(X_tr, y_tr)
            acc = clf.score(X_te, y_te)

            model_dir = Path(getattr(settings, 'ML_MODEL_DIR', 'signbridge_model'))
            model_dir.mkdir(exist_ok=True)
            joblib.dump(clf, model_dir / 'rf_model.pkl')
            joblib.dump(le,  model_dir / 'label_encoder.pkl')

            info = {
                'trained_at': __import__('datetime').datetime.now().isoformat(),
                'status':     'asl_generated',
                'note':       f'RF entraîné sur {len(X)} landmarks ASL générés',
                'classes':    list(le.classes_),
                'n_classes':  len(le.classes_),
                'n_samples':  len(X),
                'rf_accuracy': float(acc),
            }
            with open(model_dir / 'model_info.json', 'w') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)

            # ── Mise à jour de la BDD ──────────────────────────────────────────
            try:
                from core.models import MLModelVersion
                MLModelVersion.objects.filter(est_actif=True).update(est_actif=False)
                MLModelVersion.objects.update_or_create(
                    version='1.0.0-asl',
                    defaults=dict(
                        algorithme='RANDOM_FOREST',
                        nb_classes=len(le.classes_),
                        nb_samples=len(X),
                        accuracy=float(acc),
                        est_actif=True,
                        parametres={'n_estimators': 300, 'note': 'Generated ASL synthetic landmarks'},
                    )
                )
            except Exception as db_err:
                self.stdout.write(self.style.WARNING(f'  [!] BDD non mise à jour : {db_err}'))

            # ── Réinitialiser le singleton GestureClassifier ───────────────────
            try:
                from ml_engine.gesture_classifier import GestureClassifier
                GestureClassifier._instance = None
            except Exception:
                pass

            self.stdout.write(self.style.SUCCESS(
                f'\n  [OK] RF accuracy : {acc:.1%}  |  {len(le.classes_)} classes  |  {len(X)} samples'
                f'\n  Modele sauve -> {model_dir}/rf_model.pkl'
                f'\n  Redemarrer le serveur pour recharger le modele.\n'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erreur : {e}'))
            import traceback; traceback.print_exc()
