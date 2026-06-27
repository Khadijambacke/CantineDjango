import jwt
import random
from datetime import datetime, timedelta, timezone
import datetime as dt_module
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import User
from ..serializers import UserSerializer, RegisterSerializer, LoginSerializer

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
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Inscription d'un nouvel employé",
        request=RegisterSerializer,
        responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Génération de l'OTP (6 chiffres)
            otp = f"{random.randint(100000, 999999)}"
            user.otp_code = otp
            user.otp_expires_at = timezone.now() + dt_module.timedelta(minutes=10)
            
            # L'OTP EST MAINTENANT ACTIF
            # L'utilisateur doit valider son compte avec le code reçu par e-mail ou affiché dans la console
            user.is_verified = False
            user.save()
            
            # On affiche le code OTP dans la console Django pour les tests
            print(f"\n{'='*50}")
            print(f"  OTP pour {user.email} : {otp}")
            print(f"{'='*50}\n")
            
            # Tentative d'envoi de l'e-mail (non bloquant)
            try:
                subject = "Votre code de validation OTP - Cantine Entreprise"
                message = f"Bonjour {user.prenom},\n\nMerci de vous être inscrit sur l'application Cantine Entreprise. Voici votre code OTP de validation : {otp}\n\nCe code est valide pendant 10 minutes.\n\nCordialement,\nL'équipe Cantine Entreprise"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,  # Ne pas planter si le mail échoue
                )
            except Exception as e:
                print(f"[SMTP ERROR] {e}")
                
            return Response({
                "message": "Compte créé avec succès ! Vous pouvez vous connecter."
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    """ Contrôleur pour la vérification du code OTP """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not email or not otp_code:
            return Response({'error': 'L\'adresse e-mail et le code OTP sont obligatoires.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'message': 'Ce compte est déjà validé.'}, status=status.HTTP_200_OK)

        if user.otp_code != otp_code:
            return Response({'error': 'Code OTP incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.otp_expires_at and timezone.now() > user.otp_expires_at:
            return Response({'error': 'Le code OTP a expiré. Veuillez en demander un nouveau.'}, status=status.HTTP_400_BAD_REQUEST)

        # Le code est correct et valide
        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        user.save()

        return Response({'message': 'Compte vérifié avec succès ! Vous pouvez maintenant vous connecter.'}, status=status.HTTP_200_OK)

class ResendOTPView(APIView):
    """ Contrôleur pour renvoyer le code OTP """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'L\'adresse e-mail est obligatoire.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'message': 'Ce compte est déjà validé.'}, status=status.HTTP_200_OK)

        # Générer un nouvel OTP
        otp = f"{random.randint(100000, 999999)}"
        user.otp_code = otp
        user.otp_expires_at = timezone.now() + dt_module.timedelta(minutes=10)
        user.save()

        # Envoi de l'e-mail
        try:
            subject = "Votre nouveau code de validation OTP - Cantine Entreprise"
            message = f"Bonjour {user.prenom},\n\nVoici votre nouveau code OTP de validation : {otp}\n\nCe code est valide pendant 10 minutes.\n\nCordialement,\nL'équipe Cantine Entreprise"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                "message": "Erreur lors de l'envoi de l'e-mail. Veuillez vérifier vos configurations.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Un nouveau code OTP a été envoyé à votre adresse e-mail.'}, status=status.HTTP_200_OK)

class LoginView(APIView):
    """ Contrôleur pour la connexion (Génère le Token JWT) """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Connexion de l'utilisateur",
        request=LoginSerializer,
        responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({'error': 'Email ou mot de passe incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Vérification du statut activé/OTP
        if not user.is_verified:
            return Response({
                'error': 'Votre compte n\'est pas encore validé. Veuillez valider votre code OTP envoyé par e-mail.',
                'not_verified': True
            }, status=status.HTTP_403_FORBIDDEN)

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
    
    @extend_schema(
        summary="Déconnexion de l'utilisateur",
        request=None,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        return Response({
            'message': 'Déconnexion réussie. Supprimez le token côté client.'
        })

class MeView(APIView):
    """GET /api/me - Récupère le profil de l'utilisateur connecté."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    @extend_schema(
        summary="Récupérer le profil connecté",
        responses={200: UserSerializer}
    )
    def get(self, request):
        return Response({
            'message': 'Profil récupéré.',
            'user': UserSerializer(request.user).data,
        })