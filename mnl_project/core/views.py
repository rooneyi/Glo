import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
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


class RapportQuantitesView(LoginRequiredMixin, View):
    """Rapport : quantités reçues, produites, ensachées, livrées et stockées."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'COMPTABLE'):
            messages.error(request, "Accès réservé au comptable et à l'administrateur.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        debut_str = request.GET.get('debut', '').strip()
        fin_str = request.GET.get('fin', '').strip()
        debut, fin = self._parse_dates(debut_str, fin_str)

        rec_qs = Reception.objects.select_related('contrat__client', 'magasinier')
        prod_qs = Production.objects.filter(statut='TERMINE').select_related(
            'contrat__client', 'meunier',
        )
        ensache_qs = ProduitFini.objects.select_related('production__contrat__client')
        livre_qs = BonRetrait.objects.select_related('client', 'contrat')
        stock_qs = StockFarine.objects.select_related(
            'produit_fini__production__contrat__client',
        )

        if debut:
            rec_qs = rec_qs.filter(date_reception__gte=debut)
            prod_qs = prod_qs.filter(date_fin__gte=debut)
            ensache_qs = ensache_qs.filter(date_ensachage__gte=debut)
            livre_qs = livre_qs.filter(date_retrait__gte=debut)
        if fin:
            rec_qs = rec_qs.filter(date_reception__lte=fin)
            prod_qs = prod_qs.filter(date_fin__lte=fin)
            ensache_qs = ensache_qs.filter(date_ensachage__lte=fin)
            livre_qs = livre_qs.filter(date_retrait__lte=fin)

        recu = rec_qs.aggregate(t=Sum('poids_net_kg'), n=Count('id'))
        traite = prod_qs.aggregate(t=Sum('quantite_traitee_kg'))
        produit = prod_qs.aggregate(t=Sum('quantite_farine_kg'), n=Count('id'), avg=Avg('quantite_farine_kg'))
        ensache = ensache_qs.aggregate(sacs=Sum('nombre_sacs'), kg=Sum('poids_total_kg'), n=Count('id'))
        livre = livre_qs.aggregate(sacs=Sum('quantite_sacs'), n=Count('id'))
        stocke = stock_qs.aggregate(sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg'))
        stock_mp = StockMP.objects.aggregate(t=Sum('quantite_disponible_kg'))

        recu_kg = recu['t'] or 0
        produit_kg = produit['t'] or 0
        ensache_kg = ensache['kg'] or 0
        ensache_sacs = ensache['sacs'] or 0
        livre_sacs = livre['sacs'] or 0
        rendement = round(produit_kg / recu_kg * 100, 1) if recu_kg else None
        livre_kg = round(livre_sacs * ensache_kg / ensache_sacs, 1) if ensache_sacs else 0

        periode_label = self._periode_label(debut, fin, debut_str, fin_str)

        return render(request, 'core/rapport.html', {
            'debut': debut_str,
            'fin': fin_str,
            'periode_label': periode_label,
            'rapport': {
                'recu_kg': round(recu_kg, 1),
                'recu_nb': recu['n'] or 0,
                'traite_kg': round(traite['t'] or 0, 1),
                'produit_kg': round(produit_kg, 1),
                'produit_nb': produit['n'] or 0,
                'rendement_pct': rendement,
                'ensache_sacs': ensache_sacs,
                'ensache_kg': round(ensache_kg, 1),
                'ensache_nb': ensache['n'] or 0,
                'livre_sacs': livre_sacs,
                'livre_kg': livre_kg,
                'livre_nb': livre['n'] or 0,
                'stocke_sacs': stocke['sacs'] or 0,
                'stocke_kg': round(stocke['kg'] or 0, 1),
                'stock_mp_kg': round(stock_mp['t'] or 0, 1),
            },
            'receptions': rec_qs.order_by('-date_reception')[:30],
            'productions': prod_qs.order_by('-date_fin')[:30],
            'ensachages': ensache_qs.order_by('-date_ensachage')[:30],
            'livraisons': livre_qs.order_by('-date_retrait')[:30],
            'stock_actuel': stock_qs.order_by('-date_maj')[:30],
        })

    @staticmethod
    def _parse_dates(debut_str: str, fin_str: str):
        debut = fin = None
        for raw, idx in ((debut_str, 0), (fin_str, 1)):
            if not raw:
                continue
            try:
                parsed = datetime.strptime(raw, '%Y-%m-%d').date()
                if idx == 0:
                    debut = parsed
                else:
                    fin = parsed
            except ValueError:
                pass
        return debut, fin

    @staticmethod
    def _periode_label(debut, fin, debut_str, fin_str):
        if debut and fin:
            return f"Du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}"
        if debut:
            return f"Depuis le {debut.strftime('%d/%m/%Y')}"
        if fin:
            return f"Jusqu'au {fin.strftime('%d/%m/%Y')}"
        if debut_str or fin_str:
            return 'Période personnalisée'
        return 'Toutes périodes'
