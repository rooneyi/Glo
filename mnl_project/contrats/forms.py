from django import forms
from .models import ContratMouture
from clients.models import Client


class ContratMoutureForm(forms.ModelForm):
    class Meta:
        model = ContratMouture
        fields = ['client', 'quantite_kg', 'type_mouture', 'statut', 'observations']
        widgets = {
            'observations': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.all().order_by('nom', 'prenom')
        self.fields['client'].empty_label = '— Choisir un client —'
        self.fields['type_mouture'].widget = forms.Select(
            attrs={'class': 'form-input'},
        )
        self.fields['type_mouture'].initial = (
            self.instance.type_mouture if self.instance.pk else 'MOUTURE'
        )
        # À la création, le statut est EN_ATTENTE par défaut (pas affiché dans le formulaire)
        if not self.instance.pk:
            self.fields.pop('statut', None)
