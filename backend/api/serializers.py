from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Plat, MenuJour, Reservation, Notification

# 1. Les Sérialiseurs (Les Traducteurs)
# Leur rôle est de prendre les données de la base de données et de les transformer en JSON 
# pour que React/Vue.js puisse les lire. Et inversement.

class UserSerializer(serializers.ModelSerializer):
    depenses_mensuelles = serializers.SerializerMethodField()
    facture_mensuelle_salaire = serializers.SerializerMethodField()

    class Meta:
        model = User
        # On renvoie tout SAUF le mot de passe, question de sécurité !
        exclude = ['password']

    def get_depenses_mensuelles(self, obj):
        from django.db.models import Sum
        from django.utils import timezone
        
        # Début du mois en cours
        debut_mois = timezone.now().date().replace(day=1)
        
        # Somme des prix des menus réservés pour ce mois-ci et non annulés
        total = obj.reservations.filter(
            menu_jour__date_menu__gte=debut_mois
        ).exclude(statut='annule').aggregate(total_prix=Sum('menu_jour__prix'))['total_prix']
        
        return float(total) if total is not None else 0.00

    def get_facture_mensuelle_salaire(self, obj):
        if obj.mode_paiement != 'facture':
            return 0.00
        return self.get_depenses_mensuelles(obj)

class RegisterSerializer(serializers.ModelSerializer):
    #modelseriali... lis mes modes et s'il capture des ereeurs
    class Meta:
        model = User
        fields = ['nom', 'prenom', 'email', 'telephone', 'poste', 'password']
        
    # Quand on crée un utilisateur, on doit cacher son mot de passe
    def create(self, validated_data):
        # On chiffre (hash) le mot de passe avant de le sauvegarder
        validated_data['password'] = make_password(validated_data['password'])
        
        # On crée l'utilisateur en base de données
        user = User.objects.create(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# Pour la suite, on créera les traducteurs pour les plats et réservations :
class PlatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plat
        fields = '__all__'

class MenuJourSerializer(serializers.ModelSerializer):
    plat_detail = PlatSerializer(source='plat', read_only=True)
    cuisinier_detail = UserSerializer(source='cuisinier', read_only=True)

    class Meta:
        model = MenuJour
        fields = [
            'id', 'date_menu', 'plat', 'plat_detail', 'prix', 
            'quantite_disponible', 'cuisinier', 'cuisinier_detail', 'statut'
        ]

class ReservationSerializer(serializers.ModelSerializer):
    menu_jour_detail = MenuJourSerializer(source='menu_jour', read_only=True)
    employe_detail = UserSerializer(source='employe', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'employe', 'employe_detail', 'menu_jour', 'menu_jour_detail', 
            'creneau', 'type_service', 'lieu_livraison', 'options_personnalisation', 
            'code_qr', 'statut', 'date_reservation'
        ]
        read_only_fields = ['employe', 'code_qr', 'statut']
class StatutUpdateSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=Reservation.STATUT_CHOICES)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
