from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from contrats.models import ContratMouture


class Production(models.Model):
    STATUTS = [
        ('EN_COURS',  'En cours'),
        ('SUSPENDU',  'Suspendu'),
        ('TERMINE',   'Terminé'),
    ]

    numero_production       = models.CharField(max_length=25, unique=True, blank=True)
    date_debut              = models.DateField()
    date_fin                = models.DateField(null=True, blank=True)
    quantite_traitee_kg     = models.FloatField(help_text="Quantité de maïs traitée (kg)")
    quantite_farine_kg      = models.FloatField(default=0, help_text="Farine produite (kg)")
    pertes_kg               = models.FloatField(default=0, help_text="Pertes (son, déchets) (kg)")
    statut                  = models.CharField(max_length=20, choices=STATUTS,
                                               default='EN_COURS')
    contrat                 = models.OneToOneField(ContratMouture, on_delete=models.PROTECT,
                                                   related_name='production')
    meunier                 = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                                related_name='productions')
    date_creation           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Production (mouture)'
        ordering    = ['-date_debut']

    def __str__(self):
        return f"{self.numero_production} ({self.contrat.client})"

    def save(self, *args, **kwargs):
        if not self.numero_production:
            today = timezone.now().strftime('%Y%m%d')
            count = Production.objects.filter(
                numero_production__startswith=f'PROD-{today}'
            ).count()
            self.numero_production = f'PROD-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)

    @property
    def rendement_pct(self):
        if self.quantite_traitee_kg:
            return round(self.quantite_farine_kg / self.quantite_traitee_kg * 100, 1)
        return 0


class ProduitFini(models.Model):
    TYPES_SAC = [
        ('25KG', 'Sac 25 kg'),
        ('50KG', 'Sac 50 kg'),
    ]
    STATUTS_LOT = [
        ('EN_ATTENTE', 'En attente validation'),
        ('VALIDE',     'Validé'),
    ]

    type_sac        = models.CharField(max_length=5, choices=TYPES_SAC)
    nombre_sacs     = models.IntegerField()
    poids_total_kg  = models.FloatField()
    reference_lot   = models.CharField(max_length=30, blank=True)
    statut_lot      = models.CharField(max_length=20, choices=STATUTS_LOT,
                                       default='EN_ATTENTE')
    date_ensachage  = models.DateField(auto_now_add=True)
    production      = models.ForeignKey(Production, on_delete=models.CASCADE,
                                        related_name='produits_finis')

    class Meta:
        verbose_name = 'Produit fini (sac de farine)'
        ordering    = ['-date_ensachage']

    def __str__(self):
        return f"{self.nombre_sacs} × {self.get_type_sac_display()} — {self.production}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.reference_lot:
            today = timezone.now().strftime('%Y%m%d')
            self.reference_lot = f'LOT-{today}-{self.production.numero_production}'
        super().save(*args, **kwargs)
        if is_new:
            HistoriqueLot.objects.create(
                produit_fini=self,
                type_evenement='ENSACHAGE',
                description=(
                    f"Ensachage : {self.nombre_sacs} sac(s) "
                    f"{self.get_type_sac_display()} — lot {self.reference_lot}"
                ),
                quantite_sacs=self.nombre_sacs,
                quantite_kg=self.poids_total_kg,
            )


class BonCession(models.Model):
    """Bon de cession produits finis : meunier → magasinier."""
    STATUTS = [
        ('EN_ATTENTE', 'En attente magasinier'),
        ('RECU',       'Reçu par le magasinier'),
    ]

    numero_bon      = models.CharField(max_length=25, unique=True, blank=True)
    date_cession    = models.DateField(auto_now_add=True)
    nombre_sacs_25  = models.IntegerField(default=0)
    nombre_sacs_50  = models.IntegerField(default=0)
    poids_total_kg  = models.FloatField(default=0)
    statut          = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    observations    = models.TextField(blank=True)
    production      = models.OneToOneField(Production, on_delete=models.PROTECT,
                                           related_name='bon_cession')
    meunier         = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                        related_name='bons_cession_emis')
    magasinier      = models.ForeignKey(
        Utilisateur, on_delete=models.PROTECT,
        related_name='bons_cession_recus', null=True, blank=True,
    )
    date_reception  = models.DateTimeField(null=True, blank=True)
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bon de cession produits finis'
        ordering = ['-date_cession']

    def __str__(self):
        return f"{self.numero_bon} — {self.production.numero_production}"

    def save(self, *args, **kwargs):
        if not self.numero_bon:
            today = timezone.now().strftime('%Y%m%d')
            count = BonCession.objects.filter(
                numero_bon__startswith=f'BCPF-{today}'
            ).count()
            self.numero_bon = f'BCPF-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)


class HistoriqueLot(models.Model):
    """Historique complet d'un lot de farine."""
    TYPES = [
        ('CREATION',   'Création'),
        ('ANALYSE',    'Analyse laboratoire'),
        ('MOUTURE',    'Mouture'),
        ('ENSACHAGE',  'Ensachage'),
        ('CESSION',    'Bon de cession'),
        ('VALIDATION', 'Validation magasin'),
        ('NOTIFICATION', 'Notification client'),
        ('RETRAIT',    'Retrait client'),
    ]

    produit_fini    = models.ForeignKey(ProduitFini, on_delete=models.CASCADE,
                                        related_name='historique')
    type_evenement  = models.CharField(max_length=20, choices=TYPES)
    description     = models.TextField()
    quantite_sacs   = models.IntegerField(null=True, blank=True)
    quantite_kg     = models.FloatField(null=True, blank=True)
    auteur          = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='evenements_lot',
    )
    date_evenement  = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Historique lot'
        verbose_name_plural = 'Historiques lots'
        ordering = ['date_evenement']

    def __str__(self):
        return f"{self.produit_fini.reference_lot} — {self.get_type_evenement_display()}"


class StockFarine(models.Model):
    type_farine     = models.CharField(max_length=50, default='Farine de maïs')
    quantite_sacs   = models.IntegerField(default=0)
    quantite_kg     = models.FloatField(default=0)
    date_maj        = models.DateTimeField(auto_now=True)
    produit_fini    = models.ForeignKey(ProduitFini, on_delete=models.CASCADE,
                                        related_name='entrees_stock')

    class Meta:
        verbose_name = 'Stock farine'
        ordering    = ['-date_maj']

    def __str__(self):
        return f"Stock farine — {self.quantite_sacs} sacs ({self.quantite_kg} kg)"
