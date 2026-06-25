from django.urls import path
from . import views
from . import portal_views

app_name = 'clients'

urlpatterns = [
    path('',           views.ListeClientsView.as_view(),   name='list'),
    path('new/',       views.CreerClientView.as_view(),    name='create'),
    path('<int:pk>/edit/', views.ModifierClientView.as_view(), name='edit'),
    path('espace/',    portal_views.EspaceClientView.as_view(), name='espace'),
    path('espace/notifications/<int:pk>/lu/', portal_views.MarquerNotificationClientLuView.as_view(), name='notification_lu'),
    path('espace/notifications/tout-lu/', portal_views.MarquerToutesNotificationsLuesView.as_view(), name='notifications_tout_lu'),
]
