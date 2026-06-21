# Architecture & structure du code — Système MNL
## Minoterie de Lubumbashi (Gécamines)

Ce document décrit l'organisation du code, le modèle de données et les **justifications** de chaque technologie retenue. Il complète le [plan de développement](ROADMAP_DJANGO.md) et les [diagrammes UML](diagrammes/).

---

## 1. Contexte métier

Le système MNL digitalise le cycle complet de la mouture de maïs :

```
Client → Contrat → Réception → Stock MP → Échantillon → Résultat labo
                                                      ↓
Client ← Bon de retrait ← Production ← (si conforme)
                              ↓
                         Produit fini → Stock farine
```

**Acteurs** (rôles utilisateur) :

| Rôle | Responsabilités |
|------|-----------------|
| **Administrateur** | Gestion des utilisateurs, tableau de bord global |
| **Comptable** | Clients, contrats de mouture, bons de retrait |
| **Magasinier** | Réception du maïs, stock matière première |
| **Laborantin** | Analyse qualité (labo Likasi) |
| **Meunier** | Envoi échantillon, production, ensachage |

---

## 2. Structure du projet

```
MNL/
├── ARCHITECTURE_MNL.md          ← ce document
├── ROADMAP_DJANGO.md            ← plan de développement par phases
├── generate_diagrammes_uml.py   ← générateur des diagrammes UML
├── diagrammes/                  ← diagrammes UML (fichiers séparés)
│   ├── diagramme_classes_MNL.drawio
│   ├── diagramme_cas_utilisation_MNL.drawio
│   ├── diagramme_sequence_mouture_MNL.drawio
│   └── diagramme_activite_mouture_MNL.drawio
│
└── mnl_project/                 ← projet Django
    ├── manage.py
    ├── requirements.txt
    ├── db_mnl.sqlite3           ← base de données (développement)
    │
    ├── mnl/                     ← configuration centrale
    │   ├── settings.py          ← apps, BDD, auth, langue FR
    │   └── urls.py              ← routage principal
    │
    ├── accounts/                ← Utilisateur (auth)
    ├── clients/                 ← Client
    ├── contrats/                ← ContratMouture
    ├── magasin/                 ← Reception, StockMP
    ├── laboratoire/             ← Echantillon, ResultatLaboratoire
    ├── production/              ← Production, ProduitFini, StockFarine
    ├── facturation/             ← BonRetrait, Alerte
    ├── core/                    ← Dashboard, statistiques
    │
    ├── templates/               ← templates HTML (par app)
    └── static/                  ← CSS, JS, images
```

### Principe d'organisation : une app Django par domaine métier

Chaque application Django regroupe **un périmètre fonctionnel** cohérent. Cela permet :

- une séparation claire des responsabilités ;
- des migrations indépendantes par module ;
- une maintenance facilitée (un développeur peut travailler sur `magasin/` sans toucher `production/`) ;
- un découpage naturel des permissions par rôle.

### Fichiers standard dans chaque app

| Fichier | Rôle |
|---------|------|
| `models.py` | Entités métier et relations (ORM Django) |
| `admin.py` | Interface d'administration Django |
| `views.py` | Logique des pages (vues fonction-based ou class-based) |
| `forms.py` | Formulaires de saisie (liés à crispy-forms) |
| `urls.py` | Routes URL de l'app |
| `migrations/` | Historique des changements de schéma BDD |

Les templates sont centralisés dans `templates/<nom_app>/` (convention Django `DIRS`).

---

## 3. Modèle de données — correspondance apps / classes

| Classe (diagramme UML) | App Django | Fichier | Relations clés |
|------------------------|------------|---------|----------------|
| `Utilisateur` | `accounts` | `models.py` | Rôle ENUM, hérite `AbstractUser` |
| `Client` | `clients` | `models.py` | FK → Utilisateur (enregistre_par) |
| `Commande` | `contrats` | `models.py` | FK → Client, Utilisateur (comptable) |
| `ContratMouture` | `contrats` | `models.py` | FK → Client, OneToOne → Commande, Utilisateur (comptable) |
| `Reception` | `magasin` | `models.py` | OneToOne → ContratMouture |
| `StockMP` | `magasin` | `models.py` | FK → Reception |
| `Echantillon` | `laboratoire` | `models.py` | OneToOne → Reception |
| `ResultatLaboratoire` | `laboratoire` | `models.py` | OneToOne → Echantillon |
| `Production` | `production` | `models.py` | OneToOne → ContratMouture |
| `ProduitFini` | `production` | `models.py` | FK → Production |
| `StockFarine` | `production` | `models.py` | FK → ProduitFini |
| `BonRetrait` | `facturation` | `models.py` | OneToOne → ContratMouture |
| `Alerte` | `facturation` | `models.py` | FK → Utilisateur (destinataire) |

### Corrections apportées au diagramme manuscrit initial

Ces choix sont documentés dans le diagramme draw.io :

- **Utilisateur unifié** avec attribut `role` (ENUM) au lieu de classes séparées par acteur ;
- **Echantillon** et **ResultatLaboratoire** ajoutés pour le flux labo Likasi ;
- **ContratMouture** distinct de **Commande** : la commande est la demande client ; le contrat est créé après validation comptable ;
- **Bon de réception** (`Reception`) séparé du **bon de retrait** (`BonRetrait`) ;
- **StockMP** et **StockFarine** distincts (matière première vs produit fini) ;
- **Production** (mouture) clairement définie avec rendement calculé.

### Numérotation automatique

| Entité | Préfixe | Exemple |
|--------|---------|---------|
| Commande | `CMD-` | `CMD-20250616-0001` |
| Contrat de mouture | `CM-` | `CM-20250616-0001` |
| Bon de réception | `BRC-` | `BRC-20250616-0001` |
| Échantillon | `ECH-` | `ECH-20250616-0001` |
| Production | `PROD-` | `PROD-20250616-0001` |
| Lot farine | `LOT-` | `LOT-20250616-PROD-20250616-0001` |
| Bon de retrait | `BRT-` | `BRT-20250616-0001` |

Le préfixe est **inclus dans le champ** `numero_*` ; les méthodes `__str__` n'ajoutent pas de préfixe supplémentaire.

---

## 4. Stack technique et justifications

### Vue d'ensemble

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Django (Python) | 5.1 |
| Base de données | SQLite (dev) → PostgreSQL (prod) | — |
| Frontend | Bootstrap 5 + Django Templates | 5.x |
| Formulaires | django-crispy-forms + crispy-bootstrap5 | 2.3 |
| PDF (bons) | WeasyPrint | 62.3 |
| Statistiques | Chart.js (CDN) | — |
| Export Excel | openpyxl | 3.1.5 |
| Auth | Django Auth (AbstractUser personnalisé) | intégré |
| Utilitaires UI | django-widget-tweaks | 1.5.0 |
| Images | Pillow | 10.4.0 |

---

### Django 5.1 (Python) — Backend

**Pourquoi Django ?**

- Framework **batteries included** : ORM, authentification, admin, migrations, formulaires — tout est intégré, ce qui accélère le développement d'une application métier interne.
- **ORM puissant** : les 11 classes du diagramme se traduisent directement en modèles Python avec relations (FK, OneToOne) sans écrire de SQL.
- **Sécurité native** : protection CSRF, hachage des mots de passe, validation des entrées.
- **Admin Django** : interface de gestion immédiate pour tester et administrer les données pendant le développement.
- **Écosystème mature** : documentation exhaustive, communauté large, compatible déploiement Linux (serveur Gécamines).

**Pourquoi pas Flask / FastAPI ?** Ces frameworks sont plus légers mais nécessitent d'assembler manuellement l'auth, l'ORM, l'admin — inutile pour une application CRUD métier complète.

**Pourquoi pas un ERP (Odoo, SAP) ?** Trop lourd et coûteux pour les besoins spécifiques de la minoterie ; Django permet une solution sur mesure.

---

### SQLite → PostgreSQL — Base de données

**SQLite en développement :**

- Zéro configuration : un fichier `db_mnl.sqlite3`, pas de serveur à installer.
- Idéal pour le développement local et les démonstrations.

**PostgreSQL en production :**

- Fiabilité et performances pour un usage multi-utilisateurs simultanés en usine.
- Transactions ACID, sauvegardes, réplication — standards industriels.
- Django bascule en changeant uniquement `DATABASES` dans `settings.py`.

---

### Bootstrap 5 + Django Templates — Frontend

**Pourquoi pas React / Vue / Angular ?**

- L'application est un **outil interne** (pas un site public à fort trafic) : pas besoin d'une SPA complexe.
- Django Templates permet de générer le HTML côté serveur, ce qui simplifie l'auth et les permissions par rôle.
- Bootstrap 5 offre un design responsive (mobile, tablette) sans écrire de CSS custom.
- Courbe d'apprentissage faible pour l'équipe de maintenance.

**Chart.js (CDN)** pour les graphiques du dashboard : léger, pas d'installation npm, suffisant pour courbes et barres de KPIs.

---

### django-crispy-forms + crispy-bootstrap5 — Formulaires

**Justification :**

- Rend les formulaires Django **esthétiques et cohérents** avec Bootstrap 5 en une ligne de configuration.
- Évite d'écrire manuellement les classes CSS `form-control`, `form-label`, etc. sur chaque champ.
- Support des layouts avancés (fieldsets, boutons, grilles) pour les formulaires complexes (contrat, réception).

**django-widget-tweaks** complète crispy-forms pour des ajustements ponctuels de classes CSS sur des champs individuels.

---

### WeasyPrint — Génération PDF

**Justification :**

- Génère des PDF à partir de **templates HTML/CSS** Django — le même langage que le reste du projet.
- Utilisé pour les **bons de réception** (`BRC-…`) et **bons de retrait** (`BRT-…`) imprimables.
- Alternative open-source à ReportLab (plus bas niveau) et wkhtmltopdf (binaire externe).

**Pillow** est une dépendance de WeasyPrint pour le traitement d'images dans les PDF (logo Gécamines, etc.).

---

### openpyxl — Export Excel

**Justification :**

- Permet d'exporter les listes (contrats, stocks, productions) en fichiers `.xlsx`.
- Format familier pour les comptables et la direction Gécamines.
- Pas de licence Microsoft requise (contrairement à COM Excel).

---

### Django Auth (AbstractUser) — Authentification

**Justification :**

- Le modèle `Utilisateur` étend `AbstractUser` avec les champs métier (`nom`, `prenom`, `role`, `telephone`).
- Connexion par **email** (pas de username) — plus naturel en entreprise.
- 5 rôles ENUM contrôlent l'accès aux modules (vérification dans les vues via `dispatch()` ou décorateurs).
- Pas besoin de JWT/OAuth pour une application interne au réseau Gécamines.

---

## 5. Routage URL

| Préfixe | App | Usage |
|---------|-----|-------|
| `/admin/` | Django Admin | Gestion données (dev / admin) |
| `/accounts/` | accounts | Connexion, déconnexion, CRUD utilisateurs |
| `/dashboard/` | core | Tableau de bord et statistiques |
| `/clients/` | clients | Gestion des clients |
| `/contrats/` | contrats | Contrats de mouture |
| `/magasin/` | magasin | Réceptions, stock MP, PDF |
| `/laboratoire/` | laboratoire | Échantillons, résultats d'analyse |
| `/production/` | production | Mouture, ensachage, stock farine |
| `/facturation/` | facturation | Bons de retrait, alertes |

---

## 6. Configuration clé (`mnl/settings.py`)

| Paramètre | Valeur | Raison |
|-----------|--------|--------|
| `AUTH_USER_MODEL` | `accounts.Utilisateur` | Modèle utilisateur personnalisé |
| `LANGUAGE_CODE` | `fr-fr` | Interface en français |
| `TIME_ZONE` | `Africa/Lubumbashi` | Fuseau horaire local |
| `LOGIN_URL` | `/accounts/login/` | Redirection si non connecté |
| `LOGIN_REDIRECT_URL` | `/dashboard/` | Page d'accueil après connexion |
| `CRISPY_TEMPLATE_PACK` | `bootstrap5` | Rendu formulaires Bootstrap 5 |

---

## 7. Conventions de code

- **Nommage** : français pour les modèles, champs et labels métier ; anglais pour le code technique Django (views, urls).
- **Relations** : `on_delete=models.PROTECT` pour les données métier (empêche la suppression accidentelle), `CASCADE` pour les dépendances logiques (stock lié à une réception).
- **Numéros auto** : générés dans `save()` si le champ est vide, format `PREFIX-YYYYMMDD-XXXX`.
- **Alertes** : créées automatiquement dans `ResultatLaboratoire.save()` pour notifier le meunier.
- **Rendement** : calculé en propriété `rendement_pct` sur `Production` (pas stocké en BDD).

---

## 8. État d'avancement

| Élément | Statut |
|---------|--------|
| 8 apps Django créées | ✅ |
| 11 modèles + migrations | ✅ |
| Admin configuré (tous modèles) | ✅ |
| Base SQLite opérationnelle | ✅ |
| Vues / templates métier | 🔲 Phase 2+ (voir ROADMAP) |
| PDF WeasyPrint | 🔲 Phase 4 |
| Dashboard Chart.js | 🔲 Phase 8 |

---

## 9. Diagrammes UML

Tous les diagrammes sont générés par `generate_diagrammes_uml.py` et stockés dans `diagrammes/`. Ouvrir avec [draw.io](https://app.diagrams.net/) ou l'extension VS Code Draw.io.

| Fichier | Type UML | Contenu |
|---------|----------|---------|
| [diagramme_classes_MNL.drawio](diagrammes/diagramme_classes_MNL.drawio) | Diagramme de classes | 12 classes, 3 énumérations, associations avec multiplicités |
| [diagramme_cas_utilisation_MNL.drawio](diagrammes/diagramme_cas_utilisation_MNL.drawio) | Cas d'utilisation | 6 acteurs, 16 cas d'utilisation, relations `<<include>>` / `<<extend>>` |
| [diagramme_sequence_mouture_MNL.drawio](diagrammes/diagramme_sequence_mouture_MNL.drawio) | Séquence | Flux complet contrat → retrait (13 messages) |
| [diagramme_activite_mouture_MNL.drawio](diagrammes/diagramme_activite_mouture_MNL.drawio) | Activité | Processus de mouture avec nœud de décision « conforme ? » |

### Conventions UML respectées

- **Classes** : 3 compartiments (nom | attributs `-` | opérations `+`), types avec retour explicite
- **Énumérations** : stéréotype `<<enumeration>>`
- **Associations** : multiplicités (`1`, `0..*`, `1..*`) et rôles nommés aux extrémités
- **Cas d'utilisation** : acteurs (icône stickman), ellipses, frontière système
- **Séquence** : lifelines, messages synchrones (flèche pleine) et retours (pointillés)
- **Activité** : nœuds initial/final, actions, décision (losange), gardes `[oui]` / `[non]`

Regénérer tous les diagrammes :

```bash
python3 generate_diagrammes_uml.py
```

---

## 10. Documents associés

| Fichier | Contenu |
|---------|---------|
| [ROADMAP_DJANGO.md](ROADMAP_DJANGO.md) | Plan de développement en 10 phases |
| [diagrammes/](diagrammes/) | Diagrammes UML (4 fichiers .drawio) |
| [requirements.txt](mnl_project/requirements.txt) | Dépendances Python pip |
