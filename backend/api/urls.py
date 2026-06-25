from django.urls import path
from .views.auth_views import RegisterView, LoginView, LogoutView, MeView, VerifyOTPView, ResendOTPView
from .views.dashboard_views import DashboardGestionnaireView
from .views.plat_views import PlatListCreateView, PlatDetailView
from .views.menu_views import MenuListCreateView, MenuStatsView
from .views.reservation_views import ReservationListCreateView, ReservationDetailView
from .views.cuisinier_views import CuisinierMenusView, CuisinierReservationsView, CuisinierUpdateStatusView
from .views.notification_views import NotificationListView, NotificationMarkReadView

urlpatterns = [
    # Routes d'Authentification
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Routes des Plats (Repas)
    path('plats/', PlatListCreateView.as_view(), name='plats-list'),
    path('plats/<int:pk>/', PlatDetailView.as_view(), name='plat-detail'),

    # Routes des Menus du Jour (Planning)
    path('menus/', MenuListCreateView.as_view(), name='menus-list'),
    path('menus/stats/', MenuStatsView.as_view(), name='menus-stats'),
    
    # Routes des Réservations
    path('reservations/', ReservationListCreateView.as_view(), name='reservations-list'),
    path('reservations/<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
    
    # Routes du Cuisinier
    path('cuisinier/menus/', CuisinierMenusView.as_view(), name='cuisinier-menus'),
    path('cuisinier/reservations/', CuisinierReservationsView.as_view(), name='cuisinier-reservations'),
    path('cuisinier/reservations/<int:pk>/update-status/', CuisinierUpdateStatusView.as_view(), name='cuisinier-update-status'),

    # Routes des Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    
    # Routes Sécurisées (Exemples)
    path('dashboard/gestionnaire/', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
]
