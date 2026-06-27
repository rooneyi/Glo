"""Timeline unifiée pour l'espace client (retraits + notifications)."""
from dataclasses import dataclass
from datetime import datetime

from facturation.models import BonRetrait, NotificationClient


@dataclass
class EvenementClient:
    date: datetime
    categorie: str  # retrait | notification
    titre: str
    detail: str
    contrat_numero: str = ''
    sacs: int | None = None
    bon_numero: str = ''


def historique_client(client) -> list[EvenementClient]:
    """Fusionne bons de retrait et notifications reçues par le client."""
    evenements: list[EvenementClient] = []

    for bon in BonRetrait.objects.filter(contrat__client=client).select_related('contrat'):
        evenements.append(EvenementClient(
            date=bon.date_creation,
            categorie='retrait',
            titre=f"Bon de retrait {bon.numero_bon}",
            detail=(
                f"{bon.quantite_sacs} sac(s) — date de retrait : "
                f"{bon.date_retrait.strftime('%d/%m/%Y')}"
            ),
            contrat_numero=bon.contrat.numero_contrat,
            sacs=bon.quantite_sacs,
            bon_numero=bon.numero_bon,
        ))

    for notif in NotificationClient.objects.filter(client=client).select_related('contrat'):
        contrat_num = notif.contrat.numero_contrat if notif.contrat else ''
        evenements.append(EvenementClient(
            date=notif.date_creation,
            categorie='notification',
            titre=notif.get_type_display(),
            detail=notif.message,
            contrat_numero=contrat_num,
        ))

    evenements.sort(key=lambda e: e.date, reverse=True)
    return evenements
