from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from contrats.models import ContratMouture
from facturation.models import BonRetrait, NotificationClient

from .historique_client import historique_client


class ClientRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.role != 'CLIENT':
            messages.error(request, "Accès réservé aux clients.")
            return redirect('core:dashboard')
        if not user.profil_client_id:
            messages.error(request, "Votre compte n'est pas lié à une fiche client. Contactez l'administration.")
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class EspaceClientView(ClientRequiredMixin, View):
    """Espace client : notifications, suivi commandes, historique retraits."""

    def get(self, request):
        client = request.user.profil_client
        non_lues = NotificationClient.objects.filter(client=client, lu=False).count()
        notifications = NotificationClient.objects.filter(client=client).select_related(
            'contrat', 'magasinier',
        ).order_by('-date_creation')[:30]

        contrats = ContratMouture.objects.filter(
            client=client,
        ).select_related('production').order_by('-date_contrat')[:15]

        retraits = BonRetrait.objects.filter(
            contrat__client=client,
        ).select_related('contrat').order_by('-date_retrait')[:20]

        historique = historique_client(client)

        onglets_valides = {'notifications', 'commandes', 'retraits'}
        onglet = request.GET.get('onglet', 'notifications')
        if onglet not in onglets_valides:
            onglet = 'notifications'

        return render(request, 'clients/espace.html', {
            'client': client,
            'notifications': notifications,
            'non_lues': non_lues,
            'contrats': contrats,
            'retraits': retraits,
            'historique': historique,
            'onglet': onglet,
        })


class MarquerNotificationClientLuView(ClientRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(
            NotificationClient, pk=pk, client=request.user.profil_client,
        )
        notif.lu = True
        notif.save(update_fields=['lu'])
        return redirect(f"{reverse('clients:espace')}?onglet=notifications")


class MarquerToutesNotificationsLuesView(ClientRequiredMixin, View):
    def post(self, request):
        NotificationClient.objects.filter(
            client=request.user.profil_client, lu=False,
        ).update(lu=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect(f"{reverse('clients:espace')}?onglet=notifications")
