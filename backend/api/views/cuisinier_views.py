from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import MenuJour, Reservation, Notification
from ..serializers import MenuJourSerializer, ReservationSerializer, StatutUpdateSerializer
from ..permissions import IsCuisinier

class CuisinierMenusView(APIView):
    """
    GET /api/cuisinier/menus - Liste tous les menus programmés de la cantine (le personnel gère tout globalement)
    """
    permission_classes = [IsAuthenticated, IsCuisinier]
    serializer_class = MenuJourSerializer

    @extend_schema(
        summary="Liste de tous les menus de la cantine",
        operation_id="cuisinier_menus",
        responses={200: MenuJourSerializer(many=True)}
    )
    def get(self, request):
        menus = MenuJour.objects.all().order_by('-date_menu')
        return Response({
            'message': 'Tous les menus programmés.',
            'data': MenuJourSerializer(menus, many=True).data
        })

class CuisinierReservationsView(APIView):
    """
    GET /api/cuisinier/reservations - Liste toutes les réservations d'employés de la cantine (gérées en équipe par la cuisine)
    """
    permission_classes = [IsAuthenticated, IsCuisinier]
    serializer_class = ReservationSerializer

    @extend_schema(
        summary="Liste de toutes les réservations de la cantine",
        operation_id="cuisinier_reservations",
        responses={200: ReservationSerializer(many=True)}
    )
    def get(self, request):
        reservations = (
            Reservation.objects
            .select_related('employe', 'menu_jour', 'menu_jour__plat')
            .order_by('-date_reservation')
        )
        return Response({
            'message': 'Toutes les réservations de la cantine.',
            'data': ReservationSerializer(reservations, many=True).data
        })

class CuisinierUpdateStatusView(APIView):
    """
    POST /api/cuisinier/reservations/<id>/update-status - Mettre à jour le statut de n'importe quelle réservation
    """
    permission_classes = [IsAuthenticated, IsCuisinier]
    serializer_class = StatutUpdateSerializer

    @extend_schema(
        summary="Mettre à jour le statut d'une réservation (Cuisine)",
        operation_id="cuisinier_update_status",
        request=StatutUpdateSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request, pk):
        # Valider le nouveau statut
        serializer = StatutUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'message': 'Erreur de validation.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer la réservation
        try:
            reservation = Reservation.objects.select_related('employe', 'menu_jour', 'menu_jour__plat').get(pk=pk)
        except Reservation.DoesNotExist:
            return Response({
                'message': 'Réservation introuvable.'
            }, status=status.HTTP_404_NOT_FOUND)

        new_statut = serializer.validated_data['statut']
        old_statut = reservation.statut

        if old_statut == new_statut:
            return Response({
                'message': f"La réservation a déjà le statut {new_statut}."
            }, status=status.HTTP_400_BAD_REQUEST)

        if old_statut == 'annule':
            return Response({
                'message': "Impossible de modifier une réservation déjà annulée."
            }, status=status.HTTP_400_BAD_REQUEST)

        from django.db import transaction
        employe = reservation.employe
        menu_jour = reservation.menu_jour
        prix_repas = menu_jour.prix
        mode_paiement = employe.mode_paiement

        with transaction.atomic():
            reservation.statut = new_statut
            reservation.save()

            # 1. Si le cuisinier annule la réservation, rembourser le solde
            if new_statut == 'annule' and mode_paiement == 'solde':
                employe.solde += prix_repas
                employe.save()

            # 2. Envoyer une notification appropriée à l'employé
            titre_notif = ""
            msg_notif = ""

            if new_statut == 'annule':
                titre_notif = "Réservation annulée par la cuisine"
                msg_remboursement = f" Votre compte a été recrédité de {prix_repas} CFA. Nouveau solde : {employe.solde} CFA." if mode_paiement == 'solde' else ""
                msg_notif = f"Votre réservation pour le plat '{menu_jour.plat.libelle}' du {menu_jour.date_menu} a été annulée par l'équipe de cuisine.{msg_remboursement}"
            elif new_statut == 'prepare':
                titre_notif = "Votre repas est prêt !"
                msg_notif = f"Votre portion de '{menu_jour.plat.libelle}' du {menu_jour.date_menu} est prête. Venez la récupérer !"
            elif new_statut == 'consomme':
                titre_notif = "Repas consommé / livré"
                msg_notif = f"Votre réservation pour le plat '{menu_jour.plat.libelle}' du {menu_jour.date_menu} a été marquée comme consommée. Bon appétit !"

            if titre_notif and msg_notif:
                Notification.objects.create(
                    user=employe,
                    titre=titre_notif,
                    message=msg_notif
                )

        return Response({
            'message': f"Statut mis à jour : {reservation.statut}.",
            'data': ReservationSerializer(reservation).data
        })

class CuisinierScanQRView(APIView):
    """
    POST /api/cuisinier/reservations/scan-qr/ - Mettre à jour une réservation via scan du code QR (UUID)
    """
    permission_classes = [IsAuthenticated, IsCuisinier]

    @extend_schema(
        summary="Scanner un QR Code pour valider une réservation",
        operation_id="cuisinier_scan_qr",
        request=OpenApiTypes.OBJECT,  # attend {"code_qr": "uuid..."}
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        code_qr = request.data.get('code_qr')
        if not code_qr:
            return Response({
                'message': 'Le code QR (UUID) est requis.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            reservation = Reservation.objects.select_related('employe', 'menu_jour', 'menu_jour__plat').get(code_qr=code_qr)
        except Reservation.DoesNotExist:
            return Response({
                'message': 'Réservation introuvable pour ce QR Code.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Si la réservation est déjà annulée ou consommée
        if reservation.statut in ['annule', 'consomme']:
            return Response({
                'message': f"Cette réservation est déjà dans le statut : {reservation.statut}."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        from django.db import transaction
        employe = reservation.employe
        menu_jour = reservation.menu_jour
        
        with transaction.atomic():
            reservation.statut = 'consomme'
            reservation.save()
            
            Notification.objects.create(
                user=employe,
                titre="Repas consommé / livré",
                message=f"Votre réservation pour le plat '{menu_jour.plat.libelle}' du {menu_jour.date_menu} a été scannée et marquée comme consommée. Bon appétit !"
            )
            
        return Response({
            'message': "QR Code scanné avec succès, repas marqué comme consommé/livré.",
            'data': ReservationSerializer(reservation).data
        })
