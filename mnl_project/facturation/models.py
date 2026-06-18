from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from clients.models import Client
from contrats.models import ContratMouture


class BonRetrait(models.Model):
    numero_bon      = models.CharField(max_length=25, unique=True, blank=True)
    date_retrait    = models.DateField()
    quantite_sacs   = models.IntegerField()
    facture_reglee  = models.BooleanField(default=False)
    contrat         = models.OneToOneField(ContratMouture, on_delete=models.PROTECT,
                                           related_name='bon_retrait')
    client          = models.ForeignKey(Client, on_delete=models.PROTECT,
                                        related_name='bons_retrait')
    comptable       = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                        related_name='bons_retrait_generes')
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bon de retrait'
        ordering    = ['-date_retrait']

    def __str__(self):
        return f"{self.numero_bon} — {self.client}"

    def save(self, *args, **kwargs):
        if not self.numero_bon:
            today = timezone.now().strftime('%Y%m%d')
            count = BonRetrait.objects.filter(
                numero_bon__startswith=f'BRT-{today}'
            ).count()
            self.numero_bon = f'BRT-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)


class Alerte(models.Model):
    TYPES = [
        ('RESULTAT_LABO',    'Résultat laboratoire disponible'),
        ('LIVRAISON_PRETE',  'Farine prête à retirer'),
        ('RETARD',           'Retard détecté'),
        ('ANOMALIE',         'Anomalie'),
    ]

    type            = models.CharField(max_length=25, choices=TYPES)
    message         = models.TextField()
    lu              = models.BooleanField(default=False)
    date_creation   = models.DateTimeField(auto_now_add=True)
    destinataire    = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,
                                        related_name='alertes')

    class Meta:
        verbose_name = 'Alerte'
        ordering    = ['-date_creation']

    def __str__(self):
        return f"[{self.get_type_display()}] → {self.destinataire}"
