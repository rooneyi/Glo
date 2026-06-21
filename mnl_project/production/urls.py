from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('',                          views.ListeProductionsView.as_view(),    name='list'),
    path('new/',                       views.LancerProductionView.as_view(),  name='create'),
    path('<int:pk>/',                  views.DetailProductionView.as_view(),  name='detail'),
    path('<int:pk>/terminer/',         views.TerminerProductionView.as_view(), name='terminer'),
    path('<int:pk>/ensacher/',         views.AjouterProduitFiniView.as_view(), name='ensacher'),
    path('<int:pk>/bon-cession/',     views.GenererBonCessionView.as_view(), name='bon_cession'),
    path('lots/',                      views.ListeLotsView.as_view(),           name='lots_list'),
    path('lots/<int:pk>/historique/', views.HistoriqueLotView.as_view(),     name='historique_lot'),
    path('stock/',                     views.StockFarineView.as_view(),         name='stock_farine'),
]
