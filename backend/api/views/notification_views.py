from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Notification
from ..serializers import NotificationSerializer

class NotificationListView(APIView):
    """
    GET /api/notifications/ - Liste toutes les notifications de l'utilisateur connecté
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
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
