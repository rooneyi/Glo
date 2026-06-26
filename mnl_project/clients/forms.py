from django import forms
from django.core.exceptions import ValidationError

from accounts.models import Utilisateur

from .compte_client import email_deja_utilise
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'telephone', 'adresse', 'email']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'email': forms.EmailInput(attrs={'placeholder': 'jean@example.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].help_text = (
            "Un compte espace client sera créé automatiquement et les identifiants "
            "seront envoyés à cette adresse."
        )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise ValidationError("L'e-mail est obligatoire pour l'accès espace client.")

        exclure_id = None
        if self.instance.pk:
            lie = Utilisateur.objects.filter(profil_client_id=self.instance.pk).first()
            if lie:
                exclure_id = lie.pk

        if email_deja_utilise(email, exclure_utilisateur_id=exclure_id):
            raise ValidationError("Cet e-mail est déjà utilisé par un autre compte.")
        return email
