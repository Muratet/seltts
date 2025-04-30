import ctypes
import json
from pathlib import Path
from tkinter import *
import pyautogui # type: ignore
import keyboard # type: ignore
import pytesseract # type: ignore
import pyttsx3 # type: ignoreimport ctypes

# Définition des raccourcis
hotkey_français = 'Ctrl+Alt+Shift+f'
hotkey_anglais = 'Ctrl+Alt+Shift+a'
hotkey_epeler = 'Ctrl+Alt+Shift+e'
hotkey_quitter = 'Ctrl+Alt+Shift+q'
# Défintion des autres paramètres
mainOverlayTransparency = 0.1
sellFillColor = 'yellow'
sellOutlineColor = 'black'
sellOutlineWidth = 5

# Vérifier que l'application tesseract est installée sur l'ordianteur et accessible
try:
    test = pytesseract.get_languages()
except pytesseract.TesseractNotFoundError:
    print ("Tesseract is mandatory for seltts, please install tesseract in your computer and add it in your Path.\n See: https://github.com/tesseract-ocr/tesseract/releases")
    exit()

# tentative de trouver le fichier seltts.settings pour charger des raccourcis personnalisés
try:
    with open('seltts.settings') as f:
        d = json.load(f)
        if "fr" in d:
            hotkey_français = d["fr"]
        if "en" in d:
            hotkey_anglais = d["en"]
        if "spell" in d:
            hotkey_epeler = d["spell"]
        if "quit" in d:
            hotkey_quitter = d["quit"]
        if "mainOverlayTransparency" in d:
            mainOverlayTransparency = d["mainOverlayTransparency"]
        if "sellFillColor" in d:
            sellFillColor = d["sellFillColor"]
        if "sellOutlineColor" in d:
            sellOutlineColor = d["sellOutlineColor"]
        if "sellOutlineWidth" in d:
            sellOutlineWidth = d["sellOutlineWidth"]
        print ("seltts.settings found, use custom hotkeys:\n'"+hotkey_français+"' => Français\n'"+hotkey_anglais+"' => Anglais\n'"+hotkey_epeler+"' => Epeler\n'"+hotkey_quitter+"' => Quitter\n")
except IOError:
    print ("seltts.settings not found, use default hotkeys:\n'Ctrl+Alt+Shift+f' => Français\n'Ctrl+Alt+Shift+a' => Anglais\n'Ctrl+Alt+Shift+e' => Epeler\n'Ctrl+Alt+Shift+q' => Quitter\n")

# Charger Magnification.dll => pour la gestion de la loupe Windows
magnification = ctypes.WinDLL("Magnification")

# Définit comment prononcer les caractère spéciaux
pronunciation_map = {
        '!': "point d'exclamation",
        '?': "point d'interrogation",
        ',': "virgule",
        ';': "point-virgule",
        ':': "deux-points",
        '.': "point",
        '&': "esperluette",
        '~': "tilde",
        '"': "guillemet",
        '“': "guillemet",
        '#': "dièse",
        '\'': "apostrophe",
        '{': "accolade ouvrante",
        '(': "parenthèse ouvrante",
        '[': "crochet ouvrant",
        '-': "moins",
        '|': "pipe",
        '`': "accent grave",
        '_': "tiret bas",
        '\\': "antislash",
        '^': "accent circonflexe",
        '@': "arobase",
        '°': "degré",
        ')': "parenthèse fermante",
        ']': "crochet fermant",
        '=': "égal",
        '+': "plus",
        '}': "accolade fermante",
        '£': "livre sterling",
        '$': "dollar",
        '¤': "symbole monétaire générique",
        '%': "pourcent",
        '*': "étoile",
        '§': "paragraphe",
        '/': "slash",
        '€': "euro",
        '²': "carré",
        '<': "inférieur",
        '>': "supérieur"
    }

root = None

# Fonction pour capturer la sélection avec la souris
def capture_selection(lang):
    global root
    if root == None:
        print ("Start capturing ("+lang+")")
        # Création d'une fenêtre en superposition à toutes les autres pour récupérer les coordonnées des clics
        root = Tk()
        root.attributes("-alpha", mainOverlayTransparency) # léger voile gris pour voir à travers
        root.attributes("-topmost", True) # placer la fenêtre au primer plan, en supperposition de toutes les autres fenêtres
        root.overrideredirect(True) # Cacher la barre de titre et les bordure de la fenêtre
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0") # Redimentionnement de la fenêtre pour qu'elle couvre tout l'écran

        rect = None
        start_x = start_y = 0

        # Sur la pression du clic gauche, on initialise le carré de sélection
        def on_mouse_down(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y # Initialisation des coordonnées de départ à la position du pointeur de la souris
            # Création d'un carré de sélection à fond coloré avec bordure épaisse
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, fill=sellFillColor, outline=sellOutlineColor, width=sellOutlineWidth)
        
        # Sur le déplacement de la souris, on met à jour l'affichage du carré de sélection
        def on_move(event):
            nonlocal start_x, start_y, rect
            canvas.coords(rect, start_x, start_y, event.x, event.y)

        # Sur le relachement du clic gauche, on décode la zone sélectionnée pour la lire
        def on_mouse_up(event):
            global root
            # destruction de la fenêtre servant d'overlay (on n'en a plus besoin)
            root.destroy()
            root = None
            # Récupération des coordonnées finales
            end_x, end_y = event.x, event.y
            # On s'assure que x1/y1 sont bien les coordonnées en haut à gauche et x2/y2 les coordonnées en bas à droite
            x1, y1 = min(start_x, end_x), min(start_y, end_y)
            x2, y2 = max(start_x, end_x), max(start_y, end_y)
            # demander l'extraction du texte
            text = extract_text_from_region((x1, y1, x2-x1, y2-y1))
            # suppression de tous les caractères d'espacements inutiles
            text = text.strip()
            if text != "":
                # lancement de la synthèse vocale
                speak_text(text, lang)
            else:
                print("No text to read")

        canvas = Canvas(root, cursor="cross") # Création d'un canvas et modification de la forme du curseur de la souris
        canvas.pack(fill=BOTH, expand=True) # Etaler le Canvas sur toute la surface de l'écran
        # Lier les évènements souris aux fonctions
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        root.mainloop()

start_x = start_y = end_x = end_y = 0

# A partir d'une région (x, y, l, h) définie comme une position (x, y), une largeur  (l) et une hauteur (h), génère une capture d'image de cette zone pour en extraire le texte
# retourne le texte décodé
def extract_text_from_region(region):
    # Prise en compte de la loupe de Windows pour corriger les positions capturées
    # Initialiser la Magnification API
    if not magnification.MagInitialize():
        print("Échec de l'initialisation de Magnification API.")
        exit()
    # Déclaration des types de variables attendues
    magLevel = ctypes.c_float()
    xOffset = ctypes.c_int()
    yOffset = ctypes.c_int()
    # Appeler MagGetFullscreenTransform
    magnification.MagGetFullscreenTransform(
        ctypes.byref(magLevel), # Récupération du niveau de zoom (2 <=> 200%)
        ctypes.byref(xOffset), # Récupération du décalage horizontal
        ctypes.byref(yOffset) # Récupération du décalage vertical
    )
    # Nettoyer
    magnification.MagUninitialize()

    # Modification de la région à capturer en fonction des données du zoom
    region = (int((region[0]-xOffset.value)*magLevel.value), int((region[1]-yOffset.value)*magLevel.value), int(region[2]*magLevel.value), int(region[3]*magLevel.value))

    # Capturer la région sélectionnée (enregistrement de la capture dans le fichier screenshot.png => utile pour le débugage)
    screenshot = pyautogui.screenshot('screenshot.png', region=region)

    # Utiliser pytesseract pour extraire le texte, s'assurer que l'application est bien installée et que tesseract.exe est dans le PATH
    text = pytesseract.image_to_string(screenshot)
    return text

# lance la synthèse vocale en fonction de la lanque sélectionnée
def speak_text(text, lang):
    # Initialisation de la synthèse vocales
    engine = pyttsx3.init()
    # choix de la lanque en fonction du paramètre
    voices = engine.getProperty('voices')
    for voice in voices:
        if "_FR-FR" in voice.id and (lang == "fr" or lang == "spell"):
            engine.setProperty('voice', voice.id)
            break
        if "_EN-US" in voice.id and lang == "en":
            engine.setProperty('voice', voice.id)
            break
    # Pour épeler, l'astuce est de séparer tous les caractères par un espace
    if lang == "spell":
        newtext = ""
        for token in text:
            # La table de prononciation permet de dire à la synthèse vocal comment verbaliser ce symbole
            if token in pronunciation_map:
                newtext += pronunciation_map[token]+" "
            else:
                newtext += token+" "
        text = newtext
    
    # lancement de la synthèse vocale
    print("Texte décodé envoyé à la synthèse vocale :\n" + text)
    engine.say(text)
    engine.runAndWait()
    print ("lecture terminée!")

def main():
    # Création des raccourcis claviers
    keyboard.add_hotkey(hotkey_français, capture_selection, args=['fr'])
    keyboard.add_hotkey(hotkey_anglais, capture_selection, args=['en'])
    keyboard.add_hotkey(hotkey_epeler, capture_selection, args=['spell'])
    keyboard.wait(hotkey_quitter)
    print("Quit!")

# Exécuter le script principal
main()
