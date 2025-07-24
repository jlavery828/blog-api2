from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only authors of a post to edit or delete it.
    Everyone else can read.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE methods (GET, HEAD, OPTIONS) are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the author of the post can edit/delete
        return obj.author == request.user