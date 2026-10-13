from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        """Allow read access to everyone, write access only to the object's owner."""

        return True if request.method in SAFE_METHODS else obj.user == request.user
