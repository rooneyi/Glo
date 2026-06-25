"""Notifications envoyées aux clients (magasinier → client)."""
from django.core.exceptions import ObjectDoesNotExist

from contrats.models import ContratMouture

from .models import BonRetrait, NotificationClient


def notifier_commande_prete(contrat: ContratMouture, magasinier) -> NotificationClient | None:
    """Le magasinier signale que la farine est prête à retirer."""
    sacs = 0
    try:
        sacs = sum(p.nombre_sacs for p in contrat.production.produits_finis.all())
    except ObjectDoesNotExist:
        pass
    fragment = contrat.numero_contrat
    existe = NotificationClient.objects.filter(
        client=contrat.client,
        type='COMMANDE_PRETE',
        contrat=contrat,
        lu=False,
        message__contains=fragment,
    ).exists()
    if existe:
        return None
    msg = (
        f"Votre commande {contrat.numero_contrat} est prête au retrait — "
        f"{sacs} sac(s) disponible(s) au magasin. "
        f"Présentez-vous avec votre bon de retrait."
    )
    return NotificationClient.objects.create(
        type='COMMANDE_PRETE',
        message=msg,
        client=contrat.client,
        contrat=contrat,
        magasinier=magasinier,
    )


def notifier_retrait_effectue(bon: BonRetrait) -> NotificationClient:
    """Après génération du bon de retrait par le comptable."""
    msg = (
        f"Retrait enregistré — bon {bon.numero_bon}, "
        f"{bon.quantite_sacs} sac(s) le {bon.date_retrait.strftime('%d/%m/%Y')}."
    )
    return NotificationClient.objects.create(
        type='RETRAIT_EFFECTUE',
        message=msg,
        client=bon.client,
        contrat=bon.contrat,
    )
