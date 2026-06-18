from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView

from .forms import ReceptionForm
from .models import Reception, StockMP


class MagasinierRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'MAGASINIER'):
            messages.error(request, "Accès réservé au magasinier.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


# ── Réceptions ────────────────────────────────────────────────────────────────

class ListeReceptionsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Reception.objects.select_related('contrat__client', 'magasinier').all()
        q = request.GET.get('q', '').strip()
        if q:
            qs = (qs.filter(numero_bon__icontains=q) |
                  qs.filter(contrat__client__nom__icontains=q))
        paginator = Paginator(qs, 20)
        page_obj  = paginator.get_page(request.GET.get('page'))
        return render(request, 'magasin/receptions/list.html', {'page_obj': page_obj})


class CreerReceptionView(MagasinierRequiredMixin, CreateView):
    model        = Reception
    form_class   = ReceptionForm
    template_name = 'magasin/receptions/form.html'

    def form_valid(self, form):
        form.instance.magasinier = self.request.user
        reception = form.save()
        # Passer le contrat en EN_COURS
        contrat = reception.contrat
        if contrat.statut == 'EN_ATTENTE':
            contrat.statut = 'EN_COURS'
            contrat.save(update_fields=['statut'])
        # Créer entrée stock MP
        StockMP.objects.create(
            reception=reception,
            quantite_disponible_kg=reception.poids_net_kg,
        )
        messages.success(self.request,
            f"Réception {reception.numero_bon} enregistrée — {reception.poids_net_kg} kg ajoutés au stock.")
        return redirect('magasin:reception_detail', pk=reception.pk)


class DetailReceptionView(LoginRequiredMixin, DetailView):
    model               = Reception
    template_name       = 'magasin/receptions/detail.html'
    context_object_name = 'reception'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx['echantillon'] = self.object.echantillon
        except Exception:
            ctx['echantillon'] = None
        return ctx


class ImprimerBonReceptionView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reception = get_object_or_404(Reception, pk=pk)
        try:
            from weasyprint import HTML
            html_str = render_to_string('magasin/bon_reception_pdf.html',
                                        {'reception': reception, 'request': request})
            pdf = HTML(string=html_str, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'filename="BRC-{reception.numero_bon}.pdf"'
            )
            return response
        except ImportError:
            messages.error(request, "WeasyPrint non disponible — installez-le avec pip.")
            return redirect('magasin:reception_detail', pk=pk)


# ── Stock MP ──────────────────────────────────────────────────────────────────

class StockMPView(LoginRequiredMixin, View):
    def get(self, request):
        entrees = StockMP.objects.select_related('reception__contrat__client').order_by('-date_maj')
        total = StockMP.objects.aggregate(t=Sum('quantite_disponible_kg'))['t'] or 0
        paginator = Paginator(entrees, 25)
        page_obj  = paginator.get_page(request.GET.get('page'))
        return render(request, 'magasin/stock.html', {
            'page_obj': page_obj,
            'total_kg': round(total, 1),
        })
