from django.contrib import admin
from .models import Commande, ContratMouture


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display  = ('numero_commande', 'client', 'quantite_kg', 'statut', 'date_commande', 'comptable')
    list_filter   = ('statut', 'date_commande')
    search_fields = ('numero_commande', 'client__nom', 'client__prenom')


@admin.register(ContratMouture)
class ContratMoutureAdmin(admin.ModelAdmin):
    list_display  = ('numero_contrat', 'client', 'commande', 'quantite_kg', 'statut', 'date_contrat', 'comptable')
    list_filter   = ('statut', 'date_contrat')
    search_fields = ('numero_contrat', 'client__nom')
