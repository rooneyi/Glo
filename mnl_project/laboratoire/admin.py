from django.contrib import admin
from .models import Echantillon, ResultatLaboratoire

@admin.register(Echantillon)
class EchantillonAdmin(admin.ModelAdmin):
    list_display  = ('numero_echantillon', 'reception', 'statut', 'date_envoi_labo', 'meunier')
    list_filter   = ('statut',)

@admin.register(ResultatLaboratoire)
class ResultatLaboratoireAdmin(admin.ModelAdmin):
    list_display  = ('echantillon', 'taux_humidite', 'taux_acidite', 'conforme', 'laborantin', 'date_analyse')
    list_filter   = ('conforme',)
