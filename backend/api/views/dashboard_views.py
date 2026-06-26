import csv
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..permissions import IsGestionnaire
from ..models import Reservation, User
from ..serializers import UserSerializer

class DashboardGestionnaireView(APIView):
    """
    GET /api/dashboard/gestionnaire/ - Récupère les KPIs et la liste des employés
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    def get(self, request):
        debut_mois = timezone.now().date().replace(day=1)

        # KPIs
        # 1. Total revenus du mois (réservations non annulées)
        total_revenus = Reservation.objects.filter(
            menu_jour__date_menu__gte=debut_mois
        ).exclude(statut='annule').aggregate(total=Sum('menu_jour__prix'))['total'] or 0

        # 2. Total repas servis (statut consomme)
        total_repas = Reservation.objects.filter(
            menu_jour__date_menu__gte=debut_mois,
            statut='consomme'
        ).count()

        # 3. Taux de réservation : Pourcentage des employés ayant fait au moins une réservation ce mois-ci
        total_employes = User.objects.filter(role='employe').count()
        employes_actifs = Reservation.objects.filter(
            menu_jour__date_menu__gte=debut_mois
        ).values('employe').distinct().count()
        
        taux_reservation = int((employes_actifs / total_employes * 100)) if total_employes > 0 else 0

        # Liste des employés avec le serializer qui calcule déjà 'depenses_mensuelles'
        employes = User.objects.filter(role='employe').order_by('nom')
        employes_data = UserSerializer(employes, many=True).data

        # Filtrer pour compter ceux en attente de facturation
        factures_en_attente = sum(1 for e in employes_data if e['facture_mensuelle_salaire'] > 0)

        return Response({
            'message': 'Données du dashboard récupérées.',
            'data': {
                'kpis': {
                    'revenu_mensuel': float(total_revenus),
                    'repas_servis': total_repas,
                    'taux_reservation': taux_reservation,
                    'factures_en_attente': factures_en_attente
                },
                'employes': employes_data
            }
        })

class ExportFacturationRHView(APIView):
    """
    GET /api/dashboard/gestionnaire/export/ - Génère un CSV des retenues sur salaire
    """
    permission_classes = [IsAuthenticated, IsGestionnaire]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="facturation_cantine.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Nom', 'Prenom', 'Email', 'Poste', 'Mode de Paiement', 'Montant a prelever (CFA)'])

        employes = User.objects.filter(role='employe').order_by('nom')
        employes_data = UserSerializer(employes, many=True).data

        for e in employes_data:
            # On n'exporte que ceux qui ont choisi la facturation et qui ont un montant > 0
            # Ou tout le monde si on veut, mais c'est mieux de cibler.
            if e['mode_paiement'] == 'facture' and e['facture_mensuelle_salaire'] > 0:
                writer.writerow([
                    e['nom'],
                    e['prenom'],
                    e['email'],
                    e['poste'],
                    'Facture mensuelle',
                    e['facture_mensuelle_salaire']
                ])

        return response


class RechargerSoldeView(APIView):
    """
    POST /api/solde/recharger/ - L'employé recharge son solde cantine
    Body: { montant: 5000 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        montant_str = request.data.get('montant')
        try:
            montant = float(montant_str)
            if montant <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return Response({'message': 'Montant invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        MAX_RECHARGE = 500000  # 500 000 CFA max par opération
        if montant > MAX_RECHARGE:
            return Response({'message': f'Montant maximum autorisé : {MAX_RECHARGE} CFA.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.solde += montant
        user.save()

        return Response({
            'message': f'{montant:.0f} CFA crédités sur votre solde.',
            'nouveau_solde': float(user.solde)
        })
