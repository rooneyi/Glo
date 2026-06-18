from django.db import models
from accounts.models import Utilisateur


class Client(models.Model):
    nom                  = models.CharField(max_length=100)
    prenom               = models.CharField(max_length=100)
    telephone            = models.CharField(max_length=20)
    adresse              = models.TextField(blank=True)
    email                = models.EmailField(blank=True)
    date_enregistrement  = models.DateField(auto_now_add=True)
    enregistre_par       = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name='clients_enregistres'
    )

    class Meta:
        verbose_name = 'Client'
        ordering    = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom}"
