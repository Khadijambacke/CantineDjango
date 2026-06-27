from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes

from ..models import User, Reservation
from ..serializers import UserSerializer, ReservationSerializer
from ..permissions import IsGestionnaire


class GestionnaireEmployesView(APIView):
    """
    GET  /api/gestionnaire/employes/ - Liste tous les utilisateurs (sauf gestionnaire/admin)
    POST /api/gestionnaire/employes/ - Crée un compte employé ou cuisinier
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    @extend_schema(
        tags=['9. Espace Gestionnaire'],
        summary="Liste de tous les employés et cuisiniers",
        operation_id="gestionnaire_list_employes",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        role = request.query_params.get('role', None)
        qs = User.objects.exclude(role__in=['gestionnaire', 'administrateur']).order_by('nom')
        if role:
            qs = qs.filter(role=role)
        return Response({
            'message': 'Liste des utilisateurs.',
            'data': UserSerializer(qs, many=True).data
        })

    @extend_schema(
        tags=['9. Espace Gestionnaire'],
        summary="Créer un compte employé ou cuisinier",
        operation_id="gestionnaire_create_employe",
        request=UserSerializer,
        responses={201: UserSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        data = request.data.copy()
        # Vérifier champs obligatoires
        required = ['nom', 'prenom', 'email', 'telephone', 'poste', 'password', 'role']
        for field in required:
            if not data.get(field):
                return Response({'message': f'Le champ {field} est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        if data['role'] not in ['employe', 'cuisinier']:
            return Response({'message': 'Rôle invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=data['email']).exists():
            return Response({'message': 'Email déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            nom=data['nom'],
            prenom=data['prenom'],
            email=data['email'],
            telephone=data['telephone'],
            poste=data['poste'],
            password=make_password(data['password']),
            role=data['role'],
            is_verified=True  # Compte créé par admin = actif directement
        )
        return Response({
            'message': f'Compte {data["role"]} créé avec succès.',
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class GestionnaireEmployeDetailView(APIView):
    """
    PATCH  /api/gestionnaire/employes/<id>/ - Activer / Désactiver / Modifier un compte
    DELETE /api/gestionnaire/employes/<id>/ - Supprimer un compte
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    def get_object(self, pk):
        try:
            return User.objects.exclude(role__in=['gestionnaire', 'administrateur']).get(pk=pk)
        except User.DoesNotExist:
            return None

    @extend_schema(
        tags=['9. Espace Gestionnaire'],
        summary="Activer, désactiver ou modifier un compte employé",
        operation_id="gestionnaire_update_employe",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'message': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        # On autorise seulement la modification de is_verified (activer/désactiver), poste, mode_paiement, solde
        allowed = ['is_verified', 'poste', 'mode_paiement', 'solde']
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        return Response({
            'message': 'Compte mis à jour.',
            'data': UserSerializer(user).data
        })

    @extend_schema(
        tags=['9. Espace Gestionnaire'],
        summary="Supprimer un compte employé",
        operation_id="gestionnaire_delete_employe",
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'message': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        nom = f"{user.prenom} {user.nom}"
        user.delete()
        return Response({'message': f'Compte de {nom} supprimé.'})


class GestionnaireCommandesView(APIView):
    """
    GET /api/gestionnaire/commandes/ - Toutes les réservations (filtrables par date)
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    @extend_schema(
        tags=['9. Espace Gestionnaire'],
        summary="Toutes les réservations de la cantine (filtrables par date)",
        operation_id="gestionnaire_list_commandes",
        responses={200: ReservationSerializer(many=True)}
    )
    def get(self, request):
        date_str = request.query_params.get('date', None)
        if date_str:
            try:
                from datetime import date
                target = date.fromisoformat(date_str)
            except ValueError:
                return Response({'message': 'Format date invalide (YYYY-MM-DD).'}, status=400)
        else:
            target = timezone.now().date()

        reservations = (
            Reservation.objects
            .select_related('employe', 'menu_jour', 'menu_jour__plat')
            .filter(menu_jour__date_menu=target)
            .order_by('-date_reservation')
        )

        return Response({
            'message': f'Commandes du {target.strftime("%d/%m/%Y")}.',
            'date': target.isoformat(),
            'data': ReservationSerializer(reservations, many=True).data
        })
