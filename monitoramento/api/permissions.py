from rest_framework.permissions import BasePermission, SAFE_METHODS

class PerfilPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        print("Usuário:", user)
        print("Autenticado:", user.is_authenticated)
        print("Superusuário:", getattr(user, "is_superuser", None))
        print("Tipo:", getattr(user, "tipo", None))
        print("Método:", request.method)

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True

        return getattr(user, "tipo", None) == "ADMIN"