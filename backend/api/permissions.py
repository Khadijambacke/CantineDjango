from rest_framework.permissions import BasePermission

class IsEmploye(BasePermission):
    """
    Vérifie si l'utilisateur connecté a le rôle 'employe'.
    """
    message = "Accès interdit. Cette action est réservée aux employés."

    def has_permission(self, request, view):
        # On vérifie que l'utilisateur existe ET que son rôle est 'employe'
        return bool(request.user and request.user.role == 'employe')

class IsCuisinier(BasePermission):
    """
    Vérifie si l'utilisateur connecté a le rôle 'cuisinier'.
    """
    message = "Accès interdit. Cette action est réservée aux cuisiniers."

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'cuisinier')

class IsGestionnaire(BasePermission):
    """
    Vérifie si l'utilisateur connecté a le rôle 'gestionnaire'.
    """
    message = "Accès interdit. Cette action est réservée aux gestionnaires de la cantine."

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'gestionnaire')

class IsAdministrateur(BasePermission):
    """
    Vérifie si l'utilisateur connecté a le rôle 'administrateur' (le boss du système).
    """
    message = "Accès interdit. Rôle administrateur requis."

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'administrateur')

class IsCuisinierOrGestionnaire(BasePermission):
    """
    Vérifie si l'utilisateur connecté a le rôle 'cuisinier' ou 'gestionnaire'.
    """
    message = "Accès interdit. Cette action est réservée au personnel (cuisinier ou gestionnaire)."

    def has_permission(self, request, view):
        return bool(request.user and request.user.role in ['cuisinier', 'gestionnaire'])
