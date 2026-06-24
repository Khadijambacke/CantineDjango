from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Plat, MenuJour, Reservation

# 1. Les Sérialiseurs (Les Traducteurs)
# Leur rôle est de prendre les données de la base de données et de les transformer en JSON 
# pour que React/Vue.js puisse les lire. Et inversement.

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # On renvoie tout SAUF le mot de passe, question de sécurité !
        exclude = ['password']

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

# Pour la suite, on créera les traducteurs pour les plats et réservations :
class PlatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plat
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
