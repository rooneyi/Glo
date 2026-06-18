from django.urls import path
from . import views

app_name = 'contrats'

urlpatterns = [
    path('',              views.ListeContratsView.as_view(), name='list'),
    path('new/',          views.CreerContratView.as_view(),  name='create'),
    path('<int:pk>/edit/', views.ModifierContratView.as_view(), name='edit'),
]
