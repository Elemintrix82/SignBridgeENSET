import django, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import SignDictionary

# 1. Supprimer les signes mots/phrases
deleted = SignDictionary.objects.exclude(categorie__in=['ALPHABET','CHIFFRE']).delete()
print("Supprimes:", deleted[0])

ALPHA = {
    'A': "Poing ferme, pouce sur le cote de l'index.",
    'B': "Quatre doigts tendus et joints, pouce replie dans la paume.",
    'C': "Main courbee en forme de C, doigts et pouce ecartes.",
    'D': "Index droit pointe vers le haut, autres doigts forment un arc touchant le pouce.",
    'E': "Doigts replies vers la paume, pouce plie sous les doigts.",
    'F': "Pouce et index se touchent en cercle, trois autres doigts etendus.",
    'G': "Index et pouce horizontaux pointant sur le cote.",
    'H': "Index et majeur tendus cote a cote, horizontalement.",
    'I': "Auriculaire tendu vers le haut, autres doigts fermes en poing.",
    'J': "Auriculaire tendu, tracer la lettre J dans l'air.",
    'K': "Index et majeur en V, pouce place entre eux.",
    'L': "Pouce et index forment un L, autres doigts replies.",
    'M': "Trois premiers doigts replies par-dessus le pouce.",
    'N': "Index et majeur replies par-dessus le pouce.",
    'O': "Tous les doigts courbes forment un O avec le pouce.",
    'P': "Main inclinee vers le bas, index tendu, pouce ecartes.",
    'Q': "Index et pouce pointant vers le bas.",
    'R': "Index et majeur croises, pouce tendu sur le cote.",
    'S': "Poing ferme, pouce pose sur les doigts (devant).",
    'T': "Poing ferme, pouce coince entre index et majeur.",
    'U': "Index et majeur tendus joints et droits.",
    'V': "Index et majeur ecartes en V (victoire).",
    'W': "Index, majeur et annulaire tendus et ecartes.",
    'X': "Index replie en crochet, les autres doigts fermes.",
    'Y': "Pouce et auriculaire tendus, trois doigts du milieu fermes.",
    'Z': "Index tendu trace la lettre Z dans l'air.",
}

NUMS = {
    '0': "Tous les doigts courbes forment un O avec le pouce.",
    '1': "Index tendu vers le haut, autres doigts fermes.",
    '2': "Index et majeur tendus en V, pouce ferme.",
    '3': "Pouce, index et majeur tendus, deux derniers fermes.",
    '4': "Quatre doigts tendus, pouce replie dans la paume.",
    '5': "Main grande ouverte, cinq doigts etendus et ecartes.",
    '6': "Pouce et auriculaire se touchent, autres doigts etendus.",
    '7': "Pouce et annulaire se touchent, autres doigts etendus.",
    '8': "Pouce et majeur se touchent, autres doigts etendus.",
    '9': "Pouce et index se touchent en cercle, autres doigts etendus.",
}

for letter, desc in ALPHA.items():
    obj, created = SignDictionary.objects.update_or_create(
        mot=letter,
        defaults={'categorie':'ALPHABET','description':desc,'difficulte':'FACILE','est_valide':True}
    )
    status = "Cree" if created else "MaJ"
    print(status + ": " + letter)

for num, desc in NUMS.items():
    obj, created = SignDictionary.objects.update_or_create(
        mot=num,
        defaults={'categorie':'CHIFFRE','description':desc,'difficulte':'FACILE','est_valide':True}
    )
    status = "Cree" if created else "MaJ"
    print(status + ": " + num)

print("Total: " + str(SignDictionary.objects.count()) + " signes")
