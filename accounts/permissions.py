from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_owner


class IsOwnerOrProjectManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_owner or request.user.is_project_manager or request.user.role == 'developer')
        )


class CanViewCompanyFinance(BasePermission):
    """Only Owner can see company-wide financial analytics."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)
