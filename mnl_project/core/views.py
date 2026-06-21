import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from facturation.alertes_service import verifier_alertes_retard
from facturation.models import Alerte, BonRetrait
from contrats.models import ContratMouture
from laboratoire.models import Echantillon, ResultatLaboratoire
from magasin.models import Reception, StockMP
from production.models import BonCession, Production, ProduitFini, StockFarine


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        verifier_alertes_retard()

        alertes_qs = Alerte.objects.filter(destinataire=user, lu=False)
        alertes_non_lues = alertes_qs.count()
        ctx['alerte_count'] = alertes_non_lues
        ctx['alertes_recentes'] = Alerte.objects.filter(
            destinataire=user,
        ).order_by('-date_creation')[:8]

        kpi = {
            'alertes_non_lues': alertes_non_lues,
            'alertes_resultat_labo': alertes_qs.filter(type='RESULTAT_LABO').count(),
            'alertes_livraison': alertes_qs.filter(type='LIVRAISON_PRETE').count(),
            'alertes_retard': alertes_qs.filter(type='RETARD').count(),
        }

        if user.role in ('ADMIN', 'MAGASINIER'):
            stock_mp = StockMP.objects.aggregate(total=Sum('quantite_disponible_kg'))
            kpi['stock_mp_kg'] = round(stock_mp['total'] or 0, 1)
            receptions_mois = Reception.objects.filter(
                date_creation__year=now.year, date_creation__month=now.month,
            )
            kpi['receptions_mois'] = receptions_mois.count()
            kpi['total_mais_mois'] = round(
                receptions_mois.aggregate(t=Sum('poids_net_kg'))['t'] or 0, 1,
            )
            kpi['bons_cession_attente'] = BonCession.objects.filter(statut='EN_ATTENTE').count()

        if user.role in ('ADMIN', 'COMPTABLE'):
            kpi['contrats_en_cours'] = ContratMouture.objects.filter(statut='EN_COURS').count()
            kpi['livraisons_pretes'] = Alerte.objects.filter(
                type='LIVRAISON_PRETE', lu=False,
            ).count()

        if user.role in ('ADMIN', 'LABORANTIN', 'MEUNIER'):
            kpi['analyses_en_cours'] = Echantillon.objects.filter(
                statut__in=('EN_ATTENTE', 'EN_COURS'),
            ).count()
            kpi['resultats_labo'] = ResultatLaboratoire.objects.filter(
                date_analyse__year=now.year, date_analyse__month=now.month,
            ).count()

        if user.role in ('ADMIN', 'MEUNIER', 'MAGASINIER', 'COMPTABLE'):
            kpi['lots_valides'] = ProduitFini.objects.filter(statut_lot='VALIDE').count()
            kpi['lots_en_attente'] = ProduitFini.objects.filter(statut_lot='EN_ATTENTE').count()

        if user.role in ('ADMIN', 'MEUNIER'):
            stock_f = StockFarine.objects.aggregate(
                sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg'),
            )
            kpi['stock_farine_sacs'] = stock_f['sacs'] or 0
            kpi['stock_farine_kg'] = round(stock_f['kg'] or 0, 1)

        if user.role == 'ADMIN':
            rend = Production.objects.filter(statut='TERMINE').aggregate(
                avg=Avg('quantite_farine_kg'),
            )
            kpi['rendement_moyen'] = round(rend['avg'] or 0, 1)

        ctx['kpi'] = kpi
        stats = self._stats_production_mensuelle()
        ctx['stats_mensuelles'] = stats
        ctx['chart_labels'] = json.dumps(stats['labels'])
        ctx['chart_values'] = json.dumps(stats['values'])
        ctx['activite_recente'] = self._activite_recente(user)
        return ctx

    def _stats_production_mensuelle(self):
        """Production (kg farine) par mois — 6 derniers mois."""
        qs = (
            Production.objects.filter(statut='TERMINE')
            .annotate(mois=TruncMonth('date_fin'))
            .values('mois')
            .annotate(total_kg=Sum('quantite_farine_kg'), nb=Count('id'))
            .order_by('mois')[:6]
        )
        labels, values, counts = [], [], []
        for row in qs:
            if row['mois']:
                labels.append(row['mois'].strftime('%b %Y'))
                values.append(round(row['total_kg'] or 0, 1))
                counts.append(row['nb'])
        return {'labels': labels, 'values': values, 'counts': counts}

    def _activite_recente(self, user):
        events = []
        if user.role in ('ADMIN', 'COMPTABLE'):
            for c in ContratMouture.objects.order_by('-date_creation')[:3]:
                events.append({
                    'type': 'contrat',
                    'description': f"Contrat {c.numero_contrat} — {c.client} ({c.get_type_mouture_display()})",
                    'date': c.date_creation,
                    'auteur': str(c.comptable),
                })
        if user.role in ('ADMIN', 'MAGASINIER'):
            for r in Reception.objects.order_by('-date_creation')[:3]:
                events.append({
                    'type': 'reception',
                    'description': f"Réception {r.numero_bon} — {r.poids_net_kg} kg",
                    'date': r.date_creation,
                    'auteur': str(r.magasinier),
                })
        events.sort(key=lambda e: e['date'], reverse=True)
        return events[:8]


class RapportQuantitesView(LoginRequiredMixin, TemplateView):
    """Rapport : quantités reçues, produites, ensachées, livrées, stockées."""
    template_name = 'core/rapport.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        recu = Reception.objects.aggregate(t=Sum('poids_net_kg'))['t'] or 0
        produit = Production.objects.filter(statut='TERMINE').aggregate(
            t=Sum('quantite_farine_kg'),
        )['t'] or 0
        ensache = ProduitFini.objects.aggregate(
            sacs=Sum('nombre_sacs'), kg=Sum('poids_total_kg'),
        )
        livre = BonRetrait.objects.aggregate(t=Sum('quantite_sacs'))['t'] or 0
        stocke = StockFarine.objects.aggregate(
            sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg'),
        )
        ctx['rapport'] = {
            'recu_kg': round(recu, 1),
            'produit_kg': round(produit, 1),
            'ensache_sacs': ensache['sacs'] or 0,
            'ensache_kg': round(ensache['kg'] or 0, 1),
            'livre_sacs': livre,
            'stocke_sacs': stocke['sacs'] or 0,
            'stocke_kg': round(stocke['kg'] or 0, 1),
        }
        return ctx
