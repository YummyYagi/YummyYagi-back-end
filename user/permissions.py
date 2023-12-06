from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        else:
            raise PermissionDenied({"status": "403", "error": "접근 권한이 없습니다."})


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed({"status": "401", "error": "로그인 후 이용해주세요."})
        return True
