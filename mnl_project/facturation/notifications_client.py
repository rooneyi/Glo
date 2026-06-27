"""Notifications envoyées aux clients (magasinier → client)."""
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from contrats.models import ContratMouture

from .models import BonRetrait, NotificationClient


def _enregistrer_historique_lots(contrat: ContratMouture, description: str, auteur) -> None:
    """Trace une notification client dans l'historique de chaque lot du contrat."""
    from django.core.exceptions import ObjectDoesNotExist
    from production.models import HistoriqueLot

    try:
        produits = contrat.production.produits_finis.all()
    except ObjectDoesNotExist:
        return

    fragment = contrat.numero_contrat
    for produit in produits:
        if produit.historique.filter(
            type_evenement='NOTIFICATION',
            description__contains=fragment,
        ).exists():
            continue
        HistoriqueLot.objects.create(
            produit_fini=produit,
            type_evenement='NOTIFICATION',
            description=description,
            auteur=auteur,
        )


def _resume_sacs_contrat(contrat: ContratMouture) -> tuple[int, str]:
    """Retourne (total_sacs, détail lisible par type de sac)."""
    try:
        produits = contrat.production.produits_finis.all()
    except ObjectDoesNotExist:
        return 0, ''

    total = sum(p.nombre_sacs for p in produits)
    if not total:
        return 0, ''

    par_type: dict[str, int] = {}
    for p in produits:
        label = p.get_type_sac_display()
        par_type[label] = par_type.get(label, 0) + p.nombre_sacs

    detail = ', '.join(f"{q} × {label}" for label, q in par_type.items())
    return total, detail


def message_commande_prete_retrait(contrat: ContratMouture) -> str:
    """Texte envoyé au client pour l'inviter à passer retirer sa commande."""
    total_sacs, detail_sacs = _resume_sacs_contrat(contrat)
    lieu = getattr(settings, 'MNL_RETRAIT_LIEU', 'le magasin MNL')
    horaires = getattr(settings, 'MNL_RETRAIT_HORAIRES', 'aux heures d\'ouverture')
    contact = getattr(settings, 'MNL_RETRAIT_CONTACT', 'la comptabilité')

    if total_sacs:
        quantite = f"{total_sacs} sac(s)"
        if detail_sacs:
            quantite = f"{quantite} ({detail_sacs})"
    else:
        quantite = 'votre farine ensachée'

    try:
        bon = contrat.bon_retrait
        instruction_bon = (
            f"Munissez-vous de votre bon de retrait n° {bon.numero_bon} "
            f"({bon.quantite_sacs} sac(s))."
        )
    except BonRetrait.DoesNotExist:
        instruction_bon = (
            f"Rendez-vous d'abord auprès de {contact} pour régler votre facture "
            f"et obtenir votre bon de retrait."
        )

    return (
        f"Votre commande {contrat.numero_contrat} est prête au retrait.\n\n"
        f"Quantité disponible au magasin : {quantite}.\n\n"
        f"Pour retirer votre farine :\n"
        f"1. {instruction_bon}\n"
        f"2. Présentez-vous au {lieu}, {horaires}.\n"
        f"3. Apportez une pièce d'identité.\n\n"
        f"Nous vous attendons au magasin."
    )


def notifier_commande_prete(contrat: ContratMouture, magasinier) -> NotificationClient | None:
    """Le magasinier signale que la farine est prête à retirer."""
    if NotificationClient.objects.filter(
        client=contrat.client,
        type='COMMANDE_PRETE',
        contrat=contrat,
        lu=False,
    ).exists():
        return None

    notif = NotificationClient.objects.create(
        type='COMMANDE_PRETE',
        message=message_commande_prete_retrait(contrat),
        client=contrat.client,
        contrat=contrat,
        magasinier=magasinier,
    )
    _enregistrer_historique_lots(
        contrat,
        f"Notification client — commande {contrat.numero_contrat} prête au retrait",
        magasinier,
    )
    return notif


def notifier_retrait_effectue(bon: BonRetrait) -> NotificationClient:
    """Après génération du bon de retrait par le comptable."""
    lieu = getattr(settings, 'MNL_RETRAIT_LIEU', 'le magasin MNL')
    horaires = getattr(settings, 'MNL_RETRAIT_HORAIRES', 'aux heures d\'ouverture')

    msg = (
        f"Votre bon de retrait n° {bon.numero_bon} est disponible "
        f"({bon.quantite_sacs} sac(s), contrat {bon.contrat.numero_contrat}).\n\n"
        f"Vous pouvez passer retirer votre farine au {lieu}, {horaires}.\n"
        f"Présentez ce bon de retrait et une pièce d'identité au magasinier."
    )
    notif = NotificationClient.objects.create(
        type='RETRAIT_EFFECTUE',
        message=msg,
        client=bon.client,
        contrat=bon.contrat,
    )
    _enregistrer_historique_lots(
        bon.contrat,
        f"Notification client — bon de retrait {bon.numero_bon} disponible",
        bon.comptable,
    )
    return notif
