# Plan de développement Django — Système MNL
## Minoterie de Lubumbashi (Gécamines)

> Voir aussi : [ARCHITECTURE_MNL.md](ARCHITECTURE_MNL.md) — structure du code, modèle de données et justifications des technologies.

---

## Stack technique

| Composant       | Technologie                       |
|-----------------|-----------------------------------|
| Backend         | Django 5.1 (Python)               |
| Base de données | SQLite (dev) → PostgreSQL (prod)  |
| Frontend        | Bootstrap 5 + Django Templates    |
| Formulaires     | django-crispy-forms               |
| PDF (bons)      | WeasyPrint                        |
| Statistiques    | Chart.js (CDN)                    |
| Export Excel    | openpyxl                          |
| Auth            | Django Auth (AbstractUser)        |

---

## Structure du projet

> Détail complet, justifications et conventions : [ARCHITECTURE_MNL.md](ARCHITECTURE_MNL.md)

```
mnl_project/
├── mnl/                  ← settings, urls principal
├── accounts/             ← Utilisateur (custom AbstractUser)
├── clients/              ← Client
├── contrats/             ← ContratMouture
├── magasin/              ← Reception, StockMP
├── laboratoire/          ← Echantillon, ResultatLaboratoire
├── production/           ← Production, ProduitFini, StockFarine
├── facturation/          ← BonRetrait, Alerte
├── core/                 ← Dashboard, statistiques
└── templates/            ← templates HTML communs
```

---

## PHASE 1 — Mise en place (2 jours)

### Objectif : projet fonctionnel, BD créée, admin accessible

```bash
# Installation
pip install -r requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer le superuser (Administrateur)
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Livrables
- [x] Projet Django initialisé
- [x] 8 apps créées
- [x] 11 modèles définis
- [x] Migrations appliquées
- [x] Admin Django configuré pour chaque modèle
- [ ] Superuser créé (à faire manuellement : `python manage.py createsuperuser`)

---

## PHASE 2 — Authentification & Utilisateurs (3 jours)

### Acteur : Administrateur

### Fonctionnalités
- Page de connexion (`/accounts/login/`)
- Page de déconnexion
- Dashboard dynamique selon le rôle connecté
- CRUD utilisateurs (Admin seulement)

### Fichiers à créer
```
accounts/
├── views.py     ← login, logout, liste, créer, modifier, désactiver
├── forms.py     ← UtilisateurForm, LoginForm
├── urls.py      ← /accounts/login/, /accounts/users/
└── templates/accounts/
    ├── login.html
    ├── liste_utilisateurs.html
    └── form_utilisateur.html
```

### Vues clés
```python
# accounts/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView

class ConnexionView(LoginView):
    template_name = 'accounts/login.html'

class ListeUtilisateursView(LoginRequiredMixin, ListView):
    model = Utilisateur
    template_name = 'accounts/liste_utilisateurs.html'
    # Accessible Admin seulement → vérifier role dans dispatch()
```

---

## PHASE 3 — Clients & Contrats de mouture (3 jours)

### Acteur : Comptable

### Fonctionnalités
- Enregistrer un client
- Créer un contrat de mouture (numéro auto : CM-YYYYMMDD-XXXX)
- Liste et recherche des contrats
- Modifier / annuler un contrat

### Fichiers
```
clients/
├── views.py   ← CRUD clients
├── forms.py   ← ClientForm
└── templates/clients/

contrats/
├── views.py   ← CRUD contrats
├── forms.py   ← ContratMoutureForm
└── templates/contrats/
```

---

## PHASE 4 — Réception & Stock MP (3 jours)

### Acteur : Magasinier

### Fonctionnalités
- Enregistrer une réception (poids brut/net, observations)
- Numéro bon auto : BRC-YYYYMMDD-XXXX
- Générer le bon de réception PDF (WeasyPrint)
- Afficher le stock disponible (kg)
- Marquer l'envoi de l'échantillon au labo Likasi

### PDF bon de réception
```python
# magasin/views.py
from weasyprint import HTML
from django.template.loader import render_to_string

def imprimer_bon_reception(request, pk):
    reception = Reception.objects.get(pk=pk)
    html_str = render_to_string('magasin/bon_reception_pdf.html',
                                {'reception': reception})
    pdf = HTML(string=html_str).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="BRC-{reception.numero_bon}.pdf"'
    return response
```

---

## PHASE 5 — Module Laboratoire (3 jours)

### Acteur : Laborantin + Meunier

### Fonctionnalités
- Laborantin encode le résultat (taux humidité, acidité, matière grasse)
- Système marque automatiquement conforme / non conforme
- Alerte automatique envoyée au Meunier (modèle Alerte)
- Meunier consulte le résultat et autorise ou refuse la mouture

### Règles métier
```python
# Seuils de conformité (à adapter selon normes MNL)
SEUIL_HUMIDITE_MAX    = 14.0   # %
SEUIL_ACIDITE_MAX     = 0.05
SEUIL_MAT_GRASSE_MAX  = 5.0    # %

def est_conforme(resultat):
    return (
        resultat.taux_humidite    <= SEUIL_HUMIDITE_MAX and
        resultat.taux_acidite     <= SEUIL_ACIDITE_MAX  and
        resultat.taux_matiere_grasse <= SEUIL_MAT_GRASSE_MAX
    )
```

---

## PHASE 6 — Production / Mouture (3 jours)

### Acteur : Meunier

### Fonctionnalités
- Lancer la mouture (après résultat conforme)
- Suivi des sous-étapes : avant-nettoyage → nettoyage → mouture → ensachage
- Enregistrer les sacs produits (25 kg ou 50 kg)
- Calcul automatique du rendement : `farine_kg / traitée_kg × 100`
- Entrée automatique en stock farine

### Numéro auto : PROD-YYYYMMDD-XXXX, LOT-YYYYMMDD-PROD

---

## PHASE 7 — Facturation & Bon de retrait (2 jours)

### Acteur : Comptable + Client

### Fonctionnalités
- Générer un bon de retrait après validation paiement
- Numéro auto : BRT-YYYYMMDD-XXXX
- Imprimer le bon PDF
- Client consulte l'historique de ses retraits (lecture seule)
- Mise à jour stock farine après retrait

---

## PHASE 8 — Dashboard & Statistiques (3 jours)

### Acteur : Administrateur

### KPIs affichés
| Indicateur                     | Calcul                                |
|--------------------------------|---------------------------------------|
| Total maïs reçu (mois)         | SUM(Reception.poids_net_kg)           |
| Total farine produite (mois)   | SUM(Production.quantite_farine_kg)    |
| Stock MP actuel                | SUM(StockMP.quantite_disponible_kg)   |
| Stock farine actuel            | SUM(StockFarine.quantite_sacs)        |
| Taux de rendement moyen        | Moyenne(Production.rendement_pct)     |
| Contrats en cours              | COUNT(ContratMouture, statut=EN_COURS)|
| Alertes non lues               | COUNT(Alerte, lu=False)               |

### Graphiques (Chart.js)
- Courbe : farine produite par mois (12 derniers mois)
- Barres : réceptions vs productions par semaine
- Jauge : taux de rendement

---

## PHASE 9 — Alertes & Finitions (2 jours)

### Fonctionnalités
- Badge d'alertes dans la navbar (non lus)
- Marquer alerte comme lue
- Interface responsive (Bootstrap 5, mobile-friendly)
- Messages flash (succès / erreur) sur chaque action
- Tests manuels de tous les flux

---

## PHASE 10 — Déploiement (2 jours)

```bash
# Passer à PostgreSQL
pip install psycopg2-binary

# Variables d'environnement (.env)
SECRET_KEY=...
DEBUG=False
DATABASE_URL=postgres://user:pass@host/db_mnl

# Fichiers statiques
python manage.py collectstatic

# Serveur : Gunicorn + Nginx (ou PythonAnywhere / Railway)
pip install gunicorn
gunicorn mnl.wsgi:application
```

---

## Calendrier estimé

| Phase                            | Durée     | Priorité  |
|----------------------------------|-----------|-----------|
| 1. Setup                         | 2 jours   | ★★★       |
| 2. Auth & Utilisateurs           | 3 jours   | ★★★       |
| 3. Clients & Contrats            | 3 jours   | ★★★       |
| 4. Réception & Stock MP          | 3 jours   | ★★★       |
| 5. Laboratoire                   | 3 jours   | ★★★       |
| 6. Production / Mouture          | 3 jours   | ★★★       |
| 7. Facturation & Bon de retrait  | 2 jours   | ★★★       |
| 8. Dashboard & Statistiques      | 3 jours   | ★★        |
| 9. Alertes & Finitions           | 2 jours   | ★★        |
| 10. Déploiement                  | 2 jours   | ★         |
| **TOTAL**                        | **26 jours** |          |

---

## Commandes de démarrage rapide

```bash
cd mnl_project

# 1. Environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 2. Dépendances
pip install -r requirements.txt

# 3. Migrations
python manage.py makemigrations accounts clients contrats magasin laboratoire production facturation
python manage.py migrate

# 4. Admin
python manage.py createsuperuser

# 5. Lancer
python manage.py runserver
# → http://127.0.0.1:8000/admin/
# → http://127.0.0.1:8000/accounts/login/
```
