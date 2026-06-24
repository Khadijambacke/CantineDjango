import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from ..models import User
from ..serializers import UserSerializer, RegisterSerializer

# --- LA FONCTION DU PROF ---
def generate_token(user):
    payload = {
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.now(tz=timezone.utc) + timedelta(days=settings.JWT_EXPIRES_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

class RegisterView(APIView):
    """ Contrôleur pour l'inscription d'un nouvel employé """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Compte créé avec succès ! En attente de validation OTP."
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """ Contrôleur pour la connexion (Génère le Token JWT) """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({'error': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_token(user)

        return Response({
            'jwt': token,
            'user': UserSerializer(user).data
        })

class LogoutView(APIView):
    """
    POST /api/logout - Déconnexion.
    Note : Le JWT n'est pas stocké côté serveur, donc on dit juste au front-end 
    (React/Vue) de supprimer son token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({
            'message': 'Déconnexion réussie. Supprimez le token côté client.'
        })

class MeView(APIView):
    """GET /api/me - Récupère le profil de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'Profil récupéré.',
            'user': UserSerializer(request.user).data,
        })