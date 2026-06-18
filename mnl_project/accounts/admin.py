from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model         = Utilisateur
    list_display  = ('email', 'nom', 'prenom', 'role', 'actif', 'date_joined')
    list_filter   = ('role', 'actif')
    search_fields = ('email', 'nom', 'prenom')
    ordering      = ('nom',)
    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Informations', {'fields': ('nom', 'prenom', 'telephone')}),
        ('Rôle & accès', {'fields': ('role', 'actif', 'is_staff', 'is_superuser')}),
        ('Dates',        {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('email', 'nom', 'prenom', 'role', 'password1', 'password2')}),
    )
