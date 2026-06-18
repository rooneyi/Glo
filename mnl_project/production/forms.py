from django import forms
from django.utils import timezone

from contrats.models import ContratMouture
from laboratoire.models import ResultatLaboratoire
from .models import Production, ProduitFini


class ProductionLancerForm(forms.ModelForm):
    class Meta:
        model = Production
        fields = ['contrat', 'date_debut', 'quantite_traitee_kg']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'contrat': forms.Select(attrs={'class': 'form-input'}),
            'quantite_traitee_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        conformes = ResultatLaboratoire.objects.filter(conforme=True).values_list(
            'echantillon__reception__contrat_id', flat=True
        )
        qs = ContratMouture.objects.filter(
            pk__in=conformes,
            statut__in=['EN_COURS', 'EN_ATTENTE'],
        ).exclude(
            production__isnull=False,
        ).select_related('client').order_by('-date_contrat')
        self.fields['contrat'].queryset = qs
        self.fields['contrat'].empty_label = '— Choisir un contrat (maïs conforme) —'
        if not self.instance.pk:
            self.fields['date_debut'].initial = timezone.localdate()

    def clean_contrat(self):
        contrat = self.cleaned_data['contrat']
        try:
            resultat = contrat.reception.echantillon.resultat
        except Exception:
            raise forms.ValidationError("Ce contrat n'a pas de résultat de laboratoire conforme.")
        if not resultat.conforme:
            raise forms.ValidationError("Le maïs n'est pas conforme — mouture impossible.")
        return contrat


class ProductionTerminerForm(forms.ModelForm):
    class Meta:
        model = Production
        fields = ['date_fin', 'quantite_farine_kg', 'pertes_kg']
        widgets = {
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_fin'].initial = timezone.localdate()

    def clean(self):
        cd = super().clean()
        farine = cd.get('quantite_farine_kg', 0)
        pertes = cd.get('pertes_kg', 0)
        traite = self.instance.quantite_traitee_kg
        if farine + pertes > traite * 1.05:
            raise forms.ValidationError(
                "Farine + pertes ne peut pas dépasser sensiblement la quantité traitée."
            )
        return cd


class ProduitFiniForm(forms.ModelForm):
    class Meta:
        model = ProduitFini
        fields = ['type_sac', 'nombre_sacs', 'poids_total_kg']

    def clean(self):
        cd = super().clean()
        type_sac = cd.get('type_sac')
        nombre = cd.get('nombre_sacs')
        poids = cd.get('poids_total_kg')
        if type_sac and nombre and poids:
            attendu = 25 if type_sac == '25KG' else 50
            if abs(poids - nombre * attendu) > nombre * 2:
                raise forms.ValidationError(
                    f"Poids total incohérent avec {nombre} sac(s) de {attendu} kg."
                )
        return cd
