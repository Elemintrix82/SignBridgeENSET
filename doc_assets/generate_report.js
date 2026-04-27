const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
  LevelFormat, TableOfContents, ExternalHyperlink
} = require('docx');
const fs = require('fs');
const path = require('path');

const ASSETS = __dirname;
const OUT    = path.join(ASSETS, '..'); // racine projet

// ── Utilitaires ───────────────────────────────────────────────────────────────
const img = (file, w, h) => {
  const p = path.join(ASSETS, file);
  if (!fs.existsSync(p)) return null;
  const ext = path.extname(file).slice(1).toLowerCase();
  return new ImageRun({
    type: ext === 'jpg' ? 'jpeg' : ext,
    data: fs.readFileSync(p),
    transformation: { width: w, height: h },
    altText: { title: file, description: file, name: file }
  });
};

const cell = (text, opts = {}) => new TableCell({
  borders: {
    top:    { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
    bottom: { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
    left:   { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
    right:  { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' },
  },
  width:   { size: opts.w || 2000, type: WidthType.DXA },
  shading: opts.header
    ? { fill: '1A5276', type: ShadingType.CLEAR }
    : opts.shade
      ? { fill: 'EBF5FB', type: ShadingType.CLEAR }
      : { fill: 'FFFFFF', type: ShadingType.CLEAR },
  margins: { top: 100, bottom: 100, left: 150, right: 150 },
  verticalAlign: VerticalAlign.CENTER,
  children: [new Paragraph({
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
    children: [new TextRun({
      text,
      bold:  !!opts.bold || !!opts.header,
      color: opts.header ? 'FFFFFF' : (opts.color || '000000'),
      size:  opts.size || 20,
      font:  'Arial',
    })]
  })]
});

const hrow = (cells, widths) => new TableRow({
  tableHeader: true,
  children: cells.map((t, i) => cell(t, { header: true, w: widths[i], bold: true }))
});

const row = (cells, widths, shade = false) => new TableRow({
  children: cells.map((t, i) => cell(t, { w: widths[i], shade }))
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 180 },
  children: [new TextRun({ text, font: 'Arial', size: 32, bold: true, color: '1A5276' })]
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, font: 'Arial', size: 26, bold: true, color: '2980B9' })]
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, font: 'Arial', size: 22, bold: true, color: '1F618D' })]
});

const p = (text, opts = {}) => new Paragraph({
  spacing: { before: 80, after: 120 },
  alignment: opts.justify ? AlignmentType.JUSTIFIED : AlignmentType.LEFT,
  children: [new TextRun({ text, font: 'Arial', size: 20, color: '2C3E50', ...opts })]
});

const bullet = (text) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { before: 60, after: 60 },
  children: [new TextRun({ text, font: 'Arial', size: 20, color: '2C3E50' })]
});

const code = (text) => new Paragraph({
  spacing: { before: 80, after: 80 },
  indent: { left: 720 },
  children: [new TextRun({ text, font: 'Courier New', size: 18, color: '1A5276' })]
});

const hr = () => new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: 'AED6F1', space: 1 } },
  spacing: { before: 120, after: 120 },
  children: []
});

const pgBreak = () => new Paragraph({ children: [new PageBreak()] });

const imgPara = (file, w, h, caption = '') => {
  const i = img(file, w, h);
  if (!i) return p(`[Image: ${file} — non disponible]`, { color: '999999', italics: true });
  const items = [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, children: [i] })
  ];
  if (caption) items.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 40, after: 160 },
    children: [new TextRun({ text: caption, font: 'Arial', size: 18, italics: true, color: '7F8C8D' })]
  }));
  return items;
};

// ── DOCUMENT ─────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: '•',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 20 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run:  { size: 32, bold: true, font: 'Arial', color: '1A5276' },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run:  { size: 26, bold: true, font: 'Arial', color: '2980B9' },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run:  { size: 22, bold: true, font: 'Arial', color: '1F618D' },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 }
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '2980B9', space: 1 } },
        spacing: { after: 80 },
        children: [
          new TextRun({ text: 'SignBridge — Rapport Technique', font: 'Arial', size: 18, bold: true, color: '1A5276' }),
          new TextRun({ text: '   |   ENSET de Douala — Niveau 3', font: 'Arial', size: 18, color: '7F8C8D' }),
        ]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: '2980B9', space: 1 } },
        spacing: { before: 80 },
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: 'Page ', font: 'Arial', size: 18, color: '7F8C8D' }),
          new TextRun({ children: [PageNumber.CURRENT], font: 'Arial', size: 18, color: '2980B9' }),
          new TextRun({ text: ' / ', font: 'Arial', size: 18, color: '7F8C8D' }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: 'Arial', size: 18, color: '7F8C8D' }),
        ]
      })] })
    },
    children: [

      // ══════════════════════════════════════════════════════════════════════
      // PAGE DE TITRE
      // ══════════════════════════════════════════════════════════════════════
      new Paragraph({ spacing: { before: 1200, after: 0 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'RAPPORT TECHNIQUE', font: 'Arial', size: 48, bold: true, color: 'FFFFFF',
          highlight: undefined }),
      ]}),

      new Paragraph({ spacing: { before: 0, after: 0 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'SignBridge', font: 'Arial', size: 80, bold: true, color: '1A5276' }),
      ]}),
      new Paragraph({ spacing: { before: 0, after: 120 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'Plateforme de Traduction de la Langue des Signes par Intelligence Artificielle', font: 'Arial', size: 28, color: '2980B9', italics: true }),
      ]}),

      hr(),

      new Paragraph({ spacing: { before: 360, after: 80 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'Établissement : ENSET de Douala', font: 'Arial', size: 22, color: '2C3E50' }),
      ]}),
      new Paragraph({ spacing: { before: 0, after: 80 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'Auteur : Brice Jeason  |  Niveau 3', font: 'Arial', size: 22, bold: true, color: '2C3E50' }),
      ]}),
      new Paragraph({ spacing: { before: 0, after: 80 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'Projet : SignBridge — Groupe RYDI', font: 'Arial', size: 22, color: '2C3E50' }),
      ]}),
      new Paragraph({ spacing: { before: 0, after: 80 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: `Date : ${new Date().toLocaleDateString('fr-FR', { year:'numeric', month:'long', day:'numeric' })}`, font: 'Arial', size: 22, color: '2C3E50' }),
      ]}),

      hr(),

      new Paragraph({ spacing: { before: 600, after: 120 }, alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: 'Technologies : Python 3.10 · Django 5.2 · MediaPipe · scikit-learn · TensorFlow · Three.js', font: 'Arial', size: 18, color: '7F8C8D', italics: true }),
      ]}),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // TABLE DES MATIÈRES
      // ══════════════════════════════════════════════════════════════════════
      h1('Table des Matières'),
      new TableOfContents('Table des Matières', { hyperlink: true, headingStyleRange: '1-3' }),
      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 1. PRÉSENTATION DU PROJET
      // ══════════════════════════════════════════════════════════════════════
      h1('1. Présentation du Projet SignBridge'),
      p('SignBridge est une application web full-stack de traduction bidirectionnelle de la langue des signes. Elle permet à des utilisateurs entendants et malentendants de communiquer à travers trois modes complémentaires : la traduction de texte vers signe (avatar 2D ou main 3D), la reconnaissance de signe en temps réel via webcam, et la traduction d\'une vidéo de signe vers du texte français.', { justify: true }),
      p('Le projet a été développé dans le cadre d\'un cursus de niveau 3 à l\'ENSET de Douala, groupe RYDI. Il constitue un prototype fonctionnel démontrant l\'intégration de techniques d\'intelligence artificielle modernes dans une interface web accessible.', { justify: true }),

      h2('1.1 Objectifs'),
      bullet('Permettre la traduction Texte → Signe ASL/LSF via un avatar 2D et une main 3D procédurale'),
      bullet('Reconnaître les signes en temps réel depuis la webcam de l\'utilisateur'),
      bullet('Offrir un dictionnaire visuel des signes A-Z et 0-9'),
      bullet('Fournir une interface d\'administration pour gérer le dataset et entraîner le modèle ML'),

      h2('1.2 Capture d\'écran — Page d\'accueil'),
      ...imgPara('page_landing.png', 580, 326, 'Figure 1 : Page d\'accueil de SignBridge'),

      h2('1.3 Capture d\'écran — Interface principale'),
      ...imgPara('page_app_text.png', 580, 326, 'Figure 2 : Interface principale — Mode Texte → Signe'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 2. TECHNOLOGIES UTILISÉES
      // ══════════════════════════════════════════════════════════════════════
      h1('2. Technologies Utilisées et leur Rôle'),

      h2('2.1 Backend — Python / Django'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2400, 3000, 4200],
        rows: [
          hrow(['Technologie', 'Version', 'Rôle dans SignBridge'], [2400, 3000, 4200]),
          row(['Django', '5.2', 'Framework web principal — routing HTTP, ORM, gestion des sessions, templates Jinja2'], [2400, 3000, 4200], false),
          row(['Django Channels', '4.1.0', 'Extension Django pour WebSocket ASGI — communication temps réel pour la reconnaissance gestuelle'], [2400, 3000, 4200], true),
          row(['Daphne', '4.1.0', 'Serveur ASGI — sert simultanément HTTP et WebSocket (protocoles asynchrones)'], [2400, 3000, 4200], false),
          row(['WhiteNoise', '6.6.0', 'Sert les fichiers statiques (CSS, JS, images, modèles GLB) directement depuis Django sans Nginx'], [2400, 3000, 4200], true),
          row(['python-dotenv', '1.0.1', 'Chargement des variables d\'environnement depuis le fichier .env (SECRET_KEY, DEBUG, etc.)'], [2400, 3000, 4200], false),
          row(['Gunicorn', '21.2.0', 'Serveur WSGI de production pour le déploiement'], [2400, 3000, 4200], true),
        ]
      }),

      h2('2.2 Intelligence Artificielle et Machine Learning'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2400, 3000, 4200],
        rows: [
          hrow(['Bibliothèque', 'Version', 'Rôle'], [2400, 3000, 4200]),
          row(['MediaPipe', '0.10.11', 'Extraction des 21 landmarks de la main (x, y, z) en temps réel — cœur de la détection gestuelle'], [2400, 3000, 4200], false),
          row(['scikit-learn', '1.4.2', 'Random Forest Classifier — modèle principal de classification statique des signes (36 classes A-Z + 0-9)'], [2400, 3000, 4200], true),
          row(['TensorFlow', '2.15.0', 'LSTM (Long Short-Term Memory) — classification de séquences dynamiques de signes (30 frames)'], [2400, 3000, 4200], false),
          row(['NumPy', '1.26.4', 'Manipulation des tableaux de landmarks, normalisation, calcul des poses moyennes pour l\'avatar'], [2400, 3000, 4200], true),
          row(['joblib', '1.3.2', 'Sérialisation/désérialisation du modèle Random Forest (rf_model.pkl, 769 Mo)'], [2400, 3000, 4200], false),
          row(['OpenCV', '4.9.0', 'Lecture et décodage des fichiers vidéo pour l\'extraction frame-par-frame'], [2400, 3000, 4200], true),
        ]
      }),

      h2('2.3 Frontend — Interface Utilisateur'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2400, 2400, 4800],
        rows: [
          hrow(['Technologie', 'Version', 'Rôle'], [2400, 2400, 4800]),
          row(['Tailwind CSS', '3.4.1', 'Framework CSS utility-first — styles compilés avec npx, thème sombre/clair'], [2400, 2400, 4800], false),
          row(['Three.js', 'r160.1', 'Rendu 3D WebGL — visualisation de la main procédurale (21 sphères + 26 cylindres) avec animations fluides'], [2400, 2400, 4800], true),
          row(['MediaPipe JS', '0.10.x', 'Détection des landmarks main côté client via WebAssembly — traitement vidéo en temps réel dans le navigateur'], [2400, 2400, 4800], false),
          row(['Web Speech API', 'Natif', 'Reconnaissance vocale — dictée du texte à signer dans l\'interface'], [2400, 2400, 4800], true),
          row(['WebSocket API', 'Natif', 'Communication bidirectionnelle avec le serveur Django Channels pour l\'envoi de landmarks'], [2400, 2400, 4800], false),
          row(['Canvas 2D API', 'Natif', 'Rendu des images de signes ASL avec animation flottante (HandSignRenderer)'], [2400, 2400, 4800], true),
        ]
      }),

      h2('2.4 Base de données'),
      p('Le projet utilise SQLite comme base de données relationnelle embarquée. À la date d\'analyse, la base db.sqlite3 occupe 58 Mo et contient notamment :'),
      bullet('38 087 DatasetSample (landmarks de mains pour 36 signes)'),
      bullet('36 SignDictionary (alphabet A-Z + chiffres 0-9)'),
      bullet('Comptes utilisateurs, sessions de traduction, versions du modèle ML'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 3. OUTILS MATÉRIELS ET LOGICIELS
      // ══════════════════════════════════════════════════════════════════════
      h1('3. Outils Matériels et Logiciels'),

      h2('3.1 Environnement de développement'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2800, 6800],
        rows: [
          hrow(['Outil', 'Description'], [2800, 6800]),
          row(['Python 3.10+', 'Langage backend — compatible avec MediaPipe 0.10.x et TensorFlow 2.15'], [2800, 6800], false),
          row(['Node.js / npm', 'Compilation du CSS Tailwind (npm run build:css) — seule dépendance JS côté dev'], [2800, 6800], true),
          row(['VS Code / IDE', 'Environnement de développement principal'], [2800, 6800], false),
          row(['Git', 'Gestion de versions du code source'], [2800, 6800], true),
          row(['SQLite Browser', 'Inspection et requêtes directes sur db.sqlite3'], [2800, 6800], false),
        ]
      }),

      h2('3.2 Matériel requis'),
      bullet('Webcam HD (720p minimum) — pour la reconnaissance gestuelle en temps réel'),
      bullet('RAM ≥ 4 Go — le modèle Random Forest (rf_model.pkl) charge 769 Mo en mémoire au démarrage'),
      bullet('Navigateur moderne avec WebGL 2.0 — pour le rendu Three.js (Chrome, Firefox, Edge récents)'),
      bullet('Processeur multi-cœur — TensorFlow peut utiliser les cœurs CPU pour l\'inférence LSTM'),

      h2('3.3 Datasets utilisés'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [3200, 2200, 4200],
        rows: [
          hrow(['Dataset', 'Source', 'Contenu'], [3200, 2200, 4200]),
          row(['mediapipe-processed-asl-dataset', 'Kaggle (vignonantoine)', '20 834 landmarks A-Z et 0-9 extraits de vidéos ASL (coordonnées 2D pour les lettres)'], [3200, 2200, 4200], false),
          row(['American Sign Language Digits Dataset', 'Kaggle (Images JPEG)', '2 853 landmarks 0-9 extraits via MediaPipe — vraies coordonnées 3D'], [3200, 2200, 4200], true),
          row(['Données synthétiques ASL_POSES', 'Génération interne', '14 400 samples générés par augmentation mathématique (bruit, rotation, échelle) à partir de poses hardcodées'], [3200, 2200, 4200], false),
        ]
      }),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 4. MÉTHODES IA POUR LA DÉTECTION DE SIGNES
      // ══════════════════════════════════════════════════════════════════════
      h1('4. Méthodes d\'Intelligence Artificielle'),

      h2('4.1 Extraction de landmarks — MediaPipe Hands'),
      p('MediaPipe Hands est la brique fondamentale de la détection gestuelle dans SignBridge. Développé par Google, il détecte et suit la main en temps réel à partir d\'une image ou d\'un flux vidéo.', { justify: true }),

      h3('Principe de fonctionnement'),
      bullet('Détection de paume : un modèle CNN léger (MobileNet) localise d\'abord la paume dans l\'image complète'),
      bullet('Régression des landmarks : un second réseau prédit la position précise des 21 points anatomiques de la main'),
      bullet('Coordonnées retournées : x, y normalisés [0-1] dans l\'espace image, z (profondeur relative) dans la même échelle'),
      bullet('Traitement : 12-30 fps côté navigateur (WebAssembly), ou en Python côté serveur pour les vidéos'),

      h3('Les 21 points landmarks MediaPipe'),
      p('Chaque main est représentée par 21 landmarks numérotés de 0 à 20 :'),
      bullet('Point 0 : Poignet (wrist) — point de référence pour la normalisation'),
      bullet('Points 1-4 : Pouce (CMC, MCP, IP, Tip)'),
      bullet('Points 5-8 : Index (MCP, PIP, DIP, Tip)'),
      bullet('Points 9-12 : Majeur (MCP, PIP, DIP, Tip)'),
      bullet('Points 13-16 : Annulaire (MCP, PIP, DIP, Tip)'),
      bullet('Points 17-20 : Auriculaire (MCP, PIP, DIP, Tip)'),
      p('Le vecteur de features est de dimension 63 (21 points × 3 coordonnées x,y,z). Avant classification, il est normalisé par centrage sur le poignet (point 0 soustrait de tous les points) pour rendre la prédiction invariante à la position de la main dans l\'image.', { justify: true }),

      h2('4.2 Classification statique — Random Forest'),
      p('Le modèle principal de SignBridge est un Random Forest Classifier de scikit-learn, entraîné pour classer 36 signes distincts (lettres A-Z et chiffres 0-9).', { justify: true }),

      h3('Caractéristiques du modèle'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [3200, 6400],
        rows: [
          hrow(['Paramètre', 'Valeur'], [3200, 6400]),
          row(['Algorithme', 'Random Forest Classifier (ensemble de 100 arbres de décision)'], [3200, 6400], false),
          row(['Classes', '36 (A à Z + 0 à 9)'], [3200, 6400], true),
          row(['Features d\'entrée', '63 floats (21 landmarks × 3 coordonnées)'], [3200, 6400], false),
          row(['Taille du modèle', '769 Mo (rf_model.pkl sérialisé par joblib)'], [3200, 6400], true),
          row(['Précision', '83% (accuracy sur jeu de test)'], [3200, 6400], false),
          row(['Fichier', 'signbridge_model/rf_model.pkl'], [3200, 6400], true),
          row(['Encodeur', 'LabelEncoder — signbridge_model/label_encoder.pkl'], [3200, 6400], false),
          row(['Chargement', 'Singleton au démarrage Django (AppConfig.ready() en thread daemon)'], [3200, 6400], true),
        ]
      }),

      h2('4.3 Classification dynamique — LSTM (Long Short-Term Memory)'),
      p('Pour la reconnaissance de signes dynamiques (nécessitant un mouvement), SignBridge intègre un réseau LSTM implémenté avec TensorFlow/Keras.', { justify: true }),
      bullet('Entrée : séquence de 30 frames consécutives de landmarks (30 × 63 = 1890 valeurs)'),
      bullet('Architecture : couches LSTM empilées suivies de couches Dense avec activation softmax'),
      bullet('Segmentation : la vidéo est découpée en segments de 30 frames avec chevauchement de 15 frames'),
      bullet('Seuil de confiance : seulement les prédictions avec confidence > 0.6 sont retenues'),
      bullet('Fichiers : lstm_model.keras (prioritaire) et lstm_model.h5 (fallback)'),

      h2('4.4 Pipeline de reconnaissance en temps réel'),
      p('Le flux complet de reconnaissance via webcam suit cette pipeline :'),
      bullet('1. Frame vidéo capturée par le navigateur (getUserMedia)'),
      bullet('2. MediaPipe JS détecte les 21 landmarks (WASM, ~12 fps)'),
      bullet('3. Les coordonnées sont envoyées via WebSocket au serveur Django Channels'),
      bullet('4. SignRecognitionConsumer normalise les landmarks (centrage poignet)'),
      bullet('5. GestureClassifier.predict_static() appelle le Random Forest'),
      bullet('6. Le label et la confidence sont retournés au navigateur via WebSocket'),
      bullet('7. Mécanisme de stabilisation : 3 frames consécutives identiques requises avant validation (STABLE_NEEDED = 3)'),
      bullet('8. Seuil de confiance : 0.22 normal, 0.11 si signe stable depuis 6 frames'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 5. MODULES DÉVELOPPÉS
      // ══════════════════════════════════════════════════════════════════════
      h1('5. Modules Développés'),

      h2('5.1 Module Backend — core/'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2800, 6800],
        rows: [
          hrow(['Fichier', 'Description'], [2800, 6800]),
          row(['models.py', '5 modèles ORM : CustomUser (email login), SignDictionary, DatasetSample (landmarks), TranslationSession, MLModelVersion'], [2800, 6800], false),
          row(['views.py', '18 vues : 7 pages HTML + 7 endpoints API JSON (translate, dictionary, ml/status, stats, train, avatar-landmarks, video-to-text)'], [2800, 6800], true),
          row(['consumers.py', 'SignRecognitionConsumer — WebSocket ASGI : reçoit landmarks JSON, appelle GestureClassifier, retourne prédiction'], [2800, 6800], false),
          row(['forms.py', 'InscriptionForm + ConnexionForm (authentification par email)'], [2800, 6800], true),
          row(['decorators.py', '@admin_required — décorateur de protection des vues admin'], [2800, 6800], false),
          row(['apps.py', 'AppConfig.ready() — chargement du modèle RF en thread daemon au démarrage'], [2800, 6800], true),
          row(['routing.py', 'Routage WebSocket : ws/sign-recognition/ → SignRecognitionConsumer'], [2800, 6800], false),
          row(['urls.py', '14 routes URL (pages publiques, pages protégées, panel admin, API)'], [2800, 6800], true),
        ]
      }),

      h2('5.2 Module ML — ml_engine/'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2800, 6800],
        rows: [
          hrow(['Fichier', 'Description'], [2800, 6800]),
          row(['gesture_classifier.py', 'Singleton GestureClassifier — charge RF + LSTM, expose predict_static() et predict_dynamic()'], [2800, 6800], false),
          row(['landmark_extractor.py', 'LandmarkExtractor — wrapper MediaPipe Python, extrait landmarks depuis frame ou fichier vidéo'], [2800, 6800], true),
          row(['model_trainer.py', 'ModelTrainer — entraîne RF et LSTM depuis les DatasetSample en base, sauvegarde les modèles'], [2800, 6800], false),
          row(['dataset_manager.py', 'Chargement du dataset depuis la DB, sauvegarde de nouveaux DatasetSample'], [2800, 6800], true),
          row(['video_processor.py', 'VideoProcessor — traite une vidéo complète (extraction → segmentation → classification → texte)'], [2800, 6800], false),
        ]
      }),

      h2('5.3 Module Frontend — static/js/'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2800, 6800],
        rows: [
          hrow(['Fichier JS', 'Rôle'], [2800, 6800]),
          row(['webcam_client.js', 'Client WebSocket + initialisation MediaPipe — gère la boucle de capture et l\'envoi des landmarks'], [2800, 6800], false),
          row(['hand3d_renderer.js', 'Renderer Three.js — construit une main 3D procédurale (21 sphères + 26 cylindres), interpole les poses (tween ease-in-out)'], [2800, 6800], true),
          row(['hand_sign_renderer.js', 'Renderer Canvas 2D — affiche les images JPG des signes avec animation flottante (breathing)'], [2800, 6800], false),
          row(['avatar_player.js', 'AvatarPlayer — joue une séquence de signes avec gestion race-condition par compteur de génération'], [2800, 6800], true),
          row(['speech_input.js', 'SpeechInput — wrapper Web Speech API pour la saisie vocale du texte à traduire'], [2800, 6800], false),
          row(['video_upload.js', 'VideoUpload — upload vidéo XHR avec validation taille/format, barre de progression'], [2800, 6800], true),
        ]
      }),

      h2('5.4 Commandes de gestion (manage.py)'),
      bullet('setup_demo_data — crée 36 signes + comptes admin/démo en base'),
      bullet('train_model --algo all — entraîne RF et/ou LSTM depuis les DatasetSample'),
      bullet('extract_landmarks — extrait landmarks depuis vidéos brutes'),
      bullet('extract_from_images — extrait landmarks depuis images JPEG'),
      bullet('import_kaggle_asl — importe le dataset ASL Kaggle (CSV landmarks)'),
      bullet('import_landmarks_json — importe un fichier JSON de landmarks'),
      bullet('generate_asl_training — génère 14 400 DatasetSample synthétiques (A-Z + 0-9)'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 6. PROCÉDURE DE CRÉATION DES AVATARS 3D
      // ══════════════════════════════════════════════════════════════════════
      h1('6. Procédure de Création des Avatars 3D'),

      h2('6.1 Architecture de l\'avatar — Hand3DRenderer'),
      p('L\'avatar 3D de SignBridge est une main procédurale construite entièrement en Three.js, sans mesh 3D externe ni fichier de modèle. Elle est composée de primitives géométriques positionnées selon les landmarks MediaPipe.', { justify: true }),

      h3('Composition géométrique'),
      bullet('21 sphères (SphereGeometry) — une par articulation, taille variable : 0.040 pour le poignet, 0.026 pour les extrémités, 0.021 pour les nœuds intermédiaires'),
      bullet('26 cylindres (CylinderGeometry) — un par connexion osseuse, reliant les articulations selon la topologie MediaPipe'),
      bullet('Couleurs par doigt : vert (poignet), ambre (pouce), bleu (index), violet (majeur), rose (annulaire), cyan (auriculaire)'),
      bullet('Matériaux MeshPhong avec shininess et émissivité légère pour un rendu 3D réaliste'),

      h3('Connexions topologiques'),
      code('[0,1],[1,2],[2,3],[3,4]       // Pouce (4 segments)'),
      code('[0,5],[5,6],[6,7],[7,8]       // Index (4 segments)'),
      code('[0,9],[9,10],[10,11],[11,12]  // Majeur (4 segments)'),
      code('[0,13],[13,14],[14,15],[15,16] // Annulaire (4 segments)'),
      code('[0,17],[17,18],[18,19],[19,20] // Auriculaire (4 segments)'),
      code('[5,9],[9,13],[13,17]          // Paume (3 connexions transverses)'),

      h2('6.2 Pipeline des poses — de la source aux coordonnées 3D'),
      p('Les poses de l\'avatar sont générées via la commande generate_asl_training puis stockées en base de données. L\'API /api/avatar-landmarks/ les calcule et les retourne au navigateur.', { justify: true }),

      h3('Étape 1 — Définition des poses (generate_asl_training.py)'),
      p('Chaque signe A-Z et 0-9 est défini par un dictionnaire ASL_POSES contenant les positions 3D des 21 landmarks pour la pose de référence. Ces coordonnées sont définies manuellement comme des vecteurs NumPy simulant une vue depuis une caméra frontale.'),

      h3('Étape 2 — Augmentation des données'),
      bullet('300 variantes générées par signe par la fonction augment()'),
      bullet('Bruit gaussien σ = 2.6% sur toutes les coordonnées'),
      bullet('Rotation 2D aléatoire ±15° dans le plan XY'),
      bullet('Mise à l\'échelle ±12% (zoom in/out)'),
      bullet('Translation ±4% (déplacement de la main)'),
      bullet('Normalisation par la distance poignet→MCP-majeur'),
      bullet('Résultat : 14 400 DatasetSample avec source=\'GENERATED\''),

      h3('Étape 3 — Calcul de la pose moyenne (API)'),
      bullet('GET /api/avatar-landmarks/ récupère les 40 premiers samples par signe'),
      bullet('Moyenne NumPy des vecteurs de 63 floats → reshape (21, 3)'),
      bullet('Centrage sur le poignet : mean = mean - mean[0]'),
      bullet('Retourne un JSON {A: [{x,y,z}×21], B: [...], ..., 9: [...]}'),

      h3('Étape 4 — Rendu Three.js (hand3d_renderer.js)'),
      bullet('Scale S = 0.75 appliqué aux coordonnées (calibré pour tenir dans le cadre caméra)'),
      bullet('Inversion de l\'axe Y : Three.js Y = -landmark.y × S (MediaPipe Y pointe vers le bas, Three.js vers le haut)'),
      bullet('Position caméra : (0, 0.25, 2.40), regardant (0, 0.25, 0)'),
      bullet('Interpolation tween ease-in-out entre deux poses (450 ms de transition)'),
      bullet('Boucle requestAnimationFrame à ~60 fps'),

      h2('6.3 Captures — Mode Avatar 3D'),
      ...imgPara('page_app_avatar.png', 580, 326, 'Figure 3 : Mode Avatar 3D — main procédurale Three.js'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 7. RECONNAISSANCE DES SIGNES
      // ══════════════════════════════════════════════════════════════════════
      h1('7. Reconnaissance des Signes — Fonctionnement Détaillé'),

      h2('7.1 Mode Caméra (temps réel)'),
      ...imgPara('page_app_camera.png', 580, 326, 'Figure 4 : Interface — Mode Caméra (Signe → Texte)'),

      p('La reconnaissance en temps réel utilise un pipeline WebSocket bidirectionnel entre le navigateur et le serveur Django Channels. Voici le déroulement :'),
      bullet('L\'utilisateur active la caméra — getUserMedia ouvre le flux vidéo'),
      bullet('MediaPipe Hands JS (WASM) traite chaque frame à ~12 fps'),
      bullet('Les 63 coordonnées sont envoyées via WebSocket (ws://127.0.0.1:8001/ws/sign-recognition/)'),
      bullet('Le consumer Django normalise les landmarks et appelle predict_static()'),
      bullet('Le Random Forest retourne le label et la confidence'),
      bullet('La réponse est retournée au navigateur en JSON'),
      bullet('Mécanisme de stabilisation : STABLE_NEEDED = 3 frames consécutives identiques'),
      bullet('Seuil de confiance adaptatif : 0.22 (normal) → 0.11 après 6 frames stables'),

      h2('7.2 Mode Vidéo (upload)'),
      bullet('Upload XHR du fichier vidéo (MP4, AVI, MOV, WebM — max 100 Mo)'),
      bullet('VideoProcessor.process_video() décode la vidéo avec OpenCV'),
      bullet('Extraction des landmarks frame par frame via LandmarkExtractor (MediaPipe Python)'),
      bullet('Segmentation en fenêtres de 30 frames (chevauchement 15 frames)'),
      bullet('Classification de chaque segment via LSTM (predict_dynamic())'),
      bullet('Seuil confidence > 0.6 pour valider un signe'),
      bullet('Retourne le texte reconstruit + segments détaillés'),

      h2('7.3 Paramètres de stabilisation'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [3600, 3000, 3000],
        rows: [
          hrow(['Paramètre', 'Valeur', 'Effet'], [3600, 3000, 3000]),
          row(['STABLE_NEEDED', '3 frames', 'Nb de prédictions identiques consécutives pour valider un signe'], [3600, 3000, 3000], false),
          row(['CONF_THRESHOLD', '0.22', 'Confiance minimale pour déclencher la validation'], [3600, 3000, 3000], true),
          row(['CONF_SUSTAINED', '0.11', 'Seuil abaissé si le signe est stable depuis 6 frames'], [3600, 3000, 3000], false),
          row(['InMemoryChannelLayer', 'Dev uniquement', 'Layer de canal WebSocket (à remplacer par Redis en production)'], [3600, 3000, 3000], true),
          row(['FPS cible (vidéo)', '10 fps', 'Sous-échantillonnage pour alléger le traitement vidéo'], [3600, 3000, 3000], false),
        ]
      }),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 8. ENTRAÎNEMENT DU MODÈLE
      // ══════════════════════════════════════════════════════════════════════
      h1('8. Entraînement du Modèle ML'),

      h2('8.1 Commande d\'entraînement'),
      p('Le modèle s\'entraîne via la commande Django :'),
      code('python manage.py train_model --algo all'),
      p('Options : --algo rf (Random Forest seul), --algo lstm (LSTM seul), --algo all (les deux).'),

      h2('8.2 Pipeline d\'entraînement — Random Forest'),
      bullet('1. DatasetManager.load_dataset() charge tous les DatasetSample de la DB'),
      bullet('2. Filtrage : qualite=\'BONNE\', landmarks_data non null, longueur ≥ 63 floats'),
      bullet('3. Construction de X (matrice N×63) et y (labels encodés)'),
      bullet('4. Split train/test 80/20 avec stratification (train_test_split)'),
      bullet('5. Entraînement : RandomForestClassifier(n_estimators=100, n_jobs=-1)'),
      bullet('6. Évaluation : accuracy_score + classification_report'),
      bullet('7. Sauvegarde : joblib.dump(model, \'signbridge_model/rf_model.pkl\')'),
      bullet('8. Enregistrement MLModelVersion en base (version, algorithme, accuracy, nb_classes)'),

      h2('8.3 Pipeline d\'entraînement — LSTM'),
      bullet('1. Mêmes DatasetSample chargés, groupés par signe'),
      bullet('2. Normalisation des séquences à target_len=30 frames (padding/interpolation)'),
      bullet('3. Architecture LSTM : couches LSTM (128→64 unités) → Dense (128 → nb_classes) → Softmax'),
      bullet('4. Compilation : optimizer=Adam, loss=sparse_categorical_crossentropy'),
      bullet('5. Entraînement : 50 epochs, batch_size=32, validation_split=0.2'),
      bullet('6. Sauvegarde : model.save(\'signbridge_model/lstm_model.keras\')'),

      h2('8.4 Entraînement via l\'interface admin'),
      p('L\'API POST /api/admin/train/ lance l\'entraînement en arrière-plan (thread daemon) sans bloquer le serveur. L\'interface admin affiche les versions de modèles avec leur accuracy.'),
      ...imgPara('page_admin.png', 580, 326, 'Figure 5 : Panel Administrateur — Gestion du dataset et entraînement'),

      h2('8.5 Composition du dataset (38 087 samples)'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [2800, 2000, 2200, 2600],
        rows: [
          hrow(['Source', 'Nb Samples', 'Signes couverts', 'Qualité coordonnées Z'], [2800, 2000, 2200, 2600]),
          row(['GENERATED (synthétique)', '14 400', 'A-Z + 0-9 (36)', '3D artificiel (bruit gaussien)'], [2800, 2000, 2200, 2600], false),
          row(['KAGGLE (CSV)', '20 834', 'A-Z + 0-9 (36)', 'Z=0 pour A-Z (2D), 3D pour 0-9'], [2800, 2000, 2200, 2600], true),
          row(['KAGGLE_IMG (MediaPipe réel)', '2 853', '0-9 uniquement', 'Vraie profondeur 3D'], [2800, 2000, 2200, 2600], false),
          row(['TOTAL', '38 087', '36 signes', '—'], [2800, 2000, 2200, 2600], true),
        ]
      }),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 9. CONFIGURATIONS
      // ══════════════════════════════════════════════════════════════════════
      h1('9. Configurations du Projet'),

      h2('9.1 Fichier .env (variables d\'environnement)'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [3200, 2400, 4000],
        rows: [
          hrow(['Variable', 'Valeur (dev)', 'Rôle'], [3200, 2400, 4000]),
          row(['SECRET_KEY', '(50 chars aléatoires)', 'Clé de signature Django (sessions, CSRF)'], [3200, 2400, 4000], false),
          row(['DEBUG', 'True', 'Mode debug Django — à mettre False en production'], [3200, 2400, 4000], true),
          row(['ALLOWED_HOSTS', '127.0.0.1,localhost', 'Hôtes autorisés à accéder au serveur'], [3200, 2400, 4000], false),
          row(['DATABASE_URL', 'sqlite:///db.sqlite3', 'Chemin de la base SQLite'], [3200, 2400, 4000], true),
          row(['ML_MODEL_DIR', 'signbridge_model/', 'Répertoire des modèles ML sérialisés'], [3200, 2400, 4000], false),
        ]
      }),

      h2('9.2 Configuration Django (config/settings.py)'),
      bullet('AUTH_USER_MODEL = \'core.CustomUser\' — modèle utilisateur personnalisé (login par email)'),
      bullet('ASGI_APPLICATION = \'config.asgi.application\' — serveur ASGI Daphne/Channels'),
      bullet('CHANNEL_LAYERS : InMemoryChannelLayer (développement) — à remplacer par Redis en production'),
      bullet('STATICFILES_DIRS : inclut static/ et static_signs/ (animations GLB + images)'),
      bullet('STATICFILES_STORAGE : WhiteNoiseStorage avec compression Brotli/Gzip'),
      bullet('ML_MODEL_DIR = BASE_DIR / \'signbridge_model\' — chemin des modèles'),

      h2('9.3 Configuration ASGI (config/asgi.py)'),
      p('Le routeur ASGI dispatche les connexions entre HTTP (Django) et WebSocket (Channels) :'),
      code('HTTP  → django_asgi_app'),
      code('ws/sign-recognition/ → SignRecognitionConsumer (WebSocket)'),

      h2('9.4 Démarrage du serveur'),
      p('Développement :'),
      code('python manage.py migrate'),
      code('python manage.py setup_demo_data'),
      code('daphne -p 8001 config.asgi:application'),
      p('CSS (si node_modules manquant) :'),
      code('npm install && npm run build:css'),

      h2('9.5 Paramètres du renderer 3D (hand3d_renderer.js)'),
      new Table({
        width: { size: 9600, type: WidthType.DXA },
        columnWidths: [3200, 2400, 4000],
        rows: [
          hrow(['Paramètre', 'Valeur', 'Rôle'], [3200, 2400, 4000]),
          row(['Scale S', '0.75', 'Facteur d\'échelle des landmarks — réduit pour éviter le débordement du cadre'], [3200, 2400, 4000], false),
          row(['camera.position', '(0, 0.25, 2.40)', 'Position de la caméra Three.js'], [3200, 2400, 4000], true),
          row(['camera.lookAt', '(0, 0.25, 0)', 'Point de visée — centré sur la main'], [3200, 2400, 4000], false),
          row(['FOV', '50°', 'Champ de vision vertical de la caméra perspective'], [3200, 2400, 4000], true),
          row(['tweenDur', '450 ms', 'Durée de la transition entre deux poses (ease-in-out)'], [3200, 2400, 4000], false),
          row(['holdDur (normal)', '900 ms', 'Durée d\'affichage de chaque signe en vitesse normale'], [3200, 2400, 4000], true),
          row(['Pixel Ratio', 'min(devicePixelRatio, 2)', 'Résolution du rendu WebGL'], [3200, 2400, 4000], false),
        ]
      }),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 10. DIAGRAMMES UML
      // ══════════════════════════════════════════════════════════════════════
      h1('10. Diagrammes UML'),

      h2('10.1 Diagramme de Cas d\'Utilisation'),
      p('Ce diagramme présente les interactions entre les trois types d\'acteurs du système (visiteur non connecté, utilisateur connecté, administrateur) et les fonctionnalités offertes par SignBridge.'),
      ...imgPara('use_case.png', 620, 460, 'Figure 6 : Diagramme de Cas d\'Utilisation — SignBridge'),

      h2('10.2 Diagramme de Séquence — Reconnaissance Webcam'),
      p('Ce diagramme décrit le flux complet d\'une session de reconnaissance gestuelle en temps réel, depuis la capture vidéo dans le navigateur jusqu\'au retour du signe reconnu.'),
      ...imgPara('sequence_webcam.png', 620, 460, 'Figure 7 : Diagramme de Séquence — Mode Caméra (Signe → Texte)'),

      h2('10.3 Diagramme de Séquence — Texte vers Avatar 3D'),
      p('Ce diagramme illustre le flux de traduction d\'un texte vers l\'animation de la main 3D, incluant l\'initialisation du renderer et le chargement des poses depuis l\'API.'),
      ...imgPara('sequence_tts.png', 620, 460, 'Figure 8 : Diagramme de Séquence — Mode Texte → Avatar 3D'),

      pgBreak(),

      h2('10.4 Diagramme de Classes'),
      p('Ce diagramme présente les classes principales du projet, leurs attributs, méthodes et relations. Il couvre à la fois les modèles Django (couche données) et les classes du moteur ML.'),
      ...imgPara('class_diagram.png', 620, 500, 'Figure 9 : Diagramme de Classes — Modèles Django + Moteur ML'),

      h2('10.5 Schéma Synoptique de l\'Architecture'),
      p('Ce schéma présente l\'architecture complète en couches de SignBridge : présentation (navigateur), transport (HTTP/WebSocket), application (Django), ML/IA et données.'),
      ...imgPara('synoptic.png', 620, 480, 'Figure 10 : Schéma Synoptique — Architecture globale SignBridge'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 11. DICTIONNAIRE
      // ══════════════════════════════════════════════════════════════════════
      h1('11. Dictionnaire des Signes'),
      p('Le dictionnaire de SignBridge recense 36 signes validés : les 26 lettres de l\'alphabet (A-Z) et les 10 chiffres (0-9). Chaque entrée contient une description textuelle du geste, une image de référence, la catégorie (ALPHABET ou CHIFFRE), et un niveau de difficulté.'),
      ...imgPara('page_dictionary.png', 580, 326, 'Figure 11 : Dictionnaire LSF/ASL — Vue d\'ensemble des signes'),

      h2('11.1 Code PlantUML des diagrammes'),
      p('Les diagrammes ont été générés via le serveur public PlantUML (plantuml.com). Le code source de chaque diagramme est inclus dans le fichier doc_assets/generate_diagrams.py du projet pour faciliter leur régénération ou modification.'),
      code('python doc_assets/generate_diagrams.py'),
      p('L\'URL de génération suit le format :'),
      code('https://www.plantuml.com/plantuml/png/{encoded_deflate_base64}'),

      pgBreak(),

      // ══════════════════════════════════════════════════════════════════════
      // 12. CONCLUSION
      // ══════════════════════════════════════════════════════════════════════
      h1('12. Conclusion'),
      p('SignBridge est un projet full-stack ambitieux qui intègre avec succès plusieurs technologies d\'intelligence artificielle dans une interface web moderne et accessible. Les points forts du projet sont :', { justify: true }),
      bullet('Une reconnaissance gestuelle fonctionnelle en temps réel (Random Forest, 83% de précision, 36 classes)'),
      bullet('Un pipeline WebSocket réactif basé sur Django Channels/Daphne pour la communication asynchrone'),
      bullet('Un renderer 3D procédural original en Three.js, sans recours à des assets 3D externes'),
      bullet('Une architecture modulaire claire séparant présentation, application, ML et données'),
      bullet('Une interface d\'administration complète pour la gestion du dataset et l\'entraînement'),
      p('Les pistes d\'amélioration identifiées sont :', { justify: true }),
      bullet('Capturer de vraies données LSF (Langue des Signes Française) avec des locuteurs natifs — les données actuelles sont ASL'),
      bullet('Remplacer InMemoryChannelLayer par Redis Channels en production pour la scalabilité'),
      bullet('Optimiser le chargement du modèle RF (769 Mo) via quantification ou compression'),
      bullet('Ajouter de vrais fichiers GLB avec animations pour le mode Texte→Signe (les .glb actuels sont des stubs vides)'),
      bullet('Mettre SESSION_COOKIE_SECURE=True et configurer un proxy HTTPS pour le déploiement production'),

      hr(),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0 }, children: [
        new TextRun({ text: 'ENSET de Douala — Groupe RYDI — Brice Jeason — Niveau 3', font: 'Arial', size: 18, italics: true, color: '7F8C8D' })
      ]}),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(OUT, 'SignBridge_Rapport_Technique.docx');
  fs.writeFileSync(out, buf);
  console.log(`Document créé : ${out} (${(buf.length/1024).toFixed(0)} KB)`);
}).catch(e => { console.error(e); process.exit(1); });
