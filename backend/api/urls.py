from django.urls import path
from .views import RegisterView, LoginView, DashboardGestionnaireView

urlpatterns = [
    # Routes d'Authentification
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Routes Sécurisées (Exemples)
    path('dashboard/gestionnaire/', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
]
