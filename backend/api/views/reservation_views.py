from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Reservation, MenuJour, Notification
from ..serializers import ReservationSerializer
from ..permissions import IsEmploye

class ReservationListCreateView(APIView):
    """
    GET  /api/reservations - Liste des réservations de l'employé connecté
    POST /api/reservations - Créer une réservation pour l'employé connecté
    """
    permission_classes = [IsAuthenticated, IsEmploye]
    serializer_class = ReservationSerializer

    @extend_schema(
        summary="Lister les réservations de l'employé",
        operation_id="list_reservations",
        responses={200: ReservationSerializer(many=True)}
    )
    def get(self, request):
        # Seulement les réservations de l'employé connecté
        reservations = (
            Reservation.objects
            .filter(employe=request.user)
            .select_related('menu_jour', 'employe', 'creneau')
            .order_by('-date_reservation')
        )
        return Response({
            'message': 'Mes réservations.',
            'data': ReservationSerializer(reservations, many=True).data
        })

    @extend_schema(
        summary="Réserver un repas (menu planifié)",
        operation_id="create_reservation",
        request=ReservationSerializer,
        responses={201: ReservationSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        # 1. Valider les données entrantes avec le sérialiseur
        serializer = ReservationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'message': 'Erreur de validation.', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        data = serializer.validated_data
        menu_jour = data['menu_jour']

        # 2. Règles métier : Pas de réservation dans le passé
        if menu_jour.date_menu < date.today():
            return Response(
                {'message': 'Impossible de réserver pour un jour déjà passé.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Éviter les doublons
        already_reserved = Reservation.objects.filter(
            employe=request.user,
            menu_jour=menu_jour
        ).exclude(statut='annule').exists()

        if already_reserved:
            return Response(
                {'message': 'Vous avez déjà une réservation active pour ce repas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Vérification du solde de l'employé
        employe = request.user
        prix_repas = menu_jour.prix
        mode_paiement = employe.mode_paiement

        if mode_paiement == 'solde' and employe.solde < prix_repas:
            return Response(
                {'message': f"Solde insuffisant. Le repas coûte {prix_repas} CFA et votre solde actuel est de {employe.solde} CFA."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.db import transaction

        # 5. Créer la réservation et mettre à jour le solde atomiquement
        with transaction.atomic():
            if mode_paiement == 'solde':
                employe.solde -= prix_repas
                employe.save()

            reservation = Reservation.objects.create(
                employe=employe,
                menu_jour=menu_jour,
                creneau=data.get('creneau'),
                type_service=data.get('type_service', 'sur_place'),
                lieu_livraison=data.get('lieu_livraison', ''),
                options_personnalisation=data.get('options_personnalisation', ''),
                statut='en_attente'
            )

            # 6. Créer une notification de confirmation
            msg_solde = f" Nouveau solde : {employe.solde} CFA." if mode_paiement == 'solde' else ""
            Notification.objects.create(
                user=employe,
                titre="Réservation confirmée !",
                message=f"Votre réservation pour le plat '{menu_jour.plat.libelle}' du {menu_jour.date_menu} a été enregistrée avec succès.{msg_solde}"
            )

        # 7. Recharger avec les relations pour la réponse complète
        reservation_full = (
            Reservation.objects
            .select_related('menu_jour', 'employe', 'creneau')
            .get(pk=reservation.pk)
        )

        return Response(
            {
                'message': 'Réservation créée avec succès.',
                'data': ReservationSerializer(reservation_full).data,
            },
            status=status.HTTP_201_CREATED,
        )

class ReservationDetailView(APIView):
    """
    GET    /api/reservations/<id> - Voir les détails d'une de ses réservations
    DELETE /api/reservations/<id> - Annuler une réservation (statut 'annule')
    """
    permission_classes = [IsAuthenticated, IsEmploye]
    serializer_class = ReservationSerializer

    @extend_schema(
        summary="Voir les détails d'une de ses réservations",
        operation_id="get_reservation",
        responses={200: ReservationSerializer, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def get(self, request, pk):
        try:
          
            reservation = (
                Reservation.objects
                .select_related('menu_jour', 'employe', 'creneau')
                .get(pk=pk, employe=request.user)
            )
        except Reservation.DoesNotExist:
            return Response(
                {'message': 'Réservation introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReservationSerializer(reservation)
        return Response({
            'message': 'Détail de la réservation récupéré.',
            'data': serializer.data
        })

    @extend_schema(
        summary="Annuler une de ses réservations",
        operation_id="cancel_reservation",
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, pk):
        try:
            # Un employé ne peut annuler QUE ses propres réservations
            reservation = Reservation.objects.get(pk=pk, employe=request.user)
        except Reservation.DoesNotExist:
            return Response(
                {'message': 'Réservation introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Règles métier d'annulation
        if reservation.statut == 'annule':
            return Response(
                {'message': 'Cette réservation est déjà annulée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if reservation.statut in ['consomme', 'prepare']:
            return Response(
                {'message': "Impossible d'annuler une réservation déjà préparée ou consommée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.db import transaction
        employe = request.user
        menu_jour = reservation.menu_jour
        prix_repas = menu_jour.prix
        mode_paiement = employe.mode_paiement

        with transaction.atomic():
            reservation.statut = 'annule'
            reservation.save()

            if mode_paiement == 'solde':
                employe.solde += prix_repas
                employe.save()

            # Créer une notification d'annulation
            msg_remboursement = f" Votre solde de {prix_repas} CFA a été remboursé. Nouveau solde : {employe.solde} CFA." if mode_paiement == 'solde' else ""
            Notification.objects.create(
                user=employe,
                titre="Réservation annulée",
                message=f"Votre réservation pour le plat '{menu_jour.plat.libelle}' du {menu_jour.date_menu} a été annulée.{msg_remboursement}"
            )

        return Response({
            'message': 'Réservation annulée avec succès.',
            'data': ReservationSerializer(reservation).data
        })

import qrcode
from io import BytesIO
from django.http import HttpResponse

class ReservationQRCodeView(APIView):
    """
    GET /api/reservations/<id>/code-qr/ - Générer le code QR de la réservation
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Générer l'image du QR Code pour une réservation",
        operation_id="generate_reservation_qr",
        responses={200: OpenApiTypes.BINARY, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def get(self, request, pk):
        try:
            # Un employé ne peut voir QUE ses propres réservations, mais on laisse le cuisinier voir aussi si besoin
            # Pour l'instant on sécurise l'accès à l'employé propriétaire (et admin potentiellement)
            if request.user.role == 'employe':
                reservation = Reservation.objects.get(pk=pk, employe=request.user)
            else:
                reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return Response(
                {'message': 'Réservation introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Générer le QR Code contenant l'UUID unique de la réservation
        qr_data = str(reservation.code_qr)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder dans un buffer mémoire
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Renvoyer l'image directement en HTTP
        return HttpResponse(buffer, content_type="image/png")
