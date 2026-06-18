from django import forms
from accounts.models import Utilisateur
from magasin.models import Reception
from .models import Echantillon, ResultatLaboratoire

# Seuils de conformité MNL
SEUIL_HUMIDITE_MAX    = 14.0
SEUIL_ACIDITE_MAX     = 0.05
SEUIL_MAT_GRASSE_MAX  = 5.0


class EchantillonForm(forms.ModelForm):
    class Meta:
        model  = Echantillon
        fields = ['reception', 'meunier', 'date_envoi_labo']
        widgets = {
            'date_envoi_labo': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Réceptions sans échantillon
        qs = Reception.objects.filter(echantillon__isnull=True).select_related('contrat__client')
        self.fields['reception'].queryset = qs
        self.fields['reception'].empty_label = '— Choisir une réception —'
        # Seulement les Meuniers
        self.fields['meunier'].queryset = Utilisateur.objects.filter(role='MEUNIER', actif=True)
        self.fields['meunier'].empty_label = '— Choisir un meunier —'


class ResultatLaboratoireForm(forms.ModelForm):
    class Meta:
        model  = ResultatLaboratoire
        fields = ['echantillon', 'date_analyse', 'taux_humidite',
                  'taux_acidite', 'taux_matiere_grasse', 'observations']
        widgets = {
            'date_analyse': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Échantillons sans résultat et non encore testés
        qs = Echantillon.objects.filter(
            resultat__isnull=True
        ).exclude(statut='TESTE').select_related('reception__contrat__client')
        self.fields['echantillon'].queryset = qs
        self.fields['echantillon'].empty_label = '— Choisir un échantillon —'

    def clean(self):
        cd = super().clean()
        # Calcul automatique de la conformité
        h  = cd.get('taux_humidite')
        a  = cd.get('taux_acidite')
        mg = cd.get('taux_matiere_grasse')
        if h is not None and a is not None and mg is not None:
            cd['conforme'] = (
                h  <= SEUIL_HUMIDITE_MAX and
                a  <= SEUIL_ACIDITE_MAX  and
                mg <= SEUIL_MAT_GRASSE_MAX
            )
        return cd

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.conforme = self.cleaned_data.get('conforme', False)
        if commit:
            obj.save()
        return obj
