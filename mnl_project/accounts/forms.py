from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from clients.models import Client

from .models import Utilisateur


def clients_disponibles_pour_liaison(utilisateur: Utilisateur | None = None):
    """Clients sans compte, ou le client déjà lié à l'utilisateur en cours d'édition."""
    qs = Client.objects.order_by('nom', 'prenom')
    deja_lies = Utilisateur.objects.filter(
        profil_client__isnull=False,
        role='CLIENT',
    )
    if utilisateur and utilisateur.pk:
        deja_lies = deja_lies.exclude(pk=utilisateur.pk)
    ids_pris = deja_lies.values_list('profil_client_id', flat=True)
    return qs.exclude(pk__in=ids_pris)


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


class _ProfilClientMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        utilisateur = self.instance if getattr(self.instance, 'pk', None) else None
        self.fields['profil_client'].queryset = clients_disponibles_pour_liaison(utilisateur)
        self.fields['profil_client'].required = False

    def clean_profil_client(self):
        profil = self.cleaned_data.get('profil_client')
        if not profil:
            return None

        conflit = Utilisateur.objects.filter(profil_client=profil, role='CLIENT')
        if self.instance.pk:
            conflit = conflit.exclude(pk=self.instance.pk)
        if conflit.exists():
            compte = conflit.first()
            raise forms.ValidationError(
                f"Ce client a déjà un compte ({compte.email}). "
                "Les comptes client sont créés automatiquement lors de l'enregistrement du client."
            )
        return profil

    def clean(self):
        data = super().clean()
        role = data.get('role')
        profil = data.get('profil_client')

        if role == 'CLIENT':
            if not profil:
                raise forms.ValidationError(
                    "Sélectionnez la fiche client pour un compte Client, "
                    "ou créez le client depuis le menu Clients (compte auto)."
                )
        else:
            if profil:
                raise forms.ValidationError(
                    "La fiche client liée ne s'applique qu'au rôle Client."
                )
            data['profil_client'] = None
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role != 'CLIENT':
            user.profil_client = None
        if commit:
            user.save()
        return user


class UtilisateurCreerForm(_ProfilClientMixin, UserCreationForm):
    profil_client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        required=False,
        label='Fiche client liée',
        help_text='Uniquement pour le rôle Client — compte créé auto à l\'enregistrement client',
    )

    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role', 'profil_client']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer'


class UtilisateurModifierForm(_ProfilClientMixin, forms.ModelForm):
    profil_client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        required=False,
        label='Fiche client liée',
    )

    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'email', 'telephone', 'role', 'profil_client']
