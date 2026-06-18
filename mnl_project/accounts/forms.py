from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Utilisateur


class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'autofocus': True}),
        label='Adresse e-mail',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label='Mot de passe',
    )
    error_messages = {
        'invalid_login': "E-mail ou mot de passe incorrect.",
        'inactive': "Ce compte est désactivé.",
    }


class UtilisateurCreerForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer'


class UtilisateurModifierForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role']
