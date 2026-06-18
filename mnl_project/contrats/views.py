from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import ContratMoutureForm
from .models import ContratMouture


class ComptableRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'COMPTABLE'):
            messages.error(request, "Accès non autorisé.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ListeContratsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = ContratMouture.objects.select_related('client', 'comptable').all()
        q = request.GET.get('q', '').strip()
        statut = request.GET.get('statut', '').strip()
        if q:
            qs = qs.filter(numero_contrat__icontains=q) | qs.filter(client__nom__icontains=q)
        if statut:
            qs = qs.filter(statut=statut)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'contrats/list.html', {
            'page_obj': page_obj,
            'statuts': ContratMouture.STATUTS,
        })


class CreerContratView(ComptableRequiredMixin, CreateView):
    model = ContratMouture
    form_class = ContratMoutureForm
    template_name = 'contrats/form.html'
    success_url = reverse_lazy('contrats:list')

    def form_valid(self, form):
        form.instance.comptable = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Contrat {self.object.numero_contrat} créé avec succès.")
        return response


class ModifierContratView(ComptableRequiredMixin, UpdateView):
    model = ContratMouture
    form_class = ContratMoutureForm
    template_name = 'contrats/form.html'
    success_url = reverse_lazy('contrats:list')

    def form_valid(self, form):
        messages.success(self.request, "Contrat mis à jour.")
        return super().form_valid(form)
