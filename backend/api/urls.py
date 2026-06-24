from django.urls import path
from .views.auth_views import RegisterView, LoginView, LogoutView, MeView
from .views.dashboard_views import DashboardGestionnaireView
from .views.plat_views import PlatListCreateView, PlatDetailView

urlpatterns = [
    # Routes d'Authentification
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('me', MeView.as_view(), name='me'),
    
    # Routes des Plats (Repas)
    path('plats', PlatListCreateView.as_view(), name='plats-list'),
    path('plats/<int:pk>', PlatDetailView.as_view(), name='plat-detail'),
    
    # Routes Sécurisées (Exemples)
    path('dashboard/gestionnaire', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
]
