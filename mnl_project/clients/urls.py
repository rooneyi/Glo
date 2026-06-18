from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('',           views.ListeClientsView.as_view(),   name='list'),
    path('new/',       views.CreerClientView.as_view(),    name='create'),
    path('<int:pk>/edit/', views.ModifierClientView.as_view(), name='edit'),
]
