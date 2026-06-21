from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import CreateView, DetailView
from django.http import HttpResponse

from production.models import StockFarine
from production.lot_traceabilite import synchroniser_historique_contrat
from .forms import BonRetraitForm
from .models import Alerte, BonRetrait


class ComptableRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'COMPTABLE'):
            messages.error(request, "Accès réservé au comptable.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


def _decrementer_stock_sacs(quantite: int) -> None:
    """Retire des sacs du stock (FIFO sur les entrées les plus anciennes)."""
    reste = quantite
    for entree in StockFarine.objects.order_by('date_maj'):
        if reste <= 0:
            break
        if entree.quantite_sacs <= reste:
            reste -= entree.quantite_sacs
            entree.delete()
        else:
            ratio = reste / entree.quantite_sacs
            entree.quantite_sacs -= reste
            entree.quantite_kg = round(entree.quantite_kg * (1 - ratio), 1)
            entree.save(update_fields=['quantite_sacs', 'quantite_kg'])
            reste = 0


# ── Bons de retrait ───────────────────────────────────────────────────────────

class ListeBonsRetraitView(LoginRequiredMixin, View):
    def get(self, request):
        qs = BonRetrait.objects.select_related('client', 'comptable', 'contrat').all()
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(numero_bon__icontains=q) | qs.filter(client__nom__icontains=q)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'facturation/bons/list.html', {'page_obj': page_obj})


class CreerBonRetraitView(ComptableRequiredMixin, CreateView):
    model = BonRetrait
    form_class = BonRetraitForm
    template_name = 'facturation/bons/form.html'

    def form_valid(self, form):
        bon = form.save(commit=False)
        bon.client = bon.contrat.client
        bon.comptable = self.request.user
        bon.save()
        _decrementer_stock_sacs(bon.quantite_sacs)
        bon.contrat.statut = 'TERMINE'
        bon.contrat.save(update_fields=['statut'])
        synchroniser_historique_contrat(bon.contrat)
        messages.success(self.request, f"Bon de retrait {bon.numero_bon} généré.")
        return redirect('facturation:bon_detail', pk=bon.pk)


class DetailBonRetraitView(LoginRequiredMixin, DetailView):
    model = BonRetrait
    template_name = 'facturation/bons/detail.html'
    context_object_name = 'bon'


class ImprimerBonRetraitView(LoginRequiredMixin, View):
    def get(self, request, pk):
        bon = get_object_or_404(BonRetrait, pk=pk)
        try:
            from weasyprint import HTML
            html_str = render_to_string(
                'facturation/bons/bon_retrait_pdf.html',
                {'bon': bon, 'request': request},
            )
            pdf = HTML(string=html_str, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'filename="{bon.numero_bon}.pdf"'
            return response
        except ImportError:
            messages.error(request, "WeasyPrint non disponible.")
            return redirect('facturation:bon_detail', pk=pk)


# ── Alertes ───────────────────────────────────────────────────────────────────

class ListeAlertesView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Alerte.objects.filter(destinataire=request.user).order_by('-date_creation')
        type_filtre = request.GET.get('type', '').strip()
        if type_filtre:
            qs = qs.filter(type=type_filtre)
        non_lues = Alerte.objects.filter(destinataire=request.user, lu=False)
        compteurs = {
            'RESULTAT_LABO': non_lues.filter(type='RESULTAT_LABO').count(),
            'LIVRAISON_PRETE': non_lues.filter(type='LIVRAISON_PRETE').count(),
            'RETARD': non_lues.filter(type='RETARD').count(),
        }
        paginator = Paginator(qs, 25)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'facturation/alertes/list.html', {
            'page_obj': page_obj,
            'non_lues': non_lues.count(),
            'type_filtre': type_filtre,
            'compteurs': compteurs,
            'types_alertes': Alerte.TYPES,
        })


class MarquerAlerteLuView(LoginRequiredMixin, View):
    def post(self, request, pk):
        alerte = get_object_or_404(Alerte, pk=pk, destinataire=request.user)
        alerte.lu = True
        alerte.save(update_fields=['lu'])
        return redirect('facturation:alertes')


class MarquerToutesLuesView(LoginRequiredMixin, View):
    def post(self, request):
        Alerte.objects.filter(destinataire=request.user, lu=False).update(lu=True)
        messages.success(request, "Toutes les alertes ont été marquées comme lues.")
        return redirect('facturation:alertes')


# ── Historique retraits (par client, staff) ────────────────────────────────────

class MesRetraitsView(ComptableRequiredMixin, View):
    """Historique des retraits — filtrable par client (pas de rôle CLIENT pour l'instant)."""

    def get(self, request):
        qs = BonRetrait.objects.select_related('client', 'contrat').order_by('-date_retrait')
        client_id = request.GET.get('client', '').strip()
        if client_id:
            qs = qs.filter(client_id=client_id)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        from clients.models import Client
        return render(request, 'facturation/bons/mes_retraits.html', {
            'page_obj': page_obj,
            'clients': Client.objects.order_by('nom', 'prenom')[:100],
        })
