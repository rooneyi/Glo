from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from .forms import ConnexionForm, UtilisateurCreerForm, UtilisateurModifierForm
from .models import Utilisateur


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            messages.error(request, "Accès réservé à l'administrateur.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


# ── Auth ─────────────────────────────────────────────────────────────────────

class ConnexionView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return render(request, self.template_name, {'form': ConnexionForm()})

    def post(self, request):
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.actif:
                messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                return render(request, self.template_name, {'form': form})
            login(request, user)
            return redirect(request.GET.get('next', 'core:dashboard'))
        return render(request, self.template_name, {'form': form})


class DeconnexionView(View):
    def post(self, request):
        logout(request)
        return redirect('accounts:login')

    def get(self, request):
        logout(request)
        return redirect('accounts:login')


# ── Utilisateurs (Admin) ──────────────────────────────────────────────────────

class ListeUtilisateursView(AdminRequiredMixin, View):
    def get(self, request):
        qs = Utilisateur.objects.all().order_by('nom', 'prenom')
        q = request.GET.get('q', '').strip()
        role = request.GET.get('role', '').strip()
        if q:
            qs = qs.filter(nom__icontains=q) | qs.filter(prenom__icontains=q) | qs.filter(email__icontains=q)
        if role:
            qs = qs.filter(role=role)
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'accounts/users/list.html', {
            'page_obj': page_obj,
            'roles': Utilisateur.ROLES,
        })


class CreerUtilisateurView(AdminRequiredMixin, CreateView):
    model = Utilisateur
    form_class = UtilisateurCreerForm
    template_name = 'accounts/users/form.html'
    success_url = reverse_lazy('accounts:users_list')

    def form_valid(self, form):
        messages.success(self.request, f"Utilisateur {form.instance.get_full_name()} créé avec succès.")
        return super().form_valid(form)


class ModifierUtilisateurView(AdminRequiredMixin, UpdateView):
    model = Utilisateur
    form_class = UtilisateurModifierForm
    template_name = 'accounts/users/form.html'
    success_url = reverse_lazy('accounts:users_list')

    def form_valid(self, form):
        messages.success(self.request, "Modifications enregistrées.")
        return super().form_valid(form)


class ToggleActifView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        if user.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        else:
            user.actif = not user.actif
            user.save(update_fields=['actif'])
            etat = "activé" if user.actif else "désactivé"
            messages.success(request, f"Compte de {user.get_full_name()} {etat}.")
        return redirect('accounts:users_list')
