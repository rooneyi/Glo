import json
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from facturation.alertes_service import verifier_alertes_retard
from facturation.models import Alerte, BonRetrait
from contrats.models import ContratMouture
from laboratoire.models import Echantillon, ResultatLaboratoire
from magasin.models import Reception, StockMP
from production.models import BonCession, HistoriqueLot, Production, ProduitFini, StockFarine

NB_MOIS_STATS = 12


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
            livraisons_mois = BonRetrait.objects.filter(
                date_retrait__year=now.year, date_retrait__month=now.month,
            )
            kpi['livraisons_mois'] = livraisons_mois.count()
            kpi['livraisons_sacs_mois'] = livraisons_mois.aggregate(
                t=Sum('quantite_sacs'),
            )['t'] or 0

        if user.role in ('ADMIN', 'LABORANTIN', 'MEUNIER'):
            kpi['analyses_en_cours'] = Echantillon.objects.filter(
                statut__in=('EN_ATTENTE', 'EN_COURS'),
            ).count()
            kpi['resultats_labo'] = ResultatLaboratoire.objects.filter(
                date_analyse__year=now.year, date_analyse__month=now.month,
            ).count()
            kpi['echantillons_mois'] = Echantillon.objects.filter(
                date_envoi_labo__year=now.year, date_envoi_labo__month=now.month,
            ).count()
            kpi['analyses_conformes_mois'] = ResultatLaboratoire.objects.filter(
                date_analyse__year=now.year,
                date_analyse__month=now.month,
                conforme=True,
            ).count()

        if user.role in ('ADMIN', 'MEUNIER', 'MAGASINIER', 'COMPTABLE'):
            kpi['lots_valides'] = ProduitFini.objects.filter(statut_lot='VALIDE').count()
            kpi['lots_en_attente'] = ProduitFini.objects.filter(statut_lot='EN_ATTENTE').count()
            kpi['lots_valides_mois'] = HistoriqueLot.objects.filter(
                type_evenement='VALIDATION',
                date_evenement__year=now.year,
                date_evenement__month=now.month,
            ).count()

        if user.role in ('ADMIN', 'MEUNIER'):
            stock_f = StockFarine.objects.aggregate(
                sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg'),
            )
            kpi['stock_farine_sacs'] = stock_f['sacs'] or 0
            kpi['stock_farine_kg'] = round(stock_f['kg'] or 0, 1)
            prod_mois = Production.objects.filter(
                statut='TERMINE',
                date_fin__year=now.year,
                date_fin__month=now.month,
            )
            kpi['productions_mois'] = prod_mois.count()
            kpi['production_kg_mois'] = round(
                prod_mois.aggregate(t=Sum('quantite_farine_kg'))['t'] or 0, 1,
            )

        if user.role == 'ADMIN':
            rend = Production.objects.filter(statut='TERMINE').aggregate(
                avg=Avg('quantite_farine_kg'),
            )
            kpi['rendement_moyen'] = round(rend['avg'] or 0, 1)

        ctx['kpi'] = kpi

        show_stats = user.role in ('ADMIN', 'COMPTABLE', 'MEUNIER', 'MAGASINIER', 'LABORANTIN')
        stats = self._stats_dashboard_mensuel() if show_stats else None
        activite = self._activite_recente(user)
        ctx['dashboard_payload'] = self._build_dashboard_payload(
            request=self.request,
            user=user,
            kpi=kpi,
            stats=stats,
            show_stats=show_stats,
            alertes=list(ctx['alertes_recentes']),
            activite=activite,
        )
        ctx['dashboard_built'] = (
            settings.BASE_DIR / 'static' / 'dashboard' / 'dashboard.js'
        ).is_file()
        return ctx

    @staticmethod
    def _derniers_mois(n: int = NB_MOIS_STATS) -> list[date]:
        today = timezone.now().date().replace(day=1)
        months = [today]
        current = today
        for _ in range(n - 1):
            if current.month == 1:
                current = date(current.year - 1, 12, 1)
            else:
                current = date(current.year, current.month - 1, 1)
            months.insert(0, current)
        return months

    @staticmethod
    def _dict_par_mois(qs, date_field: str, **aggregations) -> dict:
        rows = (
            qs.annotate(mois=TruncMonth(date_field))
            .values('mois')
            .annotate(**aggregations)
            .order_by('mois')
        )
        return {
            (row['mois'].year, row['mois'].month): row
            for row in rows
            if row['mois']
        }

    def _stats_dashboard_mensuel(self) -> dict:
        """Statistiques mensuelles sur 12 mois — production, lots, livraisons, labo."""
        mois_list = self._derniers_mois(NB_MOIS_STATS)
        debut = mois_list[0]

        prod_map = self._dict_par_mois(
            Production.objects.filter(statut='TERMINE', date_fin__gte=debut),
            'date_fin',
            total_kg=Sum('quantite_farine_kg'),
            nb=Count('id'),
        )
        lots_map = self._dict_par_mois(
            HistoriqueLot.objects.filter(
                type_evenement='VALIDATION',
                date_evenement__gte=debut,
            ),
            'date_evenement',
            nb=Count('id'),
        )
        livraisons_map = self._dict_par_mois(
            BonRetrait.objects.filter(date_retrait__gte=debut),
            'date_retrait',
            sacs=Sum('quantite_sacs'),
            nb=Count('id'),
        )
        analyses_map = self._dict_par_mois(
            ResultatLaboratoire.objects.filter(date_analyse__gte=debut),
            'date_analyse',
            nb=Count('id'),
            conformes=Count('id', filter=Q(conforme=True)),
        )
        echantillons_map = self._dict_par_mois(
            Echantillon.objects.filter(date_envoi_labo__gte=debut),
            'date_envoi_labo',
            nb=Count('id'),
        )

        labels, production_kg, production_nb = [], [], []
        lots_valides, livraisons_sacs, analyses_labo = [], [], []
        echantillons_envoyes, table_rows = [], []

        for mois in mois_list:
            key = (mois.year, mois.month)
            label = mois.strftime('%b %Y')
            labels.append(label)

            p = prod_map.get(key, {})
            kg = round(p.get('total_kg') or 0, 1)
            p_nb = p.get('nb') or 0
            production_kg.append(kg)
            production_nb.append(p_nb)

            l_nb = lots_map.get(key, {}).get('nb') or 0
            lots_valides.append(l_nb)

            liv = livraisons_map.get(key, {})
            l_sacs = liv.get('sacs') or 0
            livraisons_sacs.append(l_sacs)

            a_nb = analyses_map.get(key, {}).get('nb') or 0
            analyses_labo.append(a_nb)

            e_nb = echantillons_map.get(key, {}).get('nb') or 0
            echantillons_envoyes.append(e_nb)

            table_rows.append({
                'mois': label,
                'mois_key': mois.isoformat(),
                'production_nb': p_nb,
                'production_kg': kg,
                'lots_valides': l_nb,
                'livraisons_nb': liv.get('nb') or 0,
                'livraisons_sacs': l_sacs,
                'analyses_nb': a_nb,
                'analyses_conformes': analyses_map.get(key, {}).get('conformes') or 0,
                'echantillons_nb': e_nb,
            })

        return {
            'labels': labels,
            'production_kg': production_kg,
            'production_nb': production_nb,
            'lots_valides': lots_valides,
            'livraisons_sacs': livraisons_sacs,
            'analyses_labo': analyses_labo,
            'echantillons_envoyes': echantillons_envoyes,
            'rows': table_rows,
            'totaux': {
                'production_kg': round(sum(production_kg), 1),
                'production_nb': sum(production_nb),
                'lots_valides': sum(lots_valides),
                'livraisons_sacs': sum(livraisons_sacs),
                'analyses_labo': sum(analyses_labo),
            },
        }

    def _activite_recente(self, user):
        events = []
        if user.role in ('ADMIN', 'COMPTABLE'):
            for c in ContratMouture.objects.select_related('client', 'comptable').order_by('-date_creation')[:4]:
                events.append({
                    'type': 'contrat',
                    'description': f"Contrat {c.numero_contrat} — {c.client}",
                    'date': c.date_creation,
                    'auteur': str(c.comptable),
                })
        if user.role in ('ADMIN', 'MAGASINIER'):
            for r in Reception.objects.select_related('magasinier').order_by('-date_creation')[:4]:
                events.append({
                    'type': 'reception',
                    'description': f"Réception {r.numero_bon} — {r.poids_net_kg} kg",
                    'date': r.date_creation,
                    'auteur': str(r.magasinier),
                })
        if user.role in ('ADMIN', 'MEUNIER'):
            for p in Production.objects.select_related('contrat__client').order_by('-date_creation')[:3]:
                events.append({
                    'type': 'production',
                    'description': f"Mouture {p.numero_production} — {p.contrat.client}",
                    'date': p.date_creation,
                    'auteur': str(p.meunier),
                })
        if user.role in ('ADMIN', 'LABORANTIN'):
            for e in Echantillon.objects.order_by('-date_creation')[:3]:
                events.append({
                    'type': 'labo',
                    'description': f"Échantillon {e.numero_echantillon} — {e.get_statut_display()}",
                    'date': e.date_creation,
                    'auteur': str(e.meunier),
                })
        events.sort(key=lambda e: e['date'], reverse=True)
        return events[:8]

    def _build_dashboard_payload(self, request, user, kpi, stats, show_stats, alertes, activite):
        role = user.role
        alerte_types = {
            'RESULTAT_LABO': ('text-indigo-600', 'Résultat laboratoire'),
            'LIVRAISON_PRETE': ('text-green-700', 'Livraison prête'),
            'RETARD': ('text-red-600', 'Retard'),
        }

        def fmt_since(dt):
            delta = timezone.now() - dt
            sec = int(delta.total_seconds())
            if sec < 3600:
                return f'il y a {max(sec // 60, 1)} min'
            if sec < 86400:
                return f'il y a {sec // 3600} h'
            return f'il y a {sec // 86400} j'

        urls = {
            'alertes': reverse('facturation:alertes'),
        }
        if role in ('ADMIN', 'COMPTABLE'):
            urls['rapport'] = reverse('core:rapport')

        cards = []

        def add_card(cid, label, value, unit='', sub='', accent='blue', link=''):
            cards.append({
                'id': cid, 'label': label, 'value': str(value), 'unit': unit,
                'sub': sub, 'accent': accent, 'link': link,
            })

        if role in ('ADMIN', 'MAGASINIER'):
            add_card('stock_mp', 'Stock maïs', kpi.get('stock_mp_kg', 0), 'kg',
                     'Matière première disponible', 'green')
        if role in ('ADMIN', 'COMPTABLE'):
            add_card('contrats', 'Contrats actifs', kpi.get('contrats_en_cours', 0), '',
                     'En cours de traitement', 'blue')
        if role in ('ADMIN', 'MEUNIER'):
            add_card('stock_farine', 'Stock farine', kpi.get('stock_farine_sacs', 0), 'sacs',
                     f"{kpi.get('stock_farine_kg', 0)} kg disponibles", 'orange')
        add_card(
            'alertes', 'Alertes', kpi.get('alertes_non_lues', 0), '',
            f"Labo {kpi.get('alertes_resultat_labo', 0)} · Livraison {kpi.get('alertes_livraison', 0)} · Retard {kpi.get('alertes_retard', 0)}"
            if kpi.get('alertes_non_lues') else 'Aucune alerte',
            'red' if kpi.get('alertes_non_lues') else 'blue',
            reverse('facturation:alertes') if kpi.get('alertes_non_lues') else '',
        )
        if role == 'ADMIN':
            add_card('rendement', 'Rendement moyen', kpi.get('rendement_moyen', '—'), '%',
                     'Taux de mouture', 'purple')
            add_card('receptions', 'Réceptions (mois)', kpi.get('receptions_mois', 0), '',
                     f"{kpi.get('total_mais_mois', 0)} kg reçus", 'teal')
        if role in ('ADMIN', 'LABORANTIN', 'MEUNIER'):
            sub_labo = f"En cours · {kpi.get('resultats_labo', 0)} résultat(s) ce mois"
            if kpi.get('echantillons_mois'):
                sub_labo += f" · {kpi.get('echantillons_mois')} envoi(s) · {kpi.get('analyses_conformes_mois', 0)} conforme(s)"
            add_card('labo', 'Laboratoire', kpi.get('analyses_en_cours', 0), '', sub_labo, 'indigo')
        if role in ('ADMIN', 'COMPTABLE'):
            add_card('livraisons', 'Livraisons', kpi.get('livraisons_sacs_mois', 0), 'sacs',
                     f"{kpi.get('livraisons_mois', 0)} retrait(s) · {kpi.get('livraisons_pretes', 0)} alerte(s)",
                     'violet')
        if role in ('ADMIN', 'MEUNIER', 'MAGASINIER', 'COMPTABLE'):
            add_card('lots', 'Lots validés', kpi.get('lots_valides', 0), '',
                     f"{kpi.get('lots_en_attente', 0)} en attente · {kpi.get('lots_valides_mois', 0)} ce mois",
                     'emerald')
        if role in ('ADMIN', 'MEUNIER'):
            add_card('prod_mois', 'Production (mois)', kpi.get('production_kg_mois', 0), 'kg',
                     f"{kpi.get('productions_mois', 0)} mouture(s) terminée(s)", 'sky')
        if role in ('ADMIN', 'MAGASINIER'):
            add_card('cession', 'Bons cession', kpi.get('bons_cession_attente', 0), '',
                     'À recevoir (produits finis)', 'amber')

        actions = []
        if role in ('ADMIN', 'COMPTABLE'):
            actions.extend([
                {'label': 'Nouveau client', 'sub': 'Enregistrer un client', 'href': reverse('clients:create'), 'icon': 'CL'},
                {'label': 'Nouveau contrat', 'sub': 'Contrat de mouture', 'href': reverse('contrats:create'), 'icon': 'CT'},
            ])
        if role in ('ADMIN', 'MAGASINIER'):
            actions.extend([
                {'label': 'Réception maïs', 'sub': 'Enregistrer une réception', 'href': reverse('magasin:reception_create'), 'icon': 'RC'},
                {'label': 'Bons cession PF', 'sub': f"{kpi.get('bons_cession_attente', 0)} en attente", 'href': reverse('magasin:bons_cession_list'), 'icon': 'BC'},
            ])
        if role == 'ADMIN':
            actions.append({'label': 'Nouvel utilisateur', 'sub': 'Créer un compte', 'href': reverse('accounts:user_create'), 'icon': 'US'})

        return {
            'role': role,
            'roleDisplay': user.get_role_display(),
            'showStats': show_stats,
            'kpiCards': cards,
            'stats': stats,
            'urls': urls,
            'alertes': [
                {
                    'id': a.id,
                    'typeLabel': a.get_type_display(),
                    'typeClass': alerte_types.get(a.type, ('text-zinc-500', ''))[0],
                    'message': a.message,
                    'lu': a.lu,
                    'since': fmt_since(a.date_creation),
                }
                for a in alertes
            ],
            'activite': [
                {
                    'type': e['type'],
                    'description': e['description'],
                    'auteur': e['auteur'],
                    'since': fmt_since(e['date']),
                }
                for e in activite
            ],
            'actions': actions,
        }


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
