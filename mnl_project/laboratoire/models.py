from django.db import models
from django.utils import timezone
from accounts.models import Utilisateur
from magasin.models import Reception


class Echantillon(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente — envoi à Likasi'),
        ('EN_COURS',   'En cours d\'analyse'),
        ('TESTE',      'Analysé'),
    ]

    numero_echantillon  = models.CharField(max_length=25, unique=True, blank=True)
    date_envoi_labo     = models.DateField()
    statut              = models.CharField(max_length=20, choices=STATUTS,
                                          default='EN_ATTENTE')
    reception           = models.OneToOneField(Reception, on_delete=models.CASCADE,
                                               related_name='echantillon')
    meunier             = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                            related_name='echantillons_envoyes')
    date_creation       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Échantillon'
        ordering    = ['-date_envoi_labo']

    def __str__(self):
        return self.numero_echantillon

    def save(self, *args, **kwargs):
        if not self.numero_echantillon:
            today = timezone.now().strftime('%Y%m%d')
            count = Echantillon.objects.filter(
                numero_echantillon__startswith=f'ECH-{today}'
            ).count()
            self.numero_echantillon = f'ECH-{today}-{count + 1:04d}'
        super().save(*args, **kwargs)


class ResultatLaboratoire(models.Model):
    date_analyse        = models.DateField()
    taux_humidite       = models.FloatField(help_text="Taux d'humidité (%)")
    taux_acidite        = models.FloatField(help_text="Taux d'acidité")
    taux_matiere_grasse = models.FloatField(help_text="Taux de matière grasse (%)")
    conforme            = models.BooleanField(default=False,
                                              help_text="Maïs conforme pour mouture ?")
    observations        = models.TextField(blank=True)
    echantillon         = models.OneToOneField(Echantillon, on_delete=models.CASCADE,
                                               related_name='resultat')
    laborantin          = models.ForeignKey(Utilisateur, on_delete=models.PROTECT,
                                            related_name='resultats_encodes')
    date_creation       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Résultat laboratoire'
        ordering    = ['-date_creation']

    def __str__(self):
        statut = "✓ Conforme" if self.conforme else "✗ Non conforme"
        return f"Résultat {self.echantillon} — {statut}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Met à jour le statut de l'échantillon
        self.echantillon.statut = 'TESTE'
        self.echantillon.save(update_fields=['statut'])
        # Crée une alerte pour le meunier
        from facturation.models import Alerte
        Alerte.objects.create(
            type='RESULTAT_LABO',
            message=(f"Résultat labo disponible pour {self.echantillon}. "
                     f"Maïs {'conforme' if self.conforme else 'NON conforme'}."),
            destinataire=self.echantillon.meunier,
        )
