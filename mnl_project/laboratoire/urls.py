from django.urls import path
from . import views

app_name = 'laboratoire'

urlpatterns = [
    path('echantillons/',      views.ListeEchantillonsView.as_view(), name='echantillons_list'),
    path('echantillons/new/',  views.CreerEchantillonView.as_view(),  name='echantillon_create'),
    path('resultats/',         views.ListeResultatsView.as_view(),    name='resultats_list'),
    path('resultats/new/',     views.EncoderResultatView.as_view(),   name='resultat_create'),
]
