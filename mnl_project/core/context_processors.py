from facturation.models import Alerte


def alertes(request):
    if request.user.is_authenticated:
        count = Alerte.objects.filter(destinataire=request.user, lu=False).count()
        return {'alerte_count': count}
    return {'alerte_count': 0}
