from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed({"status": "401", "error": "로그인 후 이용해주세요."})
        return True
