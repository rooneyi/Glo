from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView

from facturation.models import Alerte
from accounts.models import Utilisateur
from .forms import ProductionLancerForm, ProductionTerminerForm, ProduitFiniForm
from .models import Production, ProduitFini, StockFarine, BonCession, HistoriqueLot


class MeunierRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'MEUNIER'):
            messages.error(request, "Accès réservé au meunier.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ListeProductionsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Production.objects.select_related('contrat__client', 'meunier').all()
        statut = request.GET.get('statut', '').strip()
        q = request.GET.get('q', '').strip()
        if statut:
            qs = qs.filter(statut=statut)
        if q:
            qs = qs.filter(numero_production__icontains=q) | qs.filter(contrat__client__nom__icontains=q)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'production/list.html', {
            'page_obj': page_obj,
            'statuts': Production.STATUTS,
        })


class DetailProductionView(LoginRequiredMixin, DetailView):
    model = Production
    template_name = 'production/detail.html'
    context_object_name = 'production'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['produits'] = self.object.produits_finis.all()
        try:
            ctx['bon_cession'] = self.object.bon_cession
        except ObjectDoesNotExist:
            ctx['bon_cession'] = None
        ctx['peut_generer_cession'] = (
            self.object.statut == 'TERMINE'
            and self.object.produits_finis.exists()
            and ctx['bon_cession'] is None
            and user.role in ('ADMIN', 'MEUNIER')
        )
        ctx['peut_terminer'] = (
            self.object.statut == 'EN_COURS' and user.role in ('ADMIN', 'MEUNIER')
        )
        ctx['peut_ensacher'] = (
            self.object.statut in ('EN_COURS', 'TERMINE') and user.role in ('ADMIN', 'MEUNIER')
        )
        return ctx


class LancerProductionView(MeunierRequiredMixin, CreateView):
    model = Production
    form_class = ProductionLancerForm
    template_name = 'production/lancer_form.html'

    def form_valid(self, form):
        form.instance.meunier = self.request.user
        form.instance.statut = 'EN_COURS'
        production = form.save()
        contrat = production.contrat
        if contrat.statut != 'EN_COURS':
            contrat.statut = 'EN_COURS'
            contrat.save(update_fields=['statut'])
        messages.success(
            self.request,
            f"Mouture {production.numero_production} lancée pour {contrat.client}.",
        )
        return redirect('production:detail', pk=production.pk)


class TerminerProductionView(MeunierRequiredMixin, View):
    def get(self, request, pk):
        production = get_object_or_404(Production, pk=pk, statut='EN_COURS')
        return render(request, 'production/terminer_form.html', {
            'production': production,
            'form': ProductionTerminerForm(instance=production),
        })

    def post(self, request, pk):
        production = get_object_or_404(Production, pk=pk, statut='EN_COURS')
        form = ProductionTerminerForm(request.POST, instance=production)
        if form.is_valid():
            prod = form.save(commit=False)
            prod.statut = 'TERMINE'
            prod.save()
            for comptable in Utilisateur.objects.filter(role='COMPTABLE', actif=True):
                Alerte.objects.create(
                    type='LIVRAISON_PRETE',
                    message=(
                        f"Production {prod.numero_production} terminée — "
                        f"{prod.quantite_farine_kg} kg de farine prêts pour retrait."
                    ),
                    destinataire=comptable,
                )
            messages.success(request, f"Mouture {prod.numero_production} terminée.")
            return redirect('production:detail', pk=pk)
        return render(request, 'production/terminer_form.html', {
            'production': production,
            'form': form,
        })


class AjouterProduitFiniView(MeunierRequiredMixin, View):
    def get(self, request, pk):
        production = get_object_or_404(Production, pk=pk)
        return render(request, 'production/produit_form.html', {
            'production': production,
            'form': ProduitFiniForm(),
        })

    def post(self, request, pk):
        production = get_object_or_404(Production, pk=pk)
        form = ProduitFiniForm(request.POST)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.production = production
            produit.save()
            StockFarine.objects.create(
                produit_fini=produit,
                quantite_sacs=produit.nombre_sacs,
                quantite_kg=produit.poids_total_kg,
            )
            messages.success(
                request,
                f"{produit.nombre_sacs} sac(s) enregistré(s) — lot {produit.reference_lot}.",
            )
            return redirect('production:detail', pk=pk)
        return render(request, 'production/produit_form.html', {
            'production': production,
            'form': form,
        })


class StockFarineView(LoginRequiredMixin, View):
    def get(self, request):
        entrees = StockFarine.objects.select_related(
            'produit_fini__production__contrat__client'
        ).order_by('-date_maj')
        total = StockFarine.objects.aggregate(
            sacs=Sum('quantite_sacs'), kg=Sum('quantite_kg')
        )
        paginator = Paginator(entrees, 25)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'production/stock.html', {
            'page_obj': page_obj,
            'total_sacs': total['sacs'] or 0,
            'total_kg': round(total['kg'] or 0, 1),
        })


class GenererBonCessionView(MeunierRequiredMixin, View):
    """Le meunier génère le bon de cession produits finis pour le magasinier."""

    def post(self, request, pk):
        production = get_object_or_404(Production, pk=pk, statut='TERMINE')
        if hasattr(production, 'bon_cession'):
            messages.warning(request, "Un bon de cession existe déjà pour cette production.")
            return redirect('production:detail', pk=pk)
        produits = production.produits_finis.all()
        if not produits.exists():
            messages.error(request, "Aucun produit ensaché — impossible de générer le bon.")
            return redirect('production:detail', pk=pk)

        sacs_25 = sum(p.nombre_sacs for p in produits if p.type_sac == '25KG')
        sacs_50 = sum(p.nombre_sacs for p in produits if p.type_sac == '50KG')
        poids = sum(p.poids_total_kg for p in produits)

        bon = BonCession.objects.create(
            production=production,
            meunier=request.user,
            nombre_sacs_25=sacs_25,
            nombre_sacs_50=sacs_50,
            poids_total_kg=poids,
        )
        for produit in produits:
            HistoriqueLot.objects.create(
                produit_fini=produit,
                type_evenement='CESSION',
                description=f"Bon de cession {bon.numero_bon} émis par {request.user}",
                quantite_sacs=produit.nombre_sacs,
                quantite_kg=produit.poids_total_kg,
                auteur=request.user,
            )
        for mag in Utilisateur.objects.filter(role='MAGASINIER', actif=True):
            Alerte.objects.create(
                type='LIVRAISON_PRETE',
                message=(
                    f"Bon de cession {bon.numero_bon} — "
                    f"{bon.nombre_sacs_25 + bon.nombre_sacs_50} sac(s) à recevoir."
                ),
                destinataire=mag,
            )
        messages.success(request, f"Bon de cession {bon.numero_bon} généré.")
        return redirect('production:detail', pk=pk)


class HistoriqueLotView(LoginRequiredMixin, DetailView):
    model = ProduitFini
    template_name = 'production/historique_lot.html'
    context_object_name = 'produit'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['evenements'] = self.object.historique.select_related('auteur')
        return ctx
