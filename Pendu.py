# -*- coding: utf-8 -*-
"""
Jeu du pendu - TD5 INF-TC2 .

Fichier unique regroupant les classes demandées :
  - FenPrincipale, ZoneAffichage, MonBoutonLettre

+ classes bonus / interface : GestionScores, FenTableauBord

Dépendances fournies avec le rendu : mots.txt, formes.py
"""

from tkinter import *
from tkinter import colorchooser, simpledialog, messagebox, ttk
from datetime import datetime
import os
from random import randint, choice

from formes import Rectangle, Ellipse


FICHIER_SCORES = 'scores_pendu.txt'
SEPARATEUR = '|'

_W_PSEUDO = 16
_W_MOT = 22
_W_SCORE = 8
_W_GAGNE = 7
_W_ERR = 10
_W_DATE = 19

_ENTETE_COMMENTEE = """# =============================================================================
# TABLE LOGIQUE : JEUX_PENDU_PARTIES  (fichier texte = persistance simple)
# =============================================================================
# Une ligne de données = une partie enregistrée (comme une ROW en SQL).
#
# Colonne      Type (idée SQL)     Description
# ---------    ---------------     -------------------------------------------
# pseudo       VARCHAR             Nom du joueur pour cette partie
# mot          VARCHAR             Mot secret tiré au hasard
# score        DECIMAL(0,1)        Taux de lettres découvertes (0.0 … 1.0 ; 1.0 = mot entier trouvé)
# gagne        BOOLEAN (0/1)       1 = victoire avant pendu complet, 0 = défaite
# nb_erreurs   INTEGER             Nombre de mauvaises lettres à la fin de la partie
# date         DATETIME            Horodatage d’enregistrement (YYYY-MM-DD HH:MM:SS)
# =============================================================================
"""

_LIGNE_COLONNES = (
    f"{'pseudo':<{_W_PSEUDO}} | "
    f"{'mot':<{_W_MOT}} | "
    f"{'score':>{_W_SCORE}} | "
    f"{'gagne':^{_W_GAGNE}} | "
    f"{'nb_erreurs':^{_W_ERR}} | "
    f"{'date':<{_W_DATE}}"
)
_LIGNE_SEP = (
    f"{'-' * _W_PSEUDO}-+-{'-' * _W_MOT}-+-{'-' * _W_SCORE}-+-"
    f"{'-' * _W_GAGNE}-+-{'-' * _W_ERR}-+-{'-' * _W_DATE}"
)


def _formater_ligne_donnee(L):
    g = '1' if L['gagne'] else '0'
    sc = f"{L['score']:.4f}".rstrip('0').rstrip('.') if L['score'] != 1.0 else '1.0'
    if sc == '':
        sc = '0'
    pseudo = (L['pseudo'] or '')[:_W_PSEUDO]
    mot = (L['mot'] or '')[:_W_MOT]
    return (
        f"{pseudo:<{_W_PSEUDO}} | "
        f"{mot:<{_W_MOT}} | "
        f"{sc:>{_W_SCORE}} | "
        f"{g:^{_W_GAGNE}} | "
        f"{L['nb_erreurs']:^{_W_ERR}} | "
        f"{L['date']:<{_W_DATE}}"
    )


def _score_partie(mot_secret, mot_affiche, gagne):
    n = len(mot_secret)
    if n == 0:
        return 0.0
    if gagne:
        return 1.0
    trouvees = sum(1 for i in range(n) if mot_affiche[i] != '*')
    return round(trouvees / n, 4)


class GestionScores:
    """Charge et enregistre les parties dans scores_pendu.txt."""

    def __init__(self, chemin=FICHIER_SCORES):
        self.__chemin = chemin
        self.__lignes = []
        self.charger()

    def __est_ligne_meta(self, ligne):
        s = ligne.strip()
        if not s:
            return True
        if s.startswith('#'):
            return True
        if s.replace('-', '').replace('+', '').strip() == '':
            return True
        if s.replace('|', '').strip() == '':
            return True
        parts = [p.strip() for p in s.split(SEPARATEUR)]
        if len(parts) >= 6 and parts[0].lower() == 'pseudo' and parts[1].lower() == 'mot':
            return True
        return False

    def __parser_ligne_donnee(self, ligne):
        parts = [p.strip() for p in ligne.split(SEPARATEUR)]
        if len(parts) < 6:
            return None
        try:
            return {
                'pseudo': parts[0],
                'mot': parts[1],
                'score': float(parts[2]),
                'gagne': parts[3] in ('1', '1.0', 'True', 'true'),
                'nb_erreurs': int(parts[4]),
                'date': parts[5],
            }
        except (ValueError, IndexError):
            return None

    def charger(self):
        self.__lignes = []
        if not os.path.isfile(self.__chemin):
            return
        with open(self.__chemin, 'r', encoding='utf-8') as f:
            for ligne in f:
                brut = ligne.rstrip('\n\r')
                if self.__est_ligne_meta(brut):
                    continue
                rec = self.__parser_ligne_donnee(brut)
                if rec is not None:
                    self.__lignes.append(rec)

    def __sauvegarder_fichier(self):
        lignes_out = [
            _ENTETE_COMMENTEE.rstrip() + '\n',
            _LIGNE_COLONNES + '\n',
            _LIGNE_SEP + '\n',
        ]
        for L in self.__lignes:
            lignes_out.append(_formater_ligne_donnee(L) + '\n')
        with open(self.__chemin, 'w', encoding='utf-8') as f:
            f.writelines(lignes_out)

    def reecrire_fichier_en_tableau(self):
        self.charger()
        self.__sauvegarder_fichier()

    def enregistrer_partie(self, pseudo, mot_secret, mot_affiche, gagne, nb_erreurs):
        pseudo = (pseudo or 'Invité').strip() or 'Invité'
        score = _score_partie(mot_secret, mot_affiche, gagne)
        date_iso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.__lignes.append({
            'pseudo': pseudo,
            'mot': mot_secret,
            'score': score,
            'gagne': gagne,
            'nb_erreurs': nb_erreurs,
            'date': date_iso,
        })
        try:
            self.__sauvegarder_fichier()
        except OSError:
            self.__lignes.pop()
            raise
        return score

    def historique_pseudo(self, pseudo):
        pseudo = (pseudo or '').strip().lower()
        return [L for L in self.__lignes if L['pseudo'].lower() == pseudo]

    def stats_pseudo(self, pseudo):
        h = self.historique_pseudo(pseudo)
        if not h:
            return {
                'parties': 0,
                'victoires': 0,
                'taux_reussite': 0.0,
                'score_moyen': 0.0,
                'meilleur_score': 0.0,
                'erreurs_moyennes': 0.0,
            }
        n = len(h)
        vic = sum(1 for x in h if x['gagne'])
        return {
            'parties': n,
            'victoires': vic,
            'taux_reussite': round(100.0 * vic / n, 1),
            'score_moyen': round(sum(x['score'] for x in h) / n, 4),
            'meilleur_score': max(x['score'] for x in h),
            'erreurs_moyennes': round(sum(x['nb_erreurs'] for x in h) / n, 2),
        }

    def classement_joueurs(self):
        from collections import defaultdict

        par_pseudo = defaultdict(list)
        for L in self.__lignes:
            par_pseudo[L['pseudo'].lower()].append(L)
        rows = []
        for _p_lower, parties in par_pseudo.items():
            pseudo_affiche = parties[-1]['pseudo']
            n = len(parties)
            vic = sum(1 for x in parties if x['gagne'])
            taux = 100.0 * vic / n if n else 0
            rows.append((pseudo_affiche, n, vic, round(taux, 1)))
        rows.sort(key=lambda r: (-r[3], -r[1], r[0].lower()))
        return rows

    def rang_pseudo(self, pseudo):
        rows = self.classement_joueurs()
        pl = (pseudo or '').strip().lower()
        for i, row in enumerate(rows, start=1):
            if row[0].lower() == pl:
                return i, len(rows)
        return None, len(rows)

    def resume_classement_top(self, n=3):
        rows = self.classement_joueurs()[:n]
        if not rows:
            return 'Pas encore de classement — jouez une partie !'
        parts = []
        for i, r in enumerate(rows, start=1):
            parts.append(f'{i}. {r[0]} — {r[3]} % victoires ({r[2]}/{r[1]})')
        return '  •  '.join(parts)

    def dernieres_parties_pseudo(self, pseudo, k=3):
        h = self.historique_pseudo(pseudo)
        h = list(reversed(h[-k:]))
        return h

    def toutes_lignes(self):
        return list(self.__lignes)



# Fenêtre tableau de bord (bonus)



class FenTableauBord(Toplevel):
    def __init__(self, parent, gestion_scores, pseudo_courant):
        Toplevel.__init__(self, parent)
        self.title('Tableau de bord — Jeu du pendu')
        self.geometry('820x520')
        self.minsize(640, 400)
        self.__gs = gestion_scores
        self.__pseudo = (pseudo_courant or 'Invité').strip() or 'Invité'

        self.configure(bg='#1a1a2e')
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Treeview', background='#16213e', foreground='#eaeaea', fieldbackground='#16213e', rowheight=26)
        style.configure('Treeview.Heading', background='#0f3460', foreground='#e94560', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#e94560')])

        main = Frame(self, bg='#1a1a2e', padx=14, pady=12)
        main.pack(fill=BOTH, expand=True)

        titre = Label(
            main,
            text='Statistiques & performances',
            font=('Segoe UI', 18, 'bold'),
            fg='#e94560',
            bg='#1a1a2e',
        )
        titre.pack(anchor=W, pady=(0, 8))

        self.__frame_resume = Frame(main, bg='#16213e', padx=12, pady=10)
        self.__frame_resume.pack(fill=X, pady=(0, 10))

        nb = ttk.Notebook(main)
        nb.pack(fill=BOTH, expand=True, pady=4)

        tab_hist = Frame(nb, bg='#1a1a2e')
        tab_classement = Frame(nb, bg='#1a1a2e')
        nb.add(tab_hist, text='  Mon historique  ')
        nb.add(tab_classement, text='  Classement joueurs  ')

        cols = ('date', 'mot', 'score', 'resultat', 'erreurs')
        self.__tree = ttk.Treeview(tab_hist, columns=cols, show='headings', height=14)
        self.__tree.heading('date', text='Date')
        self.__tree.heading('mot', text='Mot')
        self.__tree.heading('score', text='Score (taux lettres)')
        self.__tree.heading('resultat', text='Résultat')
        self.__tree.heading('erreurs', text='Erreurs')
        self.__tree.column('date', width=140)
        self.__tree.column('mot', width=120)
        self.__tree.column('score', width=110, anchor=CENTER)
        self.__tree.column('resultat', width=100, anchor=CENTER)
        self.__tree.column('erreurs', width=70, anchor=CENTER)
        sy = Scrollbar(tab_hist, orient=VERTICAL, command=self.__tree.yview)
        self.__tree.configure(yscrollcommand=sy.set)
        self.__tree.pack(side=LEFT, fill=BOTH, expand=True)
        sy.pack(side=RIGHT, fill=Y)

        cols2 = ('rang', 'pseudo', 'parties', 'victoires', 'taux')
        self.__tree2 = ttk.Treeview(tab_classement, columns=cols2, show='headings', height=14)
        for c, t, w in [
            ('rang', '#', 50),
            ('pseudo', 'Pseudo', 200),
            ('parties', 'Parties', 80),
            ('victoires', 'Victoires', 90),
            ('taux', 'Taux réussite %', 120),
        ]:
            self.__tree2.heading(c, text=t)
            self.__tree2.column(c, width=w, anchor=CENTER if c != 'pseudo' else W)
        sy2 = Scrollbar(tab_classement, orient=VERTICAL, command=self.__tree2.yview)
        self.__tree2.configure(yscrollcommand=sy2.set)
        self.__tree2.pack(side=LEFT, fill=BOTH, expand=True)
        sy2.pack(side=RIGHT, fill=Y)

        btn = Button(
            main,
            text='Actualiser',
            command=self.rafraichir,
            bg='#e94560',
            fg='white',
            activebackground='#ff6b6b',
            font=('Segoe UI', 10, 'bold'),
            relief=FLAT,
            padx=16,
            pady=6,
        )
        btn.pack(anchor=E, pady=(8, 0))

        self.rafraichir()
        self.transient(parent)

    def rafraichir(self):
        self.__gs.charger()
        stats = self.__gs.stats_pseudo(self.__pseudo)

        for w in self.__frame_resume.winfo_children():
            w.destroy()

        def ligne(txt, val, couleur='#eaeaea'):
            f = Frame(self.__frame_resume, bg='#16213e')
            f.pack(fill=X, pady=2)
            Label(f, text=txt, font=('Segoe UI', 11), fg='#a0a0a0', bg='#16213e', width=28, anchor=W).pack(side=LEFT)
            Label(f, text=str(val), font=('Segoe UI', 11, 'bold'), fg=couleur, bg='#16213e', anchor=W).pack(side=LEFT)

        Label(
            self.__frame_resume,
            text=f'Joueur : {self.__pseudo}',
            font=('Segoe UI', 13, 'bold'),
            fg='#e94560',
            bg='#16213e',
            anchor=W,
        ).pack(fill=X, pady=(0, 8))

        ligne('Parties jouées', stats['parties'])
        ligne('Victoires', stats['victoires'], '#4ecca3')
        ligne('Taux de réussite', f"{stats['taux_reussite']} %", '#4ecca3')
        ligne('Score moyen (lettres trouvées)', stats['score_moyen'])
        ligne('Meilleur score enregistré', stats['meilleur_score'])
        ligne('Erreurs moyennes / partie', stats['erreurs_moyennes'])

        for item in self.__tree.get_children():
            self.__tree.delete(item)
        for L in reversed(self.__gs.historique_pseudo(self.__pseudo)):
            self.__tree.insert(
                '',
                END,
                values=(
                    L['date'],
                    L['mot'],
                    f"{L['score']:.1%}",
                    'Gagné' if L['gagne'] else 'Perdu',
                    L['nb_erreurs'],
                ),
            )

        for item in self.__tree2.get_children():
            self.__tree2.delete(item)
        for i, row in enumerate(self.__gs.classement_joueurs(), start=1):
            pseudo, n, vic, taux = row
            self.__tree2.insert('', END, values=(i, pseudo, n, vic, taux))

# Zone d'affichage du pendu (canvas + pièces)

def _luminance_rgb(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def _hex_vers_rgb(couleur):
    couleur = (couleur or '#808080').strip().lstrip('#')
    if len(couleur) == 3:
        couleur = ''.join(ch * 2 for ch in couleur)
    if len(couleur) != 6:
        return 128, 128, 128
    return int(couleur[0:2], 16), int(couleur[2:4], 16), int(couleur[4:6], 16)


def couleurs_contrastees_pour_fond(hex_fond):
    r, g, b = _hex_vers_rgb(hex_fond)
    lum = _luminance_rgb(r, g, b)
    if lum > 135:
        return {
            'bois': '#4E342E',
            'corps': '#1B1B1B',
            'outline_bois': '#3E2723',
            'outline_corps': '#000000',
            'epaisseur': 2,
        }
    return {
        'bois': '#D7CCC8',
        'corps': '#F5F5F5',
        'outline_bois': '#5D4037',
        'outline_corps': '#212121',
        'epaisseur': 2,
    }

def _bbox_motif(specs):
    min_x = min_y = 10**9
    max_x = max_y = -10**9
    for sp in specs:
        if sp['kind'] == 'R':
            x, y, l, h = sp['x'], sp['y'], sp['l'], sp['h']
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + l)
            max_y = max(max_y, y + h)
        else:
            cx, cy, rx, ry = sp['cx'], sp['cy'], sp['rx'], sp['ry']
            min_x = min(min_x, cx - rx)
            min_y = min(min_y, cy - ry)
            max_x = max(max_x, cx + rx)
            max_y = max(max_y, cy + ry)
    return min_x, min_y, max_x, max_y


VARIANTES_PENDU = [
    (
        'Classique — tête ronde',
        [
            {'kind': 'R', 'x': 50, 'y': 270, 'l': 200, 'h': 26, 'bois': True},
            {'kind': 'R', 'x': 87, 'y': 83, 'l': 26, 'h': 200, 'bois': True},
            {'kind': 'R', 'x': 87, 'y': 70, 'l': 150, 'h': 26, 'bois': True},
            {'kind': 'R', 'x': 183, 'y': 67, 'l': 10, 'h': 40, 'bois': True},
            {'kind': 'E', 'cx': 198, 'cy': 130, 'rx': 14, 'ry': 14, 'bois': False},
            {'kind': 'R', 'x': 175, 'y': 147, 'l': 26, 'h': 56, 'bois': False},
            {'kind': 'R', 'x': 128, 'y': 152, 'l': 42, 'h': 10, 'bois': False},
            {'kind': 'R', 'x': 208, 'y': 152, 'l': 42, 'h': 10, 'bois': False},
            {'kind': 'R', 'x': 175, 'y': 205, 'l': 10, 'h': 40, 'bois': False},
            {'kind': 'R', 'x': 191, 'y': 205, 'l': 10, 'h': 40, 'bois': False},
        ],
    ),
    (
        'Potence haute — corde en ovale',
        [
            {'kind': 'R', 'x': 55, 'y': 278, 'l': 190, 'h': 22, 'bois': True},
            {'kind': 'R', 'x': 95, 'y': 55, 'l': 22, 'h': 230, 'bois': True},
            {'kind': 'R', 'x': 95, 'y': 42, 'l': 130, 'h': 22, 'bois': True},
            {'kind': 'E', 'cx': 188, 'cy': 95, 'rx': 6, 'ry': 28, 'bois': True},
            {'kind': 'E', 'cx': 188, 'cy': 138, 'rx': 16, 'ry': 16, 'bois': False},
            {'kind': 'R', 'x': 174, 'y': 156, 'l': 28, 'h': 50, 'bois': False},
            {'kind': 'R', 'x': 118, 'y': 162, 'l': 50, 'h': 11, 'bois': False},
            {'kind': 'R', 'x': 212, 'y': 162, 'l': 50, 'h': 11, 'bois': False},
            {'kind': 'R', 'x': 172, 'y': 208, 'l': 12, 'h': 38, 'bois': False},
            {'kind': 'R', 'x': 190, 'y': 208, 'l': 12, 'h': 38, 'bois': False},
        ],
    ),
    (
        'Compact — petit gibet',
        [
            {'kind': 'R', 'x': 85, 'y': 282, 'l': 140, 'h': 18, 'bois': True},
            {'kind': 'R', 'x': 118, 'y': 110, 'l': 18, 'h': 175, 'bois': True},
            {'kind': 'R', 'x': 118, 'y': 98, 'l': 95, 'h': 18, 'bois': True},
            {'kind': 'R', 'x': 178, 'y': 94, 'l': 6, 'h': 32, 'bois': True},
            {'kind': 'E', 'cx': 181, 'cy': 132, 'rx': 11, 'ry': 11, 'bois': False},
            {'kind': 'R', 'x': 170, 'y': 145, 'l': 22, 'h': 48, 'bois': False},
            {'kind': 'E', 'cx': 152, 'cy': 158, 'rx': 8, 'ry': 8, 'bois': False},
            {'kind': 'E', 'cx': 210, 'cy': 158, 'rx': 8, 'ry': 8, 'bois': False},
            {'kind': 'R', 'x': 170, 'y': 195, 'l': 8, 'h': 32, 'bois': False},
            {'kind': 'R', 'x': 182, 'y': 195, 'l': 8, 'h': 32, 'bois': False},
        ],
    ),
    (
        'Large — base longue, grosse tête',
        [
            {'kind': 'R', 'x': 25, 'y': 268, 'l': 250, 'h': 30, 'bois': True},
            {'kind': 'R', 'x': 88, 'y': 75, 'l': 30, 'h': 205, 'bois': True},
            {'kind': 'R', 'x': 88, 'y': 60, 'l': 170, 'h': 28, 'bois': True},
            {'kind': 'R', 'x': 208, 'y': 56, 'l': 12, 'h': 45, 'bois': True},
            {'kind': 'E', 'cx': 214, 'cy': 128, 'rx': 18, 'ry': 18, 'bois': False},
            {'kind': 'R', 'x': 198, 'y': 148, 'l': 32, 'h': 68, 'bois': False},
            {'kind': 'R', 'x': 108, 'y': 155, 'l': 60, 'h': 12, 'bois': False},
            {'kind': 'R', 'x': 258, 'y': 155, 'l': 60, 'h': 12, 'bois': False},
            {'kind': 'R', 'x': 198, 'y': 218, 'l': 12, 'h': 42, 'bois': False},
            {'kind': 'R', 'x': 218, 'y': 218, 'l': 12, 'h': 42, 'bois': False},
        ],
    ),
    (
        'Original — mains rondes + tête',
        [
            {'kind': 'R', 'x': 60, 'y': 274, 'l': 180, 'h': 24, 'bois': True},
            {'kind': 'R', 'x': 105, 'y': 88, 'l': 24, 'h': 195, 'bois': True},
            {'kind': 'R', 'x': 105, 'y': 74, 'l': 125, 'h': 24, 'bois': True},
            {'kind': 'R', 'x': 185, 'y': 70, 'l': 8, 'h': 38, 'bois': True},
            {'kind': 'E', 'cx': 189, 'cy': 126, 'rx': 13, 'ry': 13, 'bois': False},
            {'kind': 'R', 'x': 176, 'y': 141, 'l': 26, 'h': 54, 'bois': False},
            {'kind': 'E', 'cx': 158, 'cy': 156, 'rx': 10, 'ry': 10, 'bois': False},
            {'kind': 'E', 'cx': 220, 'cy': 156, 'rx': 10, 'ry': 10, 'bois': False},
            {'kind': 'R', 'x': 176, 'y': 198, 'l': 10, 'h': 36, 'bois': False},
            {'kind': 'R', 'x': 190, 'y': 198, 'l': 10, 'h': 36, 'bois': False},
        ],
    ),
]


class ZoneAffichage(Canvas):
    def __init__(self, parent, largeur, hauteur):
        Canvas.__init__(self, parent, width=largeur, height=hauteur, bg='#f0c0c0')
        self.__largeur = largeur
        self.__hauteur = hauteur
        self.__couleurFond = '#f0c0c0'
        self.__piecesPendu = []
        self.__metaPieces = []
        self.__nom_motif = ''

        self.regenerer_motif_pendu()

    def get_nom_motif_courant(self):
        return self.__nom_motif or '—'

    def __detruire_pieces(self):
        for piece in self.__piecesPendu:
            piece.effacer()
        self.__piecesPendu = []
        self.__metaPieces = []

    def __fabriquer_pieces_depuis_specs(self, specs, ox, oy, pal):
        ep = pal['epaisseur']
        for sp in specs:
            bois = sp['bois']
            fill = pal['bois'] if bois else pal['corps']
            outline = pal['outline_bois'] if bois else pal['outline_corps']
            if sp['kind'] == 'R':
                x = sp['x'] + ox
                y = sp['y'] + oy
                p = Rectangle(self, x, y, sp['l'], sp['h'], fill, outline=outline, width=ep)
            else:
                cx = sp['cx'] + ox
                cy = sp['cy'] + oy
                p = Ellipse(self, cx, cy, sp['rx'], sp['ry'], fill, outline=outline, width=ep)
            self.__piecesPendu.append(p)
            self.__metaPieces.append(bois)

    def __appliquer_couleurs_pieces(self, pal):
        for piece, bois in zip(self.__piecesPendu, self.__metaPieces):
            fill = pal['bois'] if bois else pal['corps']
            outline = pal['outline_bois'] if bois else pal['outline_corps']
            piece.definir_remplissage(fill)
            piece.definir_contour(outline, pal['epaisseur'])

    def regenerer_motif_pendu(self):
        self.__detruire_pieces()
        nom, specs = choice(VARIANTES_PENDU)
        self.__nom_motif = nom

        min_x, min_y, max_x, max_y = _bbox_motif(specs)
        cx_m = (min_x + max_x) / 2
        cy_m = (min_y + max_y) / 2
        ox = self.__largeur / 2 - cx_m
        oy = self.__hauteur / 2 - cy_m

        pal = couleurs_contrastees_pour_fond(self.__couleurFond)
        self.__fabriquer_pieces_depuis_specs(specs, ox, oy, pal)
        self.cacherPendu()

    def cacherPendu(self):
        for piece in self.__piecesPendu:
            piece.set_state('hidden')

    def montrerPiece(self, index):
        if 0 <= index < len(self.__piecesPendu):
            self.__piecesPendu[index].set_state('normal')

    def definirCouleurFond(self, couleur):
        self.__couleurFond = couleur
        self.config(bg=couleur)
        if self.__piecesPendu:
            pal = couleurs_contrastees_pour_fond(self.__couleurFond)
            self.__appliquer_couleurs_pieces(pal)


# ---------------------------------------------------------------------------
# Bouton lettre (callback vers FenPrincipale.traitement)
# ---------------------------------------------------------------------------


class MonBoutonLettre(Button):
    def __init__(self, parent, lettre, fenPrincipale):
        Button.__init__(self, parent, text=lettre, width=4, command=self.cliquer)
        self.__lettre = lettre
        self.__fenPrincipale = fenPrincipale

    def cliquer(self):
        self.__fenPrincipale.traitement(self.__lettre)



class FenPrincipale(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title('Jeu du pendu')
        self.geometry('720x620')
        self.minsize(620, 520)
        self.__couleurInterface = '#4472C4'
        self.config(bg=self.__couleurInterface)
        self.chargeMots()
        self.__gestionScores = GestionScores()
        self.__motSecret = None
        self.__pseudoJoueur = None
        self.__scoreDejaEnregistre = False
        self.__historique = []
        self.__lettresJouees = set()

        barre_menu = Menu(self)
        self.config(menu=barre_menu)

        menu_joueur = Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label='Joueur', menu=menu_joueur)
        menu_joueur.add_command(label='Mes statistiques...', command=self.__ouvrirMesStatistiques)
        menu_joueur.add_command(label='Tableau de bord & historique...', command=self.__ouvrirTableauBord)
        menu_joueur.add_command(label='Classement des joueurs...', command=self.__ouvrirClassementJoueurs)
        menu_joueur.add_command(label='Changer le pseudo...', command=self.__changerPseudo)

        menu_apparence = Menu(barre_menu, tearoff=0)
        barre_menu.add_cascade(label='Apparence', menu=menu_apparence)
        menu_apparence.add_command(label='Couleur de l\'interface...', command=self.__choisirCouleurInterface)
        menu_apparence.add_command(label='Couleur de la zone pendu...', command=self.__choisirCouleurZonePendu)

        self.__frameOutils = Frame(self, bg=self.__couleurInterface)
        self.__frameOutils.pack(side=TOP, fill=X, padx=5, pady=5)
        Button(self.__frameOutils, text='Nouvelle partie', command=self.nouvellePartie).pack(side=LEFT, padx=5)
        Button(self.__frameOutils, text='Annuler le dernier coup', command=self.annulerCoup).pack(side=LEFT, padx=5)
        Button(self.__frameOutils, text='Quitter', command=self.__quitterApplication).pack(side=RIGHT, padx=5)

        self.__frameJoueur = Frame(self, bg=self.__couleurInterface)
        self.__frameJoueur.pack(fill=X, padx=10, pady=(0, 4))
        self.__labelJoueur = Label(
            self.__frameJoueur,
            text='Joueur : — (Nouvelle partie pour choisir un pseudo)',
            font=('Arial', 10, 'italic'),
            bg=self.__couleurInterface,
        )
        self.__labelJoueur.pack(anchor=W)

        self.__frameCorps = Frame(self, bg=self.__couleurInterface)

        self.__zoneAffichage = ZoneAffichage(self.__frameCorps, 500, 300)
        self.__zoneAffichage.pack(side=TOP, padx=10, pady=(8, 4), expand=True)
        self.__labelVariantePendu = Label(
            self.__frameCorps,
            text='Motif pendu : ' + self.__zoneAffichage.get_nom_motif_courant(),
            font=('Arial', 9, 'italic'),
            bg=self.__couleurInterface,
            fg='#E8E8E8',
        )
        self.__labelVariantePendu.pack(anchor=CENTER, pady=(0, 2))

        self.__frameMot = Frame(self.__frameCorps, bg=self.__couleurInterface)
        self.__frameMot.pack(side=TOP, pady=(4, 8))
        self.__labelMot = Label(self.__frameMot, text='Mot : * * * * *', font=('Arial', 18), bg=self.__couleurInterface)
        self.__labelMot.pack()

        self.__frameCorps.pack(side=TOP, fill=BOTH, expand=True)

        self.__frameClavierOuter = Frame(self, bg=self.__couleurInterface)
        self.__frameClavierOuter.pack(side=BOTTOM, fill=X, pady=(4, 14))
        self.__frameClavier = Frame(self.__frameClavierOuter, bg=self.__couleurInterface)
        self.__frameClavier.pack(anchor=CENTER)
        self.__boutonsLettres = []

        for i in range(26):
            lettre = chr(ord('A') + i)
            bouton = MonBoutonLettre(self.__frameClavier, lettre, self)
            row = i // 7
            if row < 3:
                col = i % 7
            else:
                col = 1 + (i - 21)
            bouton.grid(row=row, column=col, padx=2, pady=2)
            self.__boutonsLettres.append(bouton)

        for bouton in self.__boutonsLettres:
            bouton.config(state=DISABLED)

        self.protocol('WM_DELETE_WINDOW', self.__quitterApplication)

    def __remplir_fenetre_stats(self, pseudo, titre_lbl, lp, lv, lt, lr, dern_lbl):
        self.__gestionScores.charger()
        if not pseudo:
            titre_lbl.config(text='Statistiques -choisissez un pseudo (Nouvelle partie)')
            lp.config(text='—')
            lv.config(text='—')
            lt.config(text='—')
            lr.config(text='—')
            dern_lbl.config(text='Aucune donnée tant que vous n’avez pas joué avec un pseudo.')
            return

        st = self.__gestionScores.stats_pseudo(pseudo)
        rang, n_joueurs = self.__gestionScores.rang_pseudo(pseudo)
        titre_lbl.config(text=f'Statistiques — {pseudo}')
        lp.config(text=str(st['parties']))
        lv.config(text=str(st['victoires']))
        lt.config(text=f"{st['taux_reussite']} %")
        if st['parties'] == 0 or rang is None:
            lr.config(text='—')
        else:
            lr.config(text=f'#{rang} / {n_joueurs}')

        dern = self.__gestionScores.dernieres_parties_pseudo(pseudo, 5)
        if not dern:
            dern_lbl.config(text='Première partie avec ce pseudo — bonne chance !')
        else:
            lignes = []
            for L in dern:
                res = 'Victoire' if L['gagne'] else 'Défaite'
                sym = '✓' if L['gagne'] else '✗'
                lignes.append(
                    f"{sym} {res} — « {L['mot']} » — score {L['score']:.0%} — {L['nb_erreurs']} erreur(s) — {L['date']}"
                )
            dern_lbl.config(text='\n'.join(lignes))

    def __ouvrirMesStatistiques(self):
        bg_card = '#0d2137'
        bg_cell = '#132f4c'
        fg_title = '#90cdf4'

        top = Toplevel(self)
        top.title('Mes statistiques')
        top.geometry('560x480')
        top.configure(bg='#1a1a2e')
        top.transient(self)

        outer = Frame(top, bg='#1a1a2e', padx=16, pady=12)
        outer.pack(fill=BOTH, expand=True)

        card = Frame(outer, bg=bg_card, highlightbackground='#4299e1', highlightthickness=1)
        card.pack(fill=BOTH, expand=True)

        titre_lbl = Label(
            card, text='', font=('Segoe UI', 11, 'bold'), fg=fg_title, bg=bg_card, anchor=W,
        )
        titre_lbl.pack(fill=X, padx=14, pady=(12, 6))

        grille = Frame(card, bg=bg_card)
        grille.pack(fill=X, padx=10, pady=4)

        def cellule(col, titre):
            f = Frame(grille, bg=bg_cell, padx=10, pady=8)
            f.grid(row=0, column=col, padx=4, pady=2, sticky=NSEW)
            grille.grid_columnconfigure(col, weight=1)
            Label(f, text=titre, font=('Segoe UI', 8), fg='#a0aec0', bg=bg_cell).pack(anchor=W)
            lbl = Label(f, text='—', font=('Segoe UI', 13, 'bold'), fg='#f7fafc', bg=bg_cell)
            lbl.pack(anchor=W)
            return lbl

        lp = cellule(0, 'Parties')
        lv = cellule(1, 'Victoires')
        lt = cellule(2, 'Taux réussite')
        lr = cellule(3, 'Votre rang')

        Label(
            card, text='Dernières parties', font=('Segoe UI', 9, 'bold'),
            fg=fg_title, bg=bg_card, anchor=W,
        ).pack(fill=X, padx=14, pady=(10, 4))
        dern_lbl = Label(
            card, text='', font=('Segoe UI', 9), fg='#a0aec0', bg=bg_card,
            anchor=W, justify=LEFT, wraplength=500,
        )
        dern_lbl.pack(fill=BOTH, expand=True, padx=14, pady=(0, 12))

        self.__remplir_fenetre_stats(
            self.__pseudoJoueur, titre_lbl, lp, lv, lt, lr, dern_lbl,
        )

        Button(outer, text='Fermer', command=top.destroy, padx=24, pady=6).pack(pady=(10, 0))

    def __quitterApplication(self):
        if messagebox.askyesno(
            'Quitter',
            'Souhaitez-vous ouvrir le tableau de détail (historique complet + classement) avant de fermer ?\n\n'
            '• Oui : fenêtre des statistiques, puis fermeture.\n'
            '• Non : fermeture immédiate.',
            parent=self,
        ):
            self.__gestionScores.charger()
            tb = FenTableauBord(self, self.__gestionScores, self.__pseudoJoueur or 'Invité')
            self.wait_window(tb)
        self.destroy()

    def chargeMots(self):
        f = open('mots.txt', 'r')
        s = f.read()
        self.__mots = [m for m in s.split('\n') if m]
        f.close()

    def nouvellePartie(self):
        initial = self.__pseudoJoueur if self.__pseudoJoueur else 'Joueur'
        p = simpledialog.askstring(
            'Nouvelle partie',
            'Pseudo pour cette partie (scores enregistrés) :',
            initialvalue=initial,
            parent=self,
        )
        if p is None:
            return
        self.__pseudoJoueur = (p.strip() or 'Invité')
        self.__labelJoueur.config(text=f'Joueur : {self.__pseudoJoueur}')

        idx = randint(0, len(self.__mots) - 1)
        self.__motSecret = self.__mots[idx].upper()
        self.__motAffiche = ['*'] * len(self.__motSecret)
        self.__nbErreurs = 0
        self.__historique = []
        self.__lettresJouees = set()
        self.__scoreDejaEnregistre = False

        self.__labelMot.config(text='Mot : ' + ' '.join(self.__motAffiche))

        self.__synchroniserClavierLettres()

        self.__zoneAffichage.regenerer_motif_pendu()
        self.__labelVariantePendu.config(text='Motif pendu : ' + self.__zoneAffichage.get_nom_motif_courant())

    def traitement(self, lettre):
        if self.__motSecret is None:
            return
        if '*' not in self.__motAffiche or self.__nbErreurs >= 10:
            return

        self.__historique.append({
            'motAffiche': list(self.__motAffiche),
            'nbErreurs': self.__nbErreurs,
            'lettre': lettre,
        })

        if lettre in self.__motSecret:
            for i in range(len(self.__motSecret)):
                if self.__motSecret[i] == lettre:
                    self.__motAffiche[i] = lettre
        else:
            self.__nbErreurs += 1
            self.__zoneAffichage.montrerPiece(self.__nbErreurs - 1)

        self.__labelMot.config(text='Mot : ' + ' '.join(self.__motAffiche))
        self.__lettresJouees.add(lettre)

        if '*' not in self.__motAffiche:
            self.__bloquerClavier()
            self.__labelMot.config(text='Gagne ! Le mot etait : ' + self.__motSecret)
            self.__enregistrerFinPartie(True)
        elif self.__nbErreurs >= 10:
            self.__bloquerClavier()
            self.__labelMot.config(text='Perdu ! Le mot etait : ' + self.__motSecret)
            self.__enregistrerFinPartie(False)
        else:
            self.__synchroniserClavierLettres()

    def annulerCoup(self):
        if self.__motSecret is None or not self.__historique:
            return
        etat = self.__historique.pop()
        self.__motAffiche = etat['motAffiche']
        self.__nbErreurs = etat['nbErreurs']
        self.__lettresJouees.discard(etat['lettre'])

        self.__labelMot.config(text='Mot : ' + ' '.join(self.__motAffiche))

        self.__zoneAffichage.cacherPendu()
        for i in range(self.__nbErreurs):
            self.__zoneAffichage.montrerPiece(i)

        self.__synchroniserClavierLettres()

    def __synchroniserClavierLettres(self):
        for bouton in self.__boutonsLettres:
            L = bouton.cget('text')
            bouton.config(state=DISABLED if L in self.__lettresJouees else NORMAL)

    def __bloquerClavier(self):
        for bouton in self.__boutonsLettres:
            bouton.config(state=DISABLED)

    def __enregistrerFinPartie(self, gagne):
        if self.__scoreDejaEnregistre or self.__motSecret is None:
            return
        self.__scoreDejaEnregistre = True
        try:
            self.__gestionScores.enregistrer_partie(
                self.__pseudoJoueur or 'Invité',
                self.__motSecret,
                self.__motAffiche,
                gagne,
                self.__nbErreurs,
            )
        except OSError:
            pass

    def __ouvrirTableauBord(self):
        self.__gestionScores.charger()
        FenTableauBord(self, self.__gestionScores, self.__pseudoJoueur or 'Invité')

    def __ouvrirClassementJoueurs(self):
        self.__gestionScores.charger()
        rows = self.__gestionScores.classement_joueurs()
        top = Toplevel(self)
        top.title('Classement des joueurs')
        top.geometry('560x420')
        top.configure(bg='#1a1a2e')
        top.transient(self)

        Label(
            top,
            text='Classement (tous les pseudos — fichier scores)',
            font=('Segoe UI', 12, 'bold'),
            fg='#e94560',
            bg='#1a1a2e',
        ).pack(pady=(12, 8))

        cols = ('rang', 'pseudo', 'parties', 'victoires', 'taux')
        tree = ttk.Treeview(top, columns=cols, show='headings', height=14)
        tree.heading('rang', text='#')
        tree.heading('pseudo', text='Pseudo')
        tree.heading('parties', text='Parties')
        tree.heading('victoires', text='Victoires')
        tree.heading('taux', text='Taux %')
        tree.column('rang', width=40, anchor=CENTER)
        tree.column('pseudo', width=180, anchor=W)
        tree.column('parties', width=80, anchor=CENTER)
        tree.column('victoires', width=90, anchor=CENTER)
        tree.column('taux', width=90, anchor=CENTER)
        sy = Scrollbar(top, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sy.set)
        tree.pack(side=LEFT, fill=BOTH, expand=True, padx=(16, 0), pady=(0, 16))
        sy.pack(side=RIGHT, fill=Y, padx=(0, 16), pady=(0, 16))

        if not rows:
            tree.insert('', END, values=('—', 'Aucune partie enregistrée', '', '', ''))
        else:
            for i, r in enumerate(rows, start=1):
                tree.insert('', END, values=(i, r[0], r[1], r[2], r[3]))

        Button(top, text='Fermer', command=top.destroy, padx=20, pady=6).pack(pady=(0, 12))

    def __changerPseudo(self):
        initial = self.__pseudoJoueur if self.__pseudoJoueur else 'Joueur'
        p = simpledialog.askstring('Pseudo', 'Nouveau pseudo (affiché tout de suite) :', initialvalue=initial, parent=self)
        if p is not None:
            self.__pseudoJoueur = p.strip() or 'Invité'
            self.__labelJoueur.config(text=f'Joueur : {self.__pseudoJoueur}')

    def __choisirCouleurInterface(self):
        res = colorchooser.askcolor(title='Couleur de l\'interface', initialcolor=self.__couleurInterface)
        if res[1] is not None:
            self.__couleurInterface = res[1]
            self.config(bg=self.__couleurInterface)
            self.__frameOutils.config(bg=self.__couleurInterface)
            self.__frameJoueur.config(bg=self.__couleurInterface)
            self.__labelJoueur.config(bg=self.__couleurInterface)
            self.__frameMot.config(bg=self.__couleurInterface)
            self.__frameClavier.config(bg=self.__couleurInterface)
            self.__frameClavierOuter.config(bg=self.__couleurInterface)
            self.__labelVariantePendu.config(bg=self.__couleurInterface)
            self.__frameCorps.config(bg=self.__couleurInterface)
            self.__labelMot.config(bg=self.__couleurInterface)

    def __choisirCouleurZonePendu(self):
        res = colorchooser.askcolor(title='Couleur de la zone pendu')
        if res[1] is not None:
            self.__zoneAffichage.definirCouleurFond(res[1])


if __name__ == '__main__':
    fen = FenPrincipale()
    fen.mainloop()
