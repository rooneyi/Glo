from django.contrib import admin
from .models import ContratMouture

@admin.register(ContratMouture)
class ContratMoutureAdmin(admin.ModelAdmin):
    list_display  = ('numero_contrat', 'client', 'quantite_kg', 'statut', 'date_contrat', 'comptable')
    list_filter   = ('statut', 'date_contrat')
    search_fields = ('numero_contrat', 'client__nom')
