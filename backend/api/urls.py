from django.urls import path
from .views import (
    RegisterView, LoginView, VerifyOTPView, ResendOTPView,
    MenuListCreateView, MenuStatsView,
    ReservationListCreateView, ReservationDetailView,
    CuisinierMenusView, CuisinierReservationsView, CuisinierUpdateStatusView,
    DashboardGestionnaireView, NotificationListView, NotificationMarkReadView
)

urlpatterns = [
    # Routes d'Authentification
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Routes des Menus du Jour (Planning)
    path('menus/', MenuListCreateView.as_view(), name='menus-list'),
    path('menus/stats/', MenuStatsView.as_view(), name='menus-stats'),
    
    # Routes des Réservations
    path('reservations/', ReservationListCreateView.as_view(), name='reservations-list'),
    path('reservations/<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
    
    # Routes du Cuisinier (Équivalent Médecin)
    path('cuisinier/menus/', CuisinierMenusView.as_view(), name='cuisinier-menus'),
    path('cuisinier/reservations/', CuisinierReservationsView.as_view(), name='cuisinier-reservations'),
    path('cuisinier/reservations/<int:pk>/update-status/', CuisinierUpdateStatusView.as_view(), name='cuisinier-update-status'),

    # Routes des Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    
    # Routes Sécurisées (Exemples)
    path('dashboard/gestionnaire/', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
]
