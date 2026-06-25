import uuid
from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('employe', 'Employé'),
        ('cuisinier', 'Cuisinier'),
        ('gestionnaire', 'Gestionnaire'),
        ('administrateur', 'Administrateur'),
    ]
    
    MODE_PAIEMENT_CHOICES = [
        ('solde', 'Sur solde'),
        ('facture', 'Facture mensuelle'),
    ]

    id = models.BigAutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True) # CharField pour ne pas perdre le 0 du début !
    poste = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='employe')
    
    # Nouveautés pour ton système
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mode_paiement = models.CharField(max_length=15, choices=MODE_PAIEMENT_CHOICES, default='facture')
    is_verified = models.BooleanField(default=False) # Bloqué tant que l'OTP n'est pas validé
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_authenticated(self):
        return True
        
    class Meta:
        db_table = 'users'

class Categorie(models.Model):
    libelle = models.CharField(max_length=255)
    class Meta:
        db_table = 'categories'

class Allergene(models.Model):
    libelle = models.CharField(max_length=255)
    class Meta:
        db_table = 'allergenes'

class Creneau(models.Model):
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    class Meta:
        db_table = 'creneaux'

class Plat(models.Model):
    TYPE_PLAT_CHOICES = [
        ('entree', 'Entrée'),
        ('plat', 'Plat Principal'),
        ('dessert', 'Dessert'),
        ('boisson', 'Boisson'),
    ]
    id = models.BigAutoField(primary_key=True)
    libelle = models.CharField(max_length=255)
    description = models.TextField()
    ingredients = models.TextField(blank=True, null=True) # Pour afficher la liste des ingrédients
    image = models.ImageField(upload_to='plats/') # Oublie pas : pip install Pillow
    type_plat = models.CharField(max_length=15, choices=TYPE_PLAT_CHOICES, default='plat')
    
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='plats', null=True, blank=True)
    allergenes = models.ManyToManyField(Allergene, related_name='plats', blank=True) # Plusieurs plats = plusieurs allergènes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plats'

class MenuJour(models.Model):
    # Le planning : tel plat est servi tel jour
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('epuise', 'Épuisé'),
    ]
    id = models.BigAutoField(primary_key=True)
    date_menu = models.DateField()
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE, related_name='menus_jour')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_disponible = models.IntegerField(default=50) # Pour la gestion des stocks
    cuisinier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='menus_prepares')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='disponible')
    
    class Meta:
        db_table = 'menus_jour'

class Reservation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('prepare', 'Préparé'),
        ('consomme', 'Consommé/Livré'),
        ('annule', 'Annulé'),
    ]
    TYPE_SERVICE_CHOICES = [
        ('sur_place', 'Sur place'),
        ('emporter', 'À emporter'),
        ('livraison', 'Livraison au bureau'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    employe = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    menu_jour = models.ForeignKey(MenuJour, on_delete=models.CASCADE, related_name='reservations')
    creneau = models.ForeignKey(Creneau, on_delete=models.SET_NULL, null=True, blank=True)
    
    type_service = models.CharField(max_length=15, choices=TYPE_SERVICE_CHOICES, default='sur_place')
    lieu_livraison = models.CharField(max_length=255, null=True, blank=True) # Ex: Bureau 402
    options_personnalisation = models.TextField(null=True, blank=True) # Ex: "Sans mayo, très pimenté"
    
    # Le code magique UUID infalsifiable généré tout seul (remplace l'image lourde)
    code_qr = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 
    
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    date_reservation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservations'

class Evaluation(models.Model):
    employe = models.ForeignKey(User, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    note = models.IntegerField() # 1 à 5
    commentaire = models.TextField(null=True, blank=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evaluations'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
