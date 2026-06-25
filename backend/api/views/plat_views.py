from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import Plat
from ..serializers import PlatSerializer

class PlatListCreateView(APIView):
    """
    GET  /api/plats   - Liste tous les plats (public connecté)
    POST /api/plats   - Crée un nouveau plat (Cuisinier/Gestionnaire)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PlatSerializer

    @extend_schema(
        summary="Lister tous les plats",
        operation_id="list_plats",
        responses={200: PlatSerializer(many=True)}
    )
    def get(self, request):
        plats = Plat.objects.all()
        return Response({
            'message': 'Liste des plats récupérée.',
            'data': PlatSerializer(plats, many=True).data
        })

    @extend_schema(
        summary="Créer un nouveau plat",
        operation_id="create_plat",
        request=PlatSerializer,
        responses={201: PlatSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Rôle insuffisant.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = PlatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'message': 'Erreur de validation.', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            {'message': 'Plat créé avec succès.', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

class PlatDetailView(APIView):
    
    permission_classes = [IsAuthenticated]
    serializer_class = PlatSerializer

    @extend_schema(
        summary="Récupérer un plat par son ID",
        operation_id="get_plat",
        responses={200: PlatSerializer, 404: OpenApiTypes.OBJECT}
    )
    def get(self, request, pk):
        try:
            plat = Plat.objects.get(pk=pk)
        except Plat.DoesNotExist:
            return Response(
                {'message': 'Plat introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'message': 'Détail du plat.',
            'data': PlatSerializer(plat).data
        })

    @extend_schema(
        summary="Modifier un plat par son ID",
        operation_id="update_plat",
        request=PlatSerializer,
        responses={200: PlatSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def put(self, request, pk):
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Rôle insuffisant.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            plat = Plat.objects.get(pk=pk)
        except Plat.DoesNotExist:
            return Response(
                {'message': 'Plat introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        serializer = PlatSerializer(plat, data=request.data)
        if not serializer.is_valid():
            return Response(
                {'message': 'Erreur de validation.', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response({
            'message': 'Plat modified avec succès.',
            'data': serializer.data
        })

    @extend_schema(
        summary="Supprimer un plat par son ID",
        operation_id="delete_plat",
        responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, pk):
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Rôle insuffisant.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            plat = Plat.objects.get(pk=pk)
        except Plat.DoesNotExist:
            return Response(
                {'message': 'Plat introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        plat.delete()
        return Response({
            'message': 'Plat supprimé avec succès.'
        }, status=status.HTTP_200_OK)
