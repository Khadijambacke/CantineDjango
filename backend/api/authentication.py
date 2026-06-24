import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class JWTAuthentication(BaseAuthentication):
    """
    Cette classe agit comme un vigile à l'entrée de ton site.
    Pour chaque requête, elle regarde si l'utilisateur a envoyé un token JWT valide.
    """
    def authenticate(self, request):
        # 1. On regarde dans l'en-tête de la requête s'il y a un mot de passe (token)
        auth_header = request.headers.get('Authorization', '')
        
        # S'il n'y a pas de token ou qu'il ne commence pas par "Bearer", on laisse tomber
        if not auth_header.startswith('Bearer '):
            return None
        
        # On extrait juste le token (on enlève le mot "Bearer ")
        token = auth_header.split(' ')[1]
        
        # 2. On essaie de décoder le token avec le JWT_SECRET
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expiré. Veuillez vous reconnecter.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token invalide.')
            
        # 3. Si le token est bon, on cherche l'utilisateur dans la base de données
        try:
            # payload['id'] contient l'ID de l'utilisateur qui était caché dans le token
            user = User.objects.get(pk=payload['id'])
        except User.DoesNotExist:
            raise AuthenticationFailed('Utilisateur introuvable.')
            
        # 4. Succès ! On dit à Django : "C'est bon, laisse-le passer, voici qui il est".
        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'
