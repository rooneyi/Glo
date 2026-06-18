from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from facturation.models import Alerte, BonRetrait
from contrats.models import ContratMouture
from magasin.models import Reception, StockMP
from production.models import Production, StockFarine


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # Alertes non lues pour l'utilisateur connecté
        alertes_non_lues = Alerte.objects.filter(destinataire=user, lu=False).count()
        ctx['alerte_count'] = alertes_non_lues

        kpi = {}
        kpi['alertes_non_lues'] = alertes_non_lues

        if user.role in ('ADMIN', 'MAGASINIER'):
            stock_mp = StockMP.objects.aggregate(total=Sum('quantite_disponible_kg'))
            kpi['stock_mp_kg'] = round(stock_mp['total'] or 0, 1)
            receptions_mois = Reception.objects.filter(
                date_creation__year=now.year, date_creation__month=now.month
            )
            kpi['receptions_mois'] = receptions_mois.count()
            kpi['total_mais_mois'] = round(
                receptions_mois.aggregate(t=Sum('poids_net_kg'))['t'] or 0, 1
            )

        if user.role in ('ADMIN', 'COMPTABLE'):
            kpi['contrats_en_cours'] = ContratMouture.objects.filter(statut='EN_COURS').count()

        if user.role in ('ADMIN', 'MEUNIER'):
            stock_f = StockFarine.objects.aggregate(
                sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg')
            )
            kpi['stock_farine_sacs'] = stock_f['sacs'] or 0
            kpi['stock_farine_kg'] = round(stock_f['kg'] or 0, 1)

        if user.role == 'ADMIN':
            rend = Production.objects.filter(statut='TERMINE').aggregate(
                avg=Avg('quantite_farine_kg')
            )
            kpi['rendement_moyen'] = round(rend['avg'] or 0, 1)

        ctx['kpi'] = kpi
        ctx['activite_recente'] = self._activite_recente(user)
        return ctx

    def _activite_recente(self, user):
        events = []
        if user.role in ('ADMIN', 'COMPTABLE'):
            for c in ContratMouture.objects.order_by('-date_creation')[:3]:
                events.append({
                    'type': 'contrat',
                    'description': f"Contrat {c.numero_contrat} — {c.client}",
                    'date': c.date_creation,
                    'auteur': str(c.comptable) if hasattr(c, 'comptable') else '—',
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
