from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView

from .forms import EchantillonForm, ResultatLaboratoireForm
from .models import Echantillon, ResultatLaboratoire


class MagasinierMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'MAGASINIER'):
            messages.error(request, "Accès réservé au magasinier.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LaborantinMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'LABORANTIN'):
            messages.error(request, "Accès réservé au laborantin.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


# ── Échantillons ──────────────────────────────────────────────────────────────

class ListeEchantillonsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Echantillon.objects.select_related(
            'reception__contrat__client', 'meunier'
        ).all()
        statut = request.GET.get('statut', '').strip()
        if statut:
            qs = qs.filter(statut=statut)
        paginator = Paginator(qs, 20)
        page_obj  = paginator.get_page(request.GET.get('page'))
        return render(request, 'laboratoire/echantillons/list.html', {
            'page_obj': page_obj,
            'statuts':  Echantillon.STATUTS,
        })


class CreerEchantillonView(MagasinierMixin, CreateView):
    model         = Echantillon
    form_class    = EchantillonForm
    template_name = 'laboratoire/echantillons/form.html'
    success_url   = reverse_lazy('laboratoire:echantillons_list')

    def form_valid(self, form):
        ech = form.save()
        messages.success(self.request,
            f"Échantillon {ech.numero_echantillon} enregistré — envoi au labo Likasi.")
        return redirect(self.success_url)


# ── Résultats ─────────────────────────────────────────────────────────────────

class ListeResultatsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = ResultatLaboratoire.objects.select_related(
            'echantillon__reception__contrat__client', 'laborantin'
        ).all()
        conforme = request.GET.get('conforme', '').strip()
        if conforme == '1':
            qs = qs.filter(conforme=True)
        elif conforme == '0':
            qs = qs.filter(conforme=False)
        paginator = Paginator(qs, 20)
        page_obj  = paginator.get_page(request.GET.get('page'))
        return render(request, 'laboratoire/resultats/list.html', {'page_obj': page_obj})


class EncoderResultatView(LaborantinMixin, CreateView):
    model         = ResultatLaboratoire
    form_class    = ResultatLaboratoireForm
    template_name = 'laboratoire/resultats/form.html'
    success_url   = reverse_lazy('laboratoire:resultats_list')

    def form_valid(self, form):
        form.instance.laborantin = self.request.user
        resultat = form.save()
        statut = "conforme ✓" if resultat.conforme else "NON conforme ✗"
        messages.success(self.request,
            f"Résultat encodé pour {resultat.echantillon} — Maïs {statut}. Meunier notifié.")
        return redirect(self.success_url)
