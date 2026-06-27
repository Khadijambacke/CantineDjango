from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter

from ..models import MenuJour, Reservation
from ..serializers import MenuJourSerializer

class MenuListCreateView(APIView):
    """
    GET  /api/menus   - Liste les menus du jour et à venir (public connecté)
    POST /api/menus   - Planifie un nouveau repas (Cuisinier/Gestionnaire)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MenuJourSerializer

    @extend_schema(
        tags=['3. Menus du Jour'],
        summary="Lister les menus planifiés",
        operation_id="list_menus",
        parameters=[
            OpenApiParameter(
                name="all",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Si true et si l'utilisateur est staff, retourne l'historique complet."
            )
        ],
        responses={200: MenuJourSerializer(many=True)}
    )
    def get(self, request):
        show_all = request.query_params.get('all', 'false').lower() == 'true'
        is_staff = request.user.role in ['cuisinier', 'gestionnaire', 'administrateur']

        if show_all and is_staff:
            menus = MenuJour.objects.all().order_by('-date_menu')
        else:
            # Par défaut, on ne montre que les menus d'aujourd'hui et futurs
            menus = MenuJour.objects.filter(date_menu__gte=date.today()).order_by('date_menu')

        serializer = MenuJourSerializer(menus, many=True)
        return Response({
            'message': 'Planning des menus récupéré avec succès.',
            'data': serializer.data
        })

    @extend_schema(
        tags=['3. Menus du Jour'],
        summary="Planifier un plat à une date (Menu)",
        operation_id="create_menu",
        request=MenuJourSerializer,
        responses={201: MenuJourSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        # Restriction d'accès aux rôles autorisés
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Seul le personnel de cuisine ou de gestion peut planifier des menus.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MenuJourSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'message': 'Erreur de validation.', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        return Response(
            {'message': 'Repas planifié avec succès.', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

class MenuStatsView(APIView):
    """
    GET /api/menus/stats - Renvoie le nombre de portions réservées à préparer pour une date donnée (Cuisinier/Gestionnaire)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['3. Menus du Jour'],
        summary="Statistiques des plats réservés à préparer",
        operation_id="menu_stats",
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Date recherchée au format YYYY-MM-DD. Par défaut: demain."
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        # Restriction d'accès aux rôles autorisés
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Réservé au personnel autorisé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {'message': 'Format de date invalide. Utilisez le format YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Par défaut, on regarde pour demain
            target_date = date.today() + timedelta(days=1)

        # En Django, on peut faire le décompte des réservations directement avec un Count
        from django.db.models import Count
        stats_data = Reservation.objects.filter(
            menu_jour__date_menu=target_date
        ).exclude(
            statut='annule'
        ).values('menu_jour__id').annotate(total=Count('id'))

        # Récupérer tous les menus programmés à cette date pour lister même ceux à 0 réservation
        menus_du_jour = MenuJour.objects.filter(date_menu=target_date)
        
        result = []
        for menu in menus_du_jour:
            # Trouver s'il y a des réservations enregistrées pour ce menu
            stat_item = next((s for s in stats_data if s['menu_jour__id'] == menu.id), None)
            total_portiones = stat_item['total'] if stat_item else 0
            
            result.append({
                'menu_id': menu.id,
                'plat_id': menu.plat.id,
                'plat_libelle': menu.plat.libelle,
                'type_plat': menu.plat.type_plat,
                'prix': menu.prix,
                'total_reservations': total_portiones
            })

        return Response({
            'date': target_date.isoformat(),
            'message': f"Statistiques de préparation pour le {target_date.strftime('%d/%m/%Y')}.",
            'data': result
        })

class MenuDetailView(APIView):
    """
    GET /api/menus/<id> - Détails d'un menu
    PATCH /api/menus/<id> - Met à jour le statut (ex: passer à 'epuise')
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return MenuJour.objects.get(pk=pk)
        except MenuJour.DoesNotExist:
            return None

    @extend_schema(
        tags=['3. Menus du Jour'],
        summary="Mettre à jour un menu (Cuisinier/Gestionnaire)",
        operation_id="update_menu",
        request=MenuJourSerializer,
        responses={200: MenuJourSerializer, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def patch(self, request, pk):
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit.'},
                status=status.HTTP_403_FORBIDDEN
            )

        menu = self.get_object(pk)
        if not menu:
            return Response({'message': 'Menu introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MenuJourSerializer(menu, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Menu mis à jour avec succès.',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['3. Menus du Jour'],
        summary="Supprimer un menu du planning (Cuisinier/Gestionnaire)",
        operation_id="delete_menu",
        responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def delete(self, request, pk):
        if request.user.role not in ['cuisinier', 'gestionnaire', 'administrateur']:
            return Response(
                {'message': 'Accès interdit. Seul le personnel autorisé peut supprimer des menus.'},
                status=status.HTTP_403_FORBIDDEN
            )

        menu = self.get_object(pk)
        if not menu:
            return Response({'message': 'Menu introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        menu.delete()
        return Response({
            'message': 'Le repas a été retiré du planning avec succès.'
        }, status=status.HTTP_200_OK)

