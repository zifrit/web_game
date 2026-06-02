from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission


class IsSuperuserOrOwner(BasePermission):
    """Allows authenticated users to access their own objects, with superuser bypass."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self._is_owned_by_user(obj, user)

    def _is_owned_by_user(self, obj, user) -> bool:
        User = get_user_model()
        if isinstance(obj, User):
            return obj.pk == user.pk

        if self._matches_user_id(getattr(obj, "user_id", None), user):
            return True
        if self._matches_user_id(getattr(obj, "owner_id", None), user):
            return True
        if self._matches_user_id(getattr(obj, "owner_user_id", None), user):
            return True

        if self._related_user_matches(obj, "user", user):
            return True
        if self._related_user_matches(obj, "owner", user):
            return True
        if self._related_user_matches(obj, "owner_user", user):
            return True
        if self._related_character_matches(obj, user):
            return True

        return False

    @staticmethod
    def _matches_user_id(owner_id, user) -> bool:
        return owner_id is not None and owner_id == user.pk

    def _related_user_matches(self, obj, attr: str, user) -> bool:
        try:
            related_user = getattr(obj, attr, None)
        except ObjectDoesNotExist:
            return False
        return bool(related_user and self._matches_user_id(related_user.pk, user))

    def _related_character_matches(self, obj, user) -> bool:
        try:
            character = getattr(obj, "character", None)
        except ObjectDoesNotExist:
            return False
        return bool(character and self._matches_user_id(getattr(character, "user_id", None), user))
