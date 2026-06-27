from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Notification, User
from ..serializers import NotificationSerializer
from ..permissions import IsGestionnaire

class NotificationListView(APIView):
    """
    GET /api/notifications/ - Liste toutes les notifications de l'utilisateur connecté
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        tags=['6. Notifications'],
        summary="Liste des notifications de l'utilisateur",
        operation_id="list_notifications",
        responses={200: NotificationSerializer(many=True)}
    )
    def get(self, request):
        # On ne récupère que les notifications de l'utilisateur connecté
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'message': 'Liste des notifications récupérée.',
            'data': serializer.data
        })

class NotificationMarkReadView(APIView):
    """
    POST /api/notifications/<id>/read/ - Marquer une notification comme lue
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['6. Notifications'],
        summary="Marquer une notification comme lue",
        operation_id="mark_notification_read",
        responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def post(self, request, pk):
        try:
            # On s'assure que la notification appartient bien à l'utilisateur connecté
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({
                'message': 'Notification introuvable.'
            }, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response({
            'message': 'Notification marquée comme lue.',
            'data': NotificationSerializer(notification).data
        })

class BroadcastNotificationView(APIView):
    """
    POST /api/notifications/broadcast/ - Le gestionnaire envoie une notif à un groupe de users
    Body: { titre, message, cible: 'tous' | 'employes' | 'cuisiniers' }
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    @extend_schema(
        tags=['6. Notifications'],
        summary="Diffuser une notification globale (Gestionnaire)",
        operation_id="broadcast_notification",
        request=OpenApiTypes.OBJECT,
        responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        titre = request.data.get('titre', '').strip()
        message = request.data.get('message', '').strip()
        cible = request.data.get('cible', 'tous')

        if not titre or not message:
            return Response({'message': 'Titre et message sont requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if cible == 'employes':
            destinataires = User.objects.filter(role='employe')
        elif cible == 'cuisiniers':
            destinataires = User.objects.filter(role='cuisinier')
        else:
            destinataires = User.objects.exclude(role__in=['gestionnaire', 'administrateur'])

        notifs = [Notification(user=u, titre=titre, message=message) for u in destinataires]
        Notification.objects.bulk_create(notifs)

        return Response({
            'message': f'{len(notifs)} notification(s) envoyée(s) avec succès.'
        }, status=status.HTTP_201_CREATED)


class MessageCuisinierView(APIView):
    """
    POST /api/notifications/message-cuisinier/ - Un employé envoie un message/instruction à la cuisine
    Body: { message }
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['6. Notifications'],
        summary="Envoyer un message à l'équipe de cuisine",
        operation_id="message_cuisinier",
        request=OpenApiTypes.OBJECT,
        responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        message = request.data.get('message', '').strip()

        if not message:
            return Response({'message': 'Le message ne peut pas être vide.'}, status=status.HTTP_400_BAD_REQUEST)

        employe = request.user
        titre = f"Message de {employe.prenom} {employe.nom}"
        msg_complet = f"[Instruction cuisine]\n{message}"

        # Envoyer à tous les cuisiniers
        cuisiniers = User.objects.filter(role='cuisinier')
        if not cuisiniers.exists():
            return Response({'message': 'Aucun cuisinier disponible pour recevoir le message.'}, status=status.HTTP_404_NOT_FOUND)

        notifs = [Notification(user=c, titre=titre, message=msg_complet) for c in cuisiniers]
        Notification.objects.bulk_create(notifs)

        return Response({
            'message': f'Votre message a été transmis à l\'équipe de cuisine.'
        }, status=status.HTTP_201_CREATED)
