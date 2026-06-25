from django.urls import path
from . import views

app_name = 'magasin'

urlpatterns = [
    path('receptions/',              views.ListeReceptionsView.as_view(),   name='receptions_list'),
    path('receptions/new/',          views.CreerReceptionView.as_view(),    name='reception_create'),
    path('receptions/<int:pk>/',     views.DetailReceptionView.as_view(),   name='reception_detail'),
    path('receptions/<int:pk>/pdf/', views.ImprimerBonReceptionView.as_view(), name='reception_pdf'),
    path('stock/',                   views.StockMPView.as_view(),           name='stock'),
    path('bons-cession/',            views.ListeBonsCessionView.as_view(),  name='bons_cession_list'),
    path('bons-cession/<int:pk>/recevoir/', views.RecevoirBonCessionView.as_view(), name='bon_cession_recevoir'),
    path('bons-cession/<int:pk>/notifier-client/', views.SignalerPretClientView.as_view(), name='bon_cession_notifier'),
]
