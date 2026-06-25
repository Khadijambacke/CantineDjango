import jwt
import datetime
import random
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from ..models import User
from ..serializers import UserSerializer, RegisterSerializer

class RegisterView(APIView):
    """ Contrôleur pour l'inscription d'un nouvel employé """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Génération de l'OTP (6 chiffres)
            otp = f"{random.randint(100000, 999999)}"
            user.otp_code = otp
            user.otp_expires_at = timezone.now() + datetime.timedelta(minutes=10)
            user.is_verified = False # Par défaut bloqué tant que l'e-mail n'est pas validé
            user.save()
            
            # Envoi de l'e-mail via Mailtrap
            try:
                subject = "Votre code de validation OTP - Cantine ISI"
                message = f"Bonjour {user.prenom},\n\nMerci de vous être inscrit sur l'application Cantine ISI. Voici votre code OTP de validation : {otp}\n\nCe code est valide pendant 10 minutes.\n\nCordialement,\nL'équipe Cantine ISI"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Si l'envoi échoue (ex: SMTP non configuré localement), on renvoie l'erreur pour aider au debug
                return Response({
                    "message": "Compte créé mais erreur lors de l'envoi de l'e-mail. Veuillez vérifier vos configurations Mailtrap.",
                    "error": str(e)
                }, status=status.HTTP_201_CREATED)
                
            return Response({
                "message": "Compte créé avec succès ! Un e-mail contenant le code OTP a été envoyé."
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
        user.otp_expires_at = timezone.now() + datetime.timedelta(minutes=10)
        user.save()

        # Envoi de l'e-mail
        try:
            subject = "Votre nouveau code de validation OTP - Cantine ISI"
            message = f"Bonjour {user.prenom},\n\nVoici votre nouveau code OTP de validation : {otp}\n\nCe code est valide pendant 10 minutes.\n\nCordialement,\nL'équipe Cantine ISI"
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

        payload = {
            'id': user.id,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

        return Response({
            'jwt': token,
            'user': UserSerializer(user).data
        })
