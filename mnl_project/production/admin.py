from django.contrib import admin
from .models import Production, ProduitFini, StockFarine, BonCession, HistoriqueLot

@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display  = ('numero_production', 'contrat', 'quantite_farine_kg', 'statut', 'meunier', 'date_debut')
    list_filter   = ('statut',)

@admin.register(ProduitFini)
class ProduitFiniAdmin(admin.ModelAdmin):
    list_display = ('reference_lot', 'type_sac', 'nombre_sacs', 'statut_lot', 'production')

@admin.register(BonCession)
class BonCessionAdmin(admin.ModelAdmin):
    list_display = ('numero_bon', 'production', 'statut', 'meunier', 'magasinier', 'date_cession')

@admin.register(HistoriqueLot)
class HistoriqueLotAdmin(admin.ModelAdmin):
    list_display = ('produit_fini', 'type_evenement', 'date_evenement', 'auteur')
    list_filter = ('type_evenement',)

@admin.register(StockFarine)
class StockFarineAdmin(admin.ModelAdmin):
    list_display = ('type_farine', 'quantite_sacs', 'quantite_kg', 'date_maj')
