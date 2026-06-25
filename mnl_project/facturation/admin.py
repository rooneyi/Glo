from django.contrib import admin
from .models import BonRetrait, Alerte, NotificationClient

@admin.register(BonRetrait)
class BonRetraitAdmin(admin.ModelAdmin):
    list_display  = ('numero_bon', 'client', 'quantite_sacs', 'facture_reglee', 'date_retrait', 'comptable')
    list_filter   = ('facture_reglee',)

@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display  = ('type', 'destinataire', 'lu', 'date_creation')
    list_filter   = ('type', 'lu')

@admin.register(NotificationClient)
class NotificationClientAdmin(admin.ModelAdmin):
    list_display = ('type', 'client', 'lu', 'magasinier', 'date_creation')
    list_filter = ('type', 'lu')
