from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..serializers import EvaluationSerializer
from ..permissions import IsEmploye

class EvaluationCreateView(APIView):
    """
    POST /api/evaluations/ - Permet à un employé de noter un plat
    """
    permission_classes = [IsAuthenticated, IsEmploye]

    @extend_schema(
        tags=['5. Évaluations'],
        summary="Noter un plat (Employé)",
        operation_id="create_evaluation",
        request=EvaluationSerializer,
        responses={201: EvaluationSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        # On passe les données au sérialiseur
        serializer = EvaluationSerializer(data=request.data)
        
        if serializer.is_valid():
            # On vérifie que la note est entre 1 et 5
            if not (1 <= serializer.validated_data['note'] <= 5):
                return Response(
                    {'error': 'La note doit être comprise entre 1 et 5.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # L'employé est automatiquement l'utilisateur connecté
            serializer.save(employe=request.user)
            
            return Response({
                'message': 'Merci pour votre évaluation !',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
