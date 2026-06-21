"""Traçabilité complète d'un lot de farine (réception → retrait client)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .models import HistoriqueLot, ProduitFini


def _as_datetime(d) -> datetime:
    if not d:
        return timezone.now()
    dt = datetime.combine(d, datetime.min.time())
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


@dataclass
class EvenementTrace:
    type_evenement: str
    label: str
    description: str
    date_evenement: datetime
    auteur: Optional[str] = None
    quantite_sacs: Optional[int] = None
    quantite_kg: Optional[float] = None
    persiste: bool = False


def _a_evenement(produit: ProduitFini, type_evt: str, fragment: str) -> bool:
    return produit.historique.filter(
        type_evenement=type_evt,
        description__contains=fragment,
    ).exists()


def _creer_evenement(
    produit: ProduitFini,
    type_evt: str,
    description: str,
    *,
    date_evenement=None,
    auteur=None,
    quantite_sacs=None,
    quantite_kg=None,
) -> HistoriqueLot:
    return HistoriqueLot.objects.create(
        produit_fini=produit,
        type_evenement=type_evt,
        description=description,
        date_evenement=date_evenement or timezone.now(),
        auteur=auteur,
        quantite_sacs=quantite_sacs,
        quantite_kg=quantite_kg,
    )


def synchroniser_historique_lot(produit: ProduitFini) -> None:
    """Enregistre en base les étapes antérieures à l'ensachage si elles manquent."""
    prod = produit.production
    contrat = prod.contrat

    try:
        reception = contrat.reception
        if not _a_evenement(produit, 'CREATION', reception.numero_bon):
            _creer_evenement(
                produit,
                'CREATION',
                f"Réception magasin {reception.numero_bon} — {reception.poids_net_kg} kg net",
                date_evenement=_as_datetime(reception.date_reception),
                auteur=reception.magasinier,
                quantite_kg=reception.poids_net_kg,
            )

        try:
            echantillon = reception.echantillon
            if not _a_evenement(produit, 'ANALYSE', echantillon.numero_echantillon):
                _creer_evenement(
                    produit,
                    'ANALYSE',
                    f"Échantillon {echantillon.numero_echantillon} envoyé au laboratoire",
                    date_evenement=_as_datetime(echantillon.date_envoi_labo),
                    auteur=echantillon.meunier,
                )

            try:
                resultat = echantillon.resultat
                fragment = f"Résultat {echantillon.numero_echantillon}"
                if not _a_evenement(produit, 'ANALYSE', fragment):
                    conforme = 'conforme' if resultat.conforme else 'NON conforme'
                    _creer_evenement(
                        produit,
                        'ANALYSE',
                        (
                            f"Résultat {echantillon.numero_echantillon} — maïs {conforme} "
                            f"(H: {resultat.taux_humidite}%, MG: {resultat.taux_matiere_grasse}%)"
                        ),
                        date_evenement=_as_datetime(resultat.date_analyse),
                        auteur=resultat.laborantin,
                    )
            except ObjectDoesNotExist:
                pass
        except ObjectDoesNotExist:
            pass
    except ObjectDoesNotExist:
        pass

    if not _a_evenement(produit, 'MOUTURE', 'lancée'):
        _creer_evenement(
            produit,
            'MOUTURE',
            f"Mouture {prod.numero_production} lancée",
            date_evenement=_as_datetime(prod.date_debut),
            auteur=prod.meunier,
            quantite_kg=prod.quantite_traitee_kg or None,
        )

    if prod.statut == 'TERMINE' and prod.date_fin and not _a_evenement(produit, 'MOUTURE', 'terminée'):
        _creer_evenement(
            produit,
            'MOUTURE',
            (
                f"Mouture {prod.numero_production} terminée — "
                f"{prod.quantite_farine_kg} kg de farine produits"
            ),
            date_evenement=_as_datetime(prod.date_fin),
            auteur=prod.meunier,
            quantite_kg=prod.quantite_farine_kg,
        )

    try:
        bon_retrait = contrat.bon_retrait
        if not _a_evenement(produit, 'RETRAIT', bon_retrait.numero_bon):
            _creer_evenement(
                produit,
                'RETRAIT',
                (
                    f"Retrait client — bon {bon_retrait.numero_bon}, "
                    f"{bon_retrait.quantite_sacs} sac(s)"
                ),
                date_evenement=_as_datetime(bon_retrait.date_retrait),
                auteur=bon_retrait.comptable,
                quantite_sacs=bon_retrait.quantite_sacs,
            )
    except ObjectDoesNotExist:
        pass


def synchroniser_historique_contrat(contrat) -> None:
    """Synchronise l'historique pour tous les lots d'un contrat."""
    from django.core.exceptions import ObjectDoesNotExist
    try:
        production = contrat.production
    except ObjectDoesNotExist:
        return
    for produit in production.produits_finis.all():
        synchroniser_historique_lot(produit)


def historique_complet(produit: ProduitFini) -> list[EvenementTrace]:
    """Timeline fusionnée (persistée + contexte) triée chronologiquement."""
    synchroniser_historique_lot(produit)

    type_labels = dict(HistoriqueLot.TYPES)
    events: list[EvenementTrace] = []
    for evt in produit.historique.select_related('auteur'):
        auteur = evt.auteur.get_full_name() if evt.auteur else None
        events.append(EvenementTrace(
            type_evenement=evt.type_evenement,
            label=type_labels.get(evt.type_evenement, evt.type_evenement),
            description=evt.description,
            date_evenement=evt.date_evenement,
            auteur=auteur,
            quantite_sacs=evt.quantite_sacs,
            quantite_kg=evt.quantite_kg,
            persiste=True,
        ))

    events.sort(key=lambda e: e.date_evenement)
    return events
