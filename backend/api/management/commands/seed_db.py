import random
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from faker import Faker

from api.models import (
    User, Categorie, Allergene, Creneau, Plat, MenuJour, 
    Reservation, Evaluation, Notification
)

class Command(BaseCommand):
    help = "Génère des données de test (seed) réalistes à l'aide de Faker"

    def handle(self, *args, **kwargs):
        fake = Faker('fr_FR')
        
        self.stdout.write(self.style.WARNING("Nettoyage de la base de données..."))
        
        # Supprimer les anciennes données pour éviter les doublons ou conflits
        Notification.objects.all().delete()
        Evaluation.objects.all().delete()
        Reservation.objects.all().delete()
        MenuJour.objects.all().delete()
        Plat.objects.all().delete()
        Creneau.objects.all().delete()
        Allergene.objects.all().delete()
        Categorie.objects.all().delete()
        # On garde les superutilisateurs éventuels mais on peut vider les autres
        User.objects.filter(role__in=['employe', 'cuisinier', 'gestionnaire', 'administrateur']).delete()

        self.stdout.write(self.style.SUCCESS("Base de données nettoyée."))

        # -------------------------------------------------------------
        # 1. CRÉATION DES CATÉGORIES
        # -------------------------------------------------------------
        self.stdout.write("Création des catégories...")
        categories_noms = ["Entrées", "Plats Principaux", "Desserts", "Boissons", "Accompagnements"]
        categories = []
        for nom in categories_noms:
            cat = Categorie.objects.create(libelle=nom)
            categories.append(cat)

        # -------------------------------------------------------------
        # 2. CRÉATION DES ALLERGÈNES
        # -------------------------------------------------------------
        self.stdout.write("Création des allergènes...")
        allergenes_noms = ["Gluten", "Lactose", "Arachides", "Crustacés", "Soja", "Œufs", "Poisson"]
        allergenes = []
        for nom in allergenes_noms:
            alg = Allergene.objects.create(libelle=nom)
            allergenes.append(alg)

        # -------------------------------------------------------------
        # 3. CRÉATION DES CRÉNEAUX HORAIRES
        # -------------------------------------------------------------
        self.stdout.write("Création des créneaux horaires...")
        creneaux_data = [
            (time(12, 0), time(12, 45)),
            (time(12, 45), time(13, 30)),
            (time(13, 30), time(14, 15)),
        ]
        creneaux = []
        for debut, fin in creneaux_data:
            crn = Creneau.objects.create(heure_debut=debut, heure_fin=fin)
            creneaux.append(crn)

        # -------------------------------------------------------------
        # 4. CRÉATION DES UTILISATEURS (USERS)
        # -------------------------------------------------------------
        self.stdout.write("Création des utilisateurs...")
        hashed_password = make_password("password123")
        
        # Noms et prénoms typiquement sénégalais pour plus de réalisme
        noms_senegalais = ["Diop", "Ndiaye", "Sow", "Fall", "Gueye", "Diallo", "Ba", "Sy", "Faye", "Mbacké", "Kane", "Sarr", "Cissé", "Seck", "Thiam", "Gadiaga", "Samb", "Dramé", "Toure", "Beye"]
        prenoms_senegalais = ["Khadija", "Moussa", "Fatou", "Ousmane", "Amina", "Abdou", "Mariama", "Ibrahima", "Aissatou", "Cheikh", "Seynabou", "Babacar", "Adama", "Omar", "Bator", "Amadou", "Rama", "Astou", "Moustapha", "Khadim"]

        # Set pour garantir l'unicité des e-mails générés
        used_emails = set()

        def get_unique_sn_user():
            while True:
                prenom = random.choice(prenoms_senegalais)
                nom = random.choice(noms_senegalais)
                email = f"{prenom.lower()}.{nom.lower()}@cantine.sn"
                if email not in used_emails:
                    used_emails.add(email)
                    return prenom, nom, email
        
        # Administrateurs
        admins = []
        for _ in range(2):
            prenom, nom, email = get_unique_sn_user()
            admins.append(User.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=f"+22177{random.randint(1000000, 9999999)}",
                poste="Administrateur Système",
                password=hashed_password,
                role="administrateur",
                is_verified=True
            ))

        # Gestionnaires
        gestionnaires = []
        for _ in range(2):
            prenom, nom, email = get_unique_sn_user()
            gestionnaires.append(User.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=f"+22178{random.randint(1000000, 9999999)}",
                poste="Gestionnaire Cantine",
                password=hashed_password,
                role="gestionnaire",
                is_verified=True
            ))

        # Cuisiniers
        cuisiniers = []
        for _ in range(3):
            prenom, nom, email = get_unique_sn_user()
            cuisiniers.append(User.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=f"+22176{random.randint(1000000, 9999999)}",
                poste="Chef Cuisinier",
                password=hashed_password,
                role="cuisinier",
                is_verified=True
            ))

        # Employés standard
        employes = []
        postes = ["Développeur", "Designer UI/UX", "Comptable", "Ressources Humaines", "Chef de Projet", "Analyste", "Commercial"]
        for _ in range(15):
            prenom, nom, email = get_unique_sn_user()
            employes.append(User.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=f"+22170{random.randint(1000000, 9999999)}",
                poste=random.choice(postes),
                password=hashed_password,
                role="employe",
                solde=round(random.uniform(5000, 50000), 2), # En CFA ou solde
                mode_paiement=random.choice(['solde', 'facture']),
                is_verified=True
            ))

        self.stdout.write(f"Créé : {len(admins)} admins, {len(gestionnaires)} gestionnaires, {len(cuisiniers)} cuisiniers, {len(employes)} employés.")

        # -------------------------------------------------------------
        # 5. CRÉATION DES PLATS
        # -------------------------------------------------------------
        self.stdout.write("Création des plats...")
        
        plats_data = [
            # Entrées
            ("Salade César", "Salade croquante avec blancs de poulet grillés, croûtons et sauce César.", "Poulet, salade romaine, croûtons, parmesan, sauce césar", "entree", "Entrées", ["Gluten", "Lactose"]),
            ("Soupe à l'oignon", "Soupe traditionnelle française gratinée au fromage.", "Oignons, bouillon de bœuf, pain, fromage râpé", "entree", "Entrées", ["Gluten", "Lactose"]),
            ("Pastels au poisson", "Beignets croustillants fourrés au poisson épicé.", "Farine, poisson haché, oignon, piment, ail", "entree", "Entrées", ["Gluten", "Poisson"]),
            
            # Plats Principaux
            ("Thiéboudienne (Riz au poisson)", "Le plat national sénégalais, riz rouge cuit au bouillon de légumes et poisson.", "Riz, poisson (thiof), carotte, manioc, chou, aubergine, tomate concentrée", "plat", "Plats Principaux", ["Poisson"]),
            ("Yassa au Poulet", "Poulet mariné au citron et aux oignons caramélisés, servi avec du riz blanc.", "Poulet, oignons, citron, moutarde, ail, riz blanc", "plat", "Plats Principaux", []),
            ("Mafé au Bœuf", "Viande de bœuf mijotée dans une sauce onctueuse à la pâte d'arachide, servie avec du riz.", "Bœuf, pâte d'arachide, tomate, carotte, patate douce, riz", "plat", "Plats Principaux", ["Arachides"]),
            ("Dibi de Mouton", "Côtelettes de mouton grillées au feu de bois et assaisonnées d'oignons et moutarde.", "Viande de mouton, oignons, moutarde, épices", "plat", "Plats Principaux", []),
            
            # Desserts
            ("Thiakry", "Dessert lacté sénégalais à base de semoule de mil et de yaourt sucré.", "Semoule de mil, yaourt, lait concentré, sucre, arôme vanille", "dessert", "Desserts", ["Lactose"]),
            ("Salade de fruits tropicaux", "Mélange frais de mangues, ananas, papayes et bananes.", "Mangue, ananas, papaye, banane, menthe", "dessert", "Desserts", []),
            ("Fondant au Chocolat", "Gâteau au chocolat avec cœur coulant, servi tiède.", "Chocolat noir, beurre, œufs, sucre, farine", "dessert", "Desserts", ["Gluten", "Lactose", "Œufs"]),
            
            # Boissons
            ("Jus de Bissap", "Boisson rafraîchissante à base d'infusion de fleurs d'hibiscus.", "Fleurs d'hibiscus, sucre, menthe, arôme fraise", "boisson", "Boissons", []),
            ("Jus de Bouye", "Boisson onctueuse à base de pain de singe (fruit du baobab).", "Pain de singe, lait concentré, sucre, arôme banane", "boisson", "Boissons", ["Lactose"]),
        ]

        plats = []
        for libelle, desc, ingredients, type_p, cat_nom, alg_noms in plats_data:
            cat_obj = next((c for c in categories if c.libelle == cat_nom), None)
            plat = Plat.objects.create(
                libelle=libelle,
                description=desc,
                ingredients=ingredients,
                image="plats/default_plat.jpg", # Chemin par défaut
                type_plat=type_p,
                categorie=cat_obj
            )
            
            # Ajouter les allergènes
            for alg_nom in alg_noms:
                alg_obj = next((a for a in allergenes if a.libelle == alg_nom), None)
                if alg_obj:
                    plat.allergenes.add(alg_obj)
            
            plats.append(plat)

        self.stdout.write(f"Créé : {len(plats)} plats savoureux.")

        # -------------------------------------------------------------
        # 6. CRÉATION DES MENUS DU JOUR (PLANNING)
        # -------------------------------------------------------------
        self.stdout.write("Création du planning des menus...")
        
        # On va créer des menus pour les 3 derniers jours, aujourd'hui et les 3 prochains jours
        today = date.today()
        dates_menu = [today - timedelta(days=i) for i in range(1, 4)] + [today] + [today + timedelta(days=i) for i in range(1, 4)]
        
        menus_jour = []
        for d in dates_menu:
            # Pour chaque jour, on propose 1 entrée, 2 plats principaux, 1 dessert et 2 boissons
            plats_du_jour = {
                'entree': random.sample([p for p in plats if p.type_plat == 'entree'], 1),
                'plat': random.sample([p for p in plats if p.type_plat == 'plat'], 2),
                'dessert': random.sample([p for p in plats if p.type_plat == 'dessert'], 1),
                'boisson': random.sample([p for p in plats if p.type_plat == 'boisson'], 2),
            }
            
            for type_plat, list_plats in plats_du_jour.items():
                for p in list_plats:
                    prix = random.choice([1500, 2000, 2500, 3000]) if type_plat == 'plat' else random.choice([500, 800, 1000])
                    mj = MenuJour.objects.create(
                        date_menu=d,
                        plat=p,
                        prix=prix,
                        quantite_disponible=random.randint(15, 60),
                        cuisinier=random.choice(cuisiniers),
                        statut='disponible'
                    )
                    menus_jour.append(mj)

        self.stdout.write(f"Créé : {len(menus_jour)} menus planifiés sur plusieurs jours.")

        # -------------------------------------------------------------
        # 7. CRÉATION DES RÉSERVATIONS
        # -------------------------------------------------------------
        self.stdout.write("Création des réservations...")
        
        # On va générer des réservations pour les employés
        # Uniquement pour les menus d'aujourd'hui et passés
        past_and_today_menus = [m for m in menus_jour if m.date_menu <= today]
        
        reservation_count = 0
        for _ in range(30):
            emp = random.choice(employes)
            menu = random.choice(past_and_today_menus)
            creneau = random.choice(creneaux)
            
            # Vérifier si cet employé n'a pas déjà réservé ce même menu
            if not Reservation.objects.filter(employe=emp, menu_jour=menu).exists():
                statut_res = 'consomme' if menu.date_menu < today else random.choice(['en_attente', 'prepare', 'annule'])
                
                Reservation.objects.create(
                    employe=emp,
                    menu_jour=menu,
                    creneau=creneau,
                    type_service=random.choice(['sur_place', 'emporter', 'livraison']),
                    lieu_livraison=fake.address()[:255] if random.choice([True, False]) else None,
                    options_personnalisation=random.choice(["Pas de piment", "Sauce à part", None, "Bien chaud"]),
                    statut=statut_res
                )
                reservation_count += 1

        self.stdout.write(f"Créé : {reservation_count} réservations de test.")

        # -------------------------------------------------------------
        # 8. CRÉATION DES ÉVALUATIONS
        # -------------------------------------------------------------
        self.stdout.write("Création des évaluations...")
        
        eval_count = 0
        commentaires_avis = [
            "Excellent plat ! Je recommande fortement.",
            "C'était bon, mais un peu trop épicé à mon goût.",
            "Service rapide et nourriture de qualité.",
            "Le riz manquait un peu de cuisson.",
            "Parfait comme d'habitude !",
            "Un peu déçu par la quantité du plat, mais le goût était là.",
            "Une merveille culinaire ! Le chef se surpasse."
        ]
        
        # Les employés évaluent les plats qu'ils ont potentiellement consommés
        for _ in range(25):
            emp = random.choice(employes)
            p = random.choice(plats)
            
            if not Evaluation.objects.filter(employe=emp, plat=p).exists():
                Evaluation.objects.create(
                    employe=emp,
                    plat=p,
                    note=random.randint(3, 5), # Plutôt des bonnes notes
                    commentaire=random.choice(commentaires_avis) if random.choice([True, False]) else None
                )
                eval_count += 1

        self.stdout.write(f"Créé : {eval_count} avis/évaluations de plats.")

        # -------------------------------------------------------------
        # 9. CRÉATION DES NOTIFICATIONS
        # -------------------------------------------------------------
        self.stdout.write("Création des notifications...")
        
        notif_titles = [
            "Repas disponible !",
            "Validation de votre réservation",
            "Nouveau menu en ligne",
            "Mise à jour du solde",
            "Rappel de réservation"
        ]
        
        notif_count = 0
        for _ in range(20):
            usr = random.choice(employes + cuisiniers)
            Notification.objects.create(
                user=usr,
                titre=random.choice(notif_titles),
                message=fake.sentence(nb_words=10),
                is_read=random.choice([True, False])
            )
            notif_count += 1

        self.stdout.write(f"Créé : {notif_count} notifications.")
        self.stdout.write(self.style.SUCCESS("Félicitations ! Les données de test ont été générées avec succès !"))
