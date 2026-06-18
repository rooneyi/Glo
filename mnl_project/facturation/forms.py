from django import forms
from django.db.models import Sum
from django.utils import timezone

from contrats.models import ContratMouture
from production.models import Production, StockFarine
from .models import BonRetrait


class BonRetraitForm(forms.ModelForm):
    class Meta:
        model = BonRetrait
        fields = ['contrat', 'date_retrait', 'quantite_sacs', 'facture_reglee']
        widgets = {
            'date_retrait': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        termines = Production.objects.filter(statut='TERMINE').values_list('contrat_id', flat=True)
        qs = ContratMouture.objects.filter(
            pk__in=termines,
        ).exclude(
            bon_retrait__isnull=False,
        ).select_related('client').order_by('-date_contrat')
        self.fields['contrat'].queryset = qs
        self.fields['contrat'].empty_label = '— Choisir un contrat (production terminée) —'
        if not self.instance.pk:
            self.fields['date_retrait'].initial = timezone.localdate()

    def clean_quantite_sacs(self):
        qte = self.cleaned_data['quantite_sacs']
        if qte <= 0:
            raise forms.ValidationError("La quantité doit être positive.")
        stock_sacs = StockFarine.objects.aggregate(total=Sum('quantite_sacs'))['total'] or 0
        if qte > stock_sacs:
            raise forms.ValidationError(
                f"Stock insuffisant : {stock_sacs} sac(s) disponible(s)."
            )
        return qte

    def clean(self):
        cd = super().clean()
        contrat = cd.get('contrat')
        if contrat and not cd.get('facture_reglee'):
            raise forms.ValidationError(
                "Le paiement doit être validé avant de générer le bon de retrait."
            )
        return cd
