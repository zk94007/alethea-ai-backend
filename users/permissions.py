from rest_framework.permissions import BasePermission
from users.models import Roles


class CustomAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.roles.filter(user_roles=Roles.ADMIN).exists())
