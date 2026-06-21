from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from clients.models import Client


class Commande(models.Model):
    """Demande de mouture déposée par le client avant validation en contrat."""
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDEE',    'Validée'),
        ('REFUSEE',    'Refusée'),
        ('ANNULEE',    'Annulée'),
    ]

    numero_commande = models.CharField(max_length=25, unique=True, blank=True)
    date_commande   = models.DateField(auto_now_add=True)
    quantite_kg     = models.FloatField(help_text="Quantité de maïs demandée (kg)")
    statut          = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    observations    = models.TextField(blank=True)
    client          = models.ForeignKey(Client, on_delete=models.PROTECT,
                                        related_name='commandes')
    comptable       = models.ForeignKey(
        Utilisateur, on_delete=models.PROTECT,
        related_name='commandes_saisies', null=True, blank=True,
    )
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-date_commande']

    def __str__(self):
        return f"{self.numero_commande} — {self.client}"

    def save(self, *args, **kwargs):
        if not self.numero_commande:
            today = timezone.now().strftime('%Y%m%d')
            count = Commande.objects.filter(
                numero_commande__startswith=f'CMD-{today}'
            ).count()
            self.numero_commande = f'CMD-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)

    def valider(self, comptable):
        """Transforme la commande en contrat de mouture."""
        if self.statut != 'EN_ATTENTE':
            raise ValueError("Seule une commande en attente peut être validée.")
        if hasattr(self, 'contrat'):
            raise ValueError("Cette commande a déjà un contrat associé.")
        contrat = ContratMouture.objects.create(
            client=self.client,
            comptable=comptable,
            quantite_kg=self.quantite_kg,
            observations=self.observations,
            commande=self,
        )
        self.statut = 'VALIDEE'
        self.save(update_fields=['statut'])
        return contrat


class ContratMouture(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS',   'En cours'),
        ('TERMINE',    'Terminé'),
        ('ANNULE',     'Annulé'),
    ]
    TYPES_MOUTURE = [
        ('MOUTURE',         'Mouture'),
        ('MOUTURE_A_FACON', 'Mouture à façon'),
    ]

    numero_contrat  = models.CharField(max_length=25, unique=True, blank=True)
    date_contrat    = models.DateField(auto_now_add=True)
    quantite_kg     = models.FloatField(help_text="Quantité de maïs (kg)")
    type_mouture    = models.CharField(
        max_length=20, choices=TYPES_MOUTURE, default='MOUTURE',
        help_text="Type de mouture convenu avec le client",
    )
    statut          = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    observations    = models.TextField(blank=True)
    client          = models.ForeignKey(Client, on_delete=models.PROTECT,
                                        related_name='contrats')
    commande        = models.OneToOneField(
        Commande, on_delete=models.PROTECT,
        related_name='contrat', null=True, blank=True,
    )
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
