from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from .forms import ClientForm
from .models import Client


class ComptableRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ('ADMIN', 'COMPTABLE'):
            messages.error(request, "Accès non autorisé.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ListeClientsView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Client.objects.all()
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(nom__icontains=q) | qs.filter(prenom__icontains=q) | qs.filter(telephone__icontains=q)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'clients/list.html', {'page_obj': page_obj})


class CreerClientView(ComptableRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        form.instance.enregistre_par = self.request.user
        messages.success(self.request, f"Client {form.instance} enregistré.")
        return super().form_valid(form)


class ModifierClientView(ComptableRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        messages.success(self.request, "Client mis à jour.")
        return super().form_valid(form)
