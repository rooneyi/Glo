"""Création et vérification des alertes métier."""
from datetime import timedelta

from django.utils import timezone

from accounts.models import Utilisateur
from contrats.models import ContratMouture
from laboratoire.models import Echantillon

from .models import Alerte


def creer_alerte(
    type_alerte: str,
    message: str,
    destinataire: Utilisateur,
    *,
    cle_dedup: str = '',
) -> Alerte | None:
    """Crée une alerte si aucune alerte non lue identique n'existe déjà."""
    qs = Alerte.objects.filter(
        type=type_alerte,
        destinataire=destinataire,
        lu=False,
    )
    fragment = cle_dedup or message[:120]
    if qs.filter(message__contains=fragment).exists():
        return None
    return Alerte.objects.create(
        type=type_alerte,
        message=message,
        destinataire=destinataire,
    )


def notifier_roles(type_alerte: str, message: str, roles: tuple[str, ...], *, cle_dedup: str = ''):
    """Envoie la même alerte à tous les utilisateurs actifs d'un ou plusieurs rôles."""
    for user in Utilisateur.objects.filter(role__in=roles, actif=True):
        creer_alerte(type_alerte, message, user, cle_dedup=cle_dedup)


def verifier_alertes_retard():
    """Contrats, analyses et moutures en retard — alertes RETARD."""
    today = timezone.now().date()

    contrats = ContratMouture.objects.filter(
        statut='EN_COURS',
        date_contrat__lt=today - timedelta(days=30),
    ).select_related('client')
    for contrat in contrats:
        msg = (
            f"Retard — contrat {contrat.numero_contrat} ({contrat.client}) "
            f"en cours depuis plus de 30 jours."
        )
        notifier_roles('RETARD', msg, ('COMPTABLE', 'MEUNIER', 'ADMIN'), cle_dedup=contrat.numero_contrat)

    echantillons = Echantillon.objects.filter(
        statut__in=('EN_ATTENTE', 'EN_COURS'),
        date_envoi_labo__lt=today - timedelta(days=7),
    ).select_related('reception__contrat__client')
    for ech in echantillons:
        client = ech.reception.contrat.client
        msg = (
            f"Retard labo — échantillon {ech.numero_echantillon} ({client}) "
            f"en attente de résultat depuis plus de 7 jours."
        )
        notifier_roles(
            'RETARD', msg, ('LABORANTIN', 'MEUNIER', 'ADMIN'),
            cle_dedup=ech.numero_echantillon,
        )

    from production.models import Production
    productions = Production.objects.filter(
        statut='EN_COURS',
        date_debut__lt=today - timedelta(days=14),
    ).select_related('contrat__client')
    for prod in productions:
        msg = (
            f"Retard mouture — {prod.numero_production} ({prod.contrat.client}) "
            f"en cours depuis plus de 14 jours."
        )
        notifier_roles(
            'RETARD', msg, ('MEUNIER', 'COMPTABLE', 'ADMIN'),
            cle_dedup=prod.numero_production,
        )
