from django.urls import path
from .views import RegisterView, LoginView, DashboardGestionnaireView, LogoutView, MeView

urlpatterns = [
    # Routes d'Authentification
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    
    # Routes Sécurisées (Exemples)
    path('dashboard/gestionnaire/', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
]
