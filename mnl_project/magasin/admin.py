from django.contrib import admin
from .models import Reception, StockMP

@admin.register(Reception)
class ReceptionAdmin(admin.ModelAdmin):
    list_display  = ('numero_bon', 'contrat', 'poids_net_kg', 'date_reception', 'magasinier')
    search_fields = ('numero_bon', 'contrat__client__nom')

@admin.register(StockMP)
class StockMPAdmin(admin.ModelAdmin):
    list_display = ('quantite_disponible_kg', 'reception', 'date_maj')
