from django import forms
from contrats.models import ContratMouture
from .models import Reception


class ReceptionForm(forms.ModelForm):
    class Meta:
        model  = Reception
        fields = ['contrat', 'poids_brut_kg', 'poids_net_kg', 'observations']
        widgets = {
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Contrats éligibles : EN_ATTENTE ou EN_COURS sans réception existante
        qs = ContratMouture.objects.filter(
            statut__in=['EN_ATTENTE', 'EN_COURS']
        ).exclude(
            reception__isnull=False
        ).select_related('client').order_by('-date_contrat')
        self.fields['contrat'].queryset = qs
        self.fields['contrat'].empty_label = '— Choisir un contrat —'
        self.fields['contrat'].label_from_instance = (
            lambda c: (
                f"{c.numero_contrat} — {c.client} "
                f"({c.get_type_mouture_display()}, {c.quantite_kg:.0f} kg)"
            )
        )

    def clean(self):
        cd = super().clean()
        brut = cd.get('poids_brut_kg')
        net  = cd.get('poids_net_kg')
        if brut and net and net > brut:
            raise forms.ValidationError("Le poids net ne peut pas dépasser le poids brut.")
        return cd
