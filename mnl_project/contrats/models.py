from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from clients.models import Client


class ContratMouture(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS',   'En cours'),
        ('TERMINE',    'Terminé'),
        ('ANNULE',     'Annulé'),
    ]

    numero_contrat  = models.CharField(max_length=25, unique=True, blank=True)
    date_contrat    = models.DateField(auto_now_add=True)
    quantite_kg     = models.FloatField(help_text="Quantité de maïs (kg)")
    statut          = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    observations    = models.TextField(blank=True)
    client          = models.ForeignKey(Client, on_delete=models.PROTECT,
                                        related_name='contrats')
    comptable       = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                        related_name='contrats_saisis')
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contrat de mouture'
        ordering    = ['-date_contrat']

    def __str__(self):
        return f"{self.numero_contrat} — {self.client}"

    def save(self, *args, **kwargs):
        if not self.numero_contrat:
            today = timezone.now().strftime('%Y%m%d')
            count = ContratMouture.objects.filter(
                numero_contrat__startswith=f'CM-{today}'
            ).count()
            self.numero_contrat = f'CM-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)
