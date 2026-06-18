from django.urls import path
from . import views

app_name = 'facturation'

urlpatterns = [
    path('bons/',                    views.ListeBonsRetraitView.as_view(),    name='bons_list'),
    path('bons/new/',                views.CreerBonRetraitView.as_view(),   name='bon_create'),
    path('bons/<int:pk>/',           views.DetailBonRetraitView.as_view(),  name='bon_detail'),
    path('bons/<int:pk>/pdf/',       views.ImprimerBonRetraitView.as_view(), name='bon_pdf'),
    path('alertes/',                 views.ListeAlertesView.as_view(),      name='alertes'),
    path('alertes/<int:pk>/lu/',     views.MarquerAlerteLuView.as_view(),   name='alerte_lu'),
    path('alertes/tout-lu/',         views.MarquerToutesLuesView.as_view(), name='alertes_tout_lu'),
    path('mes-retraits/',            views.MesRetraitsView.as_view(),       name='mes_retraits'),
]
