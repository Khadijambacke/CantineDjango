from django.urls import path
from .views.auth_views import RegisterView, LoginView, LogoutView, MeView, VerifyOTPView, ResendOTPView
from .views.dashboard_views import DashboardGestionnaireView, ExportFacturationRHView, RechargerSoldeView
from .views.gestionnaire_views import GestionnaireEmployesView, GestionnaireEmployeDetailView, GestionnaireCommandesView
from .views.plat_views import PlatListCreateView, PlatDetailView
from .views.menu_views import MenuListCreateView, MenuStatsView, MenuDetailView
from .views.reservation_views import ReservationListCreateView, ReservationDetailView, ReservationQRCodeView
from .views.cuisinier_views import CuisinierMenusView, CuisinierReservationsView, CuisinierUpdateStatusView, CuisinierScanQRView, CuisinierEvaluationsView
from .views.notification_views import NotificationListView, NotificationMarkReadView, BroadcastNotificationView, MessageCuisinierView
from .views.evaluation_views import EvaluationCreateView

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
    path('menus/<int:pk>/', MenuDetailView.as_view(), name='menu-detail'),
    path('menus/stats/', MenuStatsView.as_view(), name='menus-stats'),
    
    # Routes des Réservations
    path('reservations/', ReservationListCreateView.as_view(), name='reservations-list'),
    path('reservations/<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
    path('reservations/<int:pk>/code-qr/', ReservationQRCodeView.as_view(), name='reservation-qr'),
    
    # Routes du Cuisinier
    path('cuisinier/menus/', CuisinierMenusView.as_view(), name='cuisinier-menus'),
    path('cuisinier/reservations/', CuisinierReservationsView.as_view(), name='cuisinier-reservations'),
    path('cuisinier/reservations/<int:pk>/update-status/', CuisinierUpdateStatusView.as_view(), name='cuisinier-update-status'),
    path('cuisinier/reservations/scan-qr/', CuisinierScanQRView.as_view(), name='cuisinier-scan-qr'),
    path('cuisinier/evaluations/', CuisinierEvaluationsView.as_view(), name='cuisinier-evaluations'),

    # Routes des Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/broadcast/', BroadcastNotificationView.as_view(), name='notification-broadcast'),
    path('notifications/message-cuisinier/', MessageCuisinierView.as_view(), name='message-cuisinier'),
    
    # Solde
    path('solde/recharger/', RechargerSoldeView.as_view(), name='recharger-solde'),

    # Routes Sécurisées Gestionnaire
    path('dashboard/gestionnaire/', DashboardGestionnaireView.as_view(), name='dashboard_gestionnaire'),
    path('dashboard/gestionnaire/export/', ExportFacturationRHView.as_view(), name='dashboard_export'),
    path('gestionnaire/employes/', GestionnaireEmployesView.as_view(), name='gest-employes'),
    path('gestionnaire/employes/<int:pk>/', GestionnaireEmployeDetailView.as_view(), name='gest-employe-detail'),
    path('gestionnaire/commandes/', GestionnaireCommandesView.as_view(), name='gest-commandes'),

    # Evaluations
    path('evaluations/', EvaluationCreateView.as_view(), name='evaluations-create'),
]
