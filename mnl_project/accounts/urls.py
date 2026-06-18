from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',         views.ConnexionView.as_view(),         name='login'),
    path('logout/',        views.DeconnexionView.as_view(),        name='logout'),
    path('users/',         views.ListeUtilisateursView.as_view(),  name='users_list'),
    path('users/new/',     views.CreerUtilisateurView.as_view(),   name='user_create'),
    path('users/<int:pk>/edit/',   views.ModifierUtilisateurView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle/', views.ToggleActifView.as_view(),         name='user_toggle'),
]
