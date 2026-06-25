from facturation.models import Alerte, NotificationClient


def alertes(request):
    if not request.user.is_authenticated:
        return {'alerte_count': 0, 'client_notification_count': 0}

    if request.user.role == 'CLIENT' and request.user.profil_client_id:
        count = NotificationClient.objects.filter(
            client=request.user.profil_client, lu=False,
        ).count()
        return {'alerte_count': count, 'client_notification_count': count}

    count = Alerte.objects.filter(destinataire=request.user, lu=False).count()
    return {'alerte_count': count, 'client_notification_count': 0}
