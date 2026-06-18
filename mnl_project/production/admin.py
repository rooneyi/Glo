from django.contrib import admin
from .models import Production, ProduitFini, StockFarine

@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display  = ('numero_production', 'contrat', 'quantite_farine_kg', 'statut', 'meunier', 'date_debut')
    list_filter   = ('statut',)

@admin.register(ProduitFini)
class ProduitFiniAdmin(admin.ModelAdmin):
    list_display = ('reference_lot', 'type_sac', 'nombre_sacs', 'poids_total_kg', 'production')

@admin.register(StockFarine)
class StockFarineAdmin(admin.ModelAdmin):
    list_display = ('type_farine', 'quantite_sacs', 'quantite_kg', 'date_maj')
