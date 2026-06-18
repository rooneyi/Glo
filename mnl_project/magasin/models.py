from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from contrats.models import ContratMouture


class Reception(models.Model):
    numero_bon      = models.CharField(max_length=25, unique=True, blank=True)
    date_reception  = models.DateField(auto_now_add=True)
    poids_brut_kg   = models.FloatField()
    poids_net_kg    = models.FloatField()
    observations    = models.TextField(blank=True)
    contrat         = models.OneToOneField(ContratMouture, on_delete=models.PROTECT,
                                           related_name='reception')
    magasinier      = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                        related_name='receptions')
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Réception'
        ordering    = ['-date_reception']

    def __str__(self):
        return f"{self.numero_bon} ({self.contrat.client})"

    def save(self, *args, **kwargs):
        if not self.numero_bon:
            today = timezone.now().strftime('%Y%m%d')
            count = Reception.objects.filter(
                numero_bon__startswith=f'BRC-{today}'
            ).count()
            self.numero_bon = f'BRC-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)


class StockMP(models.Model):
    """Suivi global du stock de matière première (maïs)."""
    quantite_disponible_kg  = models.FloatField(default=0)
    date_maj                = models.DateTimeField(auto_now=True)
    reception               = models.ForeignKey(Reception, on_delete=models.CASCADE,
                                                related_name='mouvements_stock')

    class Meta:
        verbose_name = 'Stock matière première'
        ordering    = ['-date_maj']

    def __str__(self):
        return f"Stock MP — {self.quantite_disponible_kg} kg"
