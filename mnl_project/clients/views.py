from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from .compte_client import (
    CompteClientError,
    creer_compte_client,
    envoyer_identifiants_client,
    synchroniser_compte_client,
)
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
        qs = Client.objects.select_related('compte_utilisateur').all()
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

    def _login_url(self):
        return self.request.build_absolute_uri(reverse('accounts:login'))

    @transaction.atomic
    def form_valid(self, form):
        form.instance.enregistre_par = self.request.user
        self.object = form.save()

        try:
            _, mot_de_passe = creer_compte_client(self.object)
        except CompteClientError as exc:
            messages.error(self.request, str(exc))
            transaction.set_rollback(True)
            return self.form_invalid(form)

        if envoyer_identifiants_client(self.object, mot_de_passe, self._login_url()):
            messages.success(
                self.request,
                f"Client {self.object} enregistré — compte créé, identifiants envoyés à {self.object.email}.",
            )
        else:
            messages.warning(
                self.request,
                f"Client {self.object} et compte créés, mais l'e-mail n'a pas pu être envoyé. "
                f"Communiquez manuellement le mot de passe au client.",
            )
        return redirect(self.success_url)


class ModifierClientView(ComptableRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def _login_url(self):
        return self.request.build_absolute_uri(reverse('accounts:login'))

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        try:
            resultat = synchroniser_compte_client(self.object)
        except CompteClientError as exc:
            messages.error(self.request, str(exc))
            transaction.set_rollback(True)
            return self.form_invalid(form)

        if resultat:
            _, mot_de_passe = resultat
            if envoyer_identifiants_client(self.object, mot_de_passe, self._login_url()):
                messages.success(
                    self.request,
                    f"Client mis à jour — compte créé, identifiants envoyés à {self.object.email}.",
                )
            else:
                messages.warning(
                    self.request,
                    "Client mis à jour et compte créé, mais l'e-mail n'a pas pu être envoyé.",
                )
        else:
            messages.success(self.request, "Client et compte mis à jour.")
        return redirect(self.success_url)
