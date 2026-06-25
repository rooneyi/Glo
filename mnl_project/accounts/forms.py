from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from clients.models import Client
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
    profil_client = forms.ModelChoiceField(
        queryset=Client.objects.order_by('nom', 'prenom'),
        required=False,
        label='Fiche client liée',
        help_text='Obligatoire si le rôle est Client',
    )

    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role', 'profil_client']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer'

    def clean(self):
        data = super().clean()
        if data.get('role') == 'CLIENT' and not data.get('profil_client'):
            raise forms.ValidationError("Sélectionnez la fiche client pour un compte Client.")
        return data


class UtilisateurModifierForm(forms.ModelForm):
    profil_client = forms.ModelChoiceField(
        queryset=Client.objects.order_by('nom', 'prenom'),
        required=False,
        label='Fiche client liée',
    )

    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role', 'profil_client']
