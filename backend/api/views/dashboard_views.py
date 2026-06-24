from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..permissions import IsGestionnaire

class DashboardGestionnaireView(APIView):
    
    permission_classes = [IsAuthenticated, IsGestionnaire]

    def get(self, request):
        return Response({
            "message": f"Bienvenue boss {request.user.prenom} ! Voici vos statistiques financières."
        })
