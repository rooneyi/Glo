"""Création du compte utilisateur client et envoi des identifiants."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from accounts.models import Utilisateur

logger = logging.getLogger(__name__)


class CompteClientError(Exception):
    pass


def client_a_un_compte(client) -> bool:
    return Utilisateur.objects.filter(profil_client=client, role='CLIENT').exists()


def email_deja_utilise(email: str, *, exclure_utilisateur_id: int | None = None) -> bool:
    qs = Utilisateur.objects.filter(email__iexact=email.strip())
    if exclure_utilisateur_id:
        qs = qs.exclude(pk=exclure_utilisateur_id)
    return qs.exists()


def creer_compte_client(client) -> tuple[Utilisateur, str]:
    """Crée un utilisateur rôle CLIENT lié à la fiche client. Retourne (user, mot_de_passe)."""
    if client_a_un_compte(client):
        raise CompteClientError("Ce client possède déjà un compte.")

    email = (client.email or '').strip()
    if not email:
        raise CompteClientError("L'e-mail du client est obligatoire pour créer un compte.")

    if email_deja_utilise(email):
        raise CompteClientError("Cet e-mail est déjà utilisé par un autre compte.")

    mot_de_passe = get_random_string(12)
    utilisateur = Utilisateur.objects.create_user(
        email=email,
        password=mot_de_passe,
        nom=client.nom,
        prenom=client.prenom,
        telephone=client.telephone,
        role='CLIENT',
        profil_client=client,
    )
    return utilisateur, mot_de_passe


def synchroniser_compte_client(client) -> tuple[Utilisateur, str] | None:
    """Met à jour le compte lié, ou le crée s'il n'existe pas encore."""
    utilisateur = Utilisateur.objects.filter(profil_client=client, role='CLIENT').first()
    if utilisateur:
        email = (client.email or '').strip()
        if email and email_deja_utilise(email, exclure_utilisateur_id=utilisateur.pk):
            raise CompteClientError("Cet e-mail est déjà utilisé par un autre compte.")
        utilisateur.nom = client.nom
        utilisateur.prenom = client.prenom
        utilisateur.telephone = client.telephone
        if email:
            utilisateur.email = email
        utilisateur.save(update_fields=['nom', 'prenom', 'telephone', 'email'])
        return None

    if (client.email or '').strip():
        return creer_compte_client(client)
    return None


def envoyer_identifiants_client(client, mot_de_passe: str, login_url: str) -> bool:
    """Envoie les identifiants par e-mail. Retourne True si envoyé."""
    contexte = {
        'client': client,
        'email': client.email,
        'mot_de_passe': mot_de_passe,
        'login_url': login_url,
        'lieu': getattr(settings, 'MNL_RETRAIT_LIEU', 'Minoterie de Lubumbashi (MNL)'),
    }
    corps = render_to_string('clients/email_identifiants.txt', contexte)
    try:
        send_mail(
            subject='Votre accès espace client — MNL Gécamines',
            message=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Échec envoi e-mail identifiants client %s", client.pk)
        return False
