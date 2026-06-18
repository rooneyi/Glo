from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'prenom', 'telephone', 'email', 'date_enregistrement')
    search_fields = ('nom', 'prenom', 'telephone')
    list_filter   = ('date_enregistrement',)
